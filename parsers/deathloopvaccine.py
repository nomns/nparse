import datetime
import re
import os
import signal


from datetime import datetime
from helpers import Parser, config, get_eqgame_pid_list, starprint


#
# simple utility to prevent Everquest Death Loop
#
# The utility functions by parsing the current (most recent) Everquest log file, and if it detects
# Death Loop symptoms, it will respond by initiating a system process kill of all "eqgame.exe"
# processes (there should usually only be one).
#
# We will define a death loop as any time a player experiences X deaths in Y seconds, and no player
# activity during that time.  The values for X and Y are configurable, via the DeathLoopVaccine.ini file.
#
# For testing purposes, there is a back door feature, controlled by sending a tell to the following
# non-existent player:
#
#   death_loop:     Simulates a player death.
#
#                   Note however that this also sets a flag that disarms the conceptual
#                   "process-killer gun", which will allow every bit of the code to
#                   execute and be tested, but will stop short of actually killing any
#                   process
#
#                   The "process-killer gun" will then be armed again after the simulated
#                   player deaths trigger the simulated process kill, or after any simulated
#                   player death events "scroll off" the death loop monitoring window.
#
class DeathLoopVaccine(Parser):

    """Tracks for DL symptoms"""

    def __init__(self):

        super().__init__()
        self.name = 'deathloopvaccine'

        # parameters that define a deathloop condition, i.e. D deaths in T seconds,
        # with no player activity in the interim
        # todo - make the deathloop.deaths and deathloop.seconds values configarable via the UI?

        # list of death messages
        # this will function as a scrolling queue, with the oldest message at position 0,
        # newest appended to the other end.  Older messages scroll off the list when more
        # than deathloop_seconds have elapsed.  The list is also flushed any time
        # player activity is detected (i.e. player is not AFK).
        #
        # if/when the length of this list meets or exceeds deathloop.deaths, then
        # the deathloop response is triggered
        self._death_list = list()

        # flag indicating whether the "process killer" gun is armed
        self._kill_armed = True

    def reset(self) -> None:
        """
        Utility function to clear the death_list and reset the armed flag

        Returns:
            None:
        """
        self._death_list.clear()
        self._kill_armed = True

    # main parsing logic here
    def parse(self, timestamp: datetime, text: str) -> None:
        """
        Parse a single text from the logfile

        Args:
            timestamp: A datetime.datetime object, created from the timestamp text of the raw logfile text
            text: The text following the everquest timestamp

        Returns:
            None:
        """

        self.check_for_death(timestamp, text)
        self.check_not_afk(timestamp, text)
        self.deathloop_response()

    def check_for_death(self, timestamp: datetime, text: str) -> None:
        """
        check for indications the player just died, and if we find it,
        save the message for later processing

        Args:
            timestamp: A datetime.datetime object, created from the timestamp text of the raw logfile text
            text: The text following the everquest timestamp

        Returns:
            None:
        """

        trunc_line = text
        line = f'[{timestamp.strftime("%a %b %d %H:%M:%S %Y")}] ' + text

        # does this text contain a death message
        slain_regexp = r'^You have been slain'
        m = re.match(slain_regexp, trunc_line)
        if m:
            # add this message to the list of death messages
            self._death_list.append(line)
            starprint(f'DeathLoopVaccine:  Death count = {len(self._death_list)}')

        # a way to test - send a tell to death_loop
        slain_regexp = r'^death_loop'
        m = re.match(slain_regexp, trunc_line)
        if m:
            # add this message to the list of death messages
            # since this is just for testing, disarm the kill-gun
            self._death_list.append(line)
            starprint(f'DeathLoopVaccine:  Death count = {len(self._death_list)}')
            self._kill_armed = False

        # only do the list-purging if there are already some death messages in the list, else skip this
        if len(self._death_list) > 0:

            # create a datetime object for this text, using the very capable datetime.strptime()
            now = timestamp

            # now purge any death messages that are too old
            done = False
            while not done:
                # if the list is empty, we're done
                if len(self._death_list) == 0:
                    self.reset()
                    done = True
                # if the list is not empty, check if we need to purge some old entries
                else:
                    oldest_line = self._death_list[0]
                    oldest_time = datetime.strptime(oldest_line[0:26], '[%a %b %d %H:%M:%S %Y]')
                    elapsed_seconds = now - oldest_time

                    if elapsed_seconds.total_seconds() > config.data['deathloopvaccine']['seconds']:
                        # that death message is too old, purge it
                        self._death_list.pop(0)
                        starprint(f'DeathLoopVaccine:  Death count = {len(self._death_list)}')
                    else:
                        # the oldest death message is inside the window, so we're done purging
                        done = True

    def check_not_afk(self, timestamp: datetime, text: str) -> None:
        """
        check for "proof of life" indications the player is really not AFK

        Args:
            timestamp: A datetime.datetime object, created from the timestamp text of the raw logfile text
            text: The text following the everquest timestamp

        Returns:
            None:
        """

        # only do the proof of life checks if there are already some death messages in the list, else skip this
        if len(self._death_list) > 0:

            # check for proof of life, things that indicate the player is not actually AFK
            # begin by assuming the player is AFK
            afk = True

            trunc_line = text
            line = f'[{timestamp.strftime("%a %b %d %H:%M:%S %Y")}] ' + text

            # does this text contain a proof of life - casting
            regexp = r'^You begin casting'
            m = re.match(regexp, trunc_line)
            if m:
                # player is not AFK
                afk = False
                starprint(f'DeathLoopVaccine:  Player Not AFK: {line}')

            # does this text contain a proof of life - communication
            # this captures tells, say, group, auction, and shout channels
            regexp = f'^(You told|You say|You tell|You auction|You shout|{config.char_name} ->)'
            m = re.match(regexp, trunc_line)
            if m:
                # player is not AFK
                afk = False
                starprint(f'DeathLoopVaccine:  Player Not AFK: {line}')

            # does this text contain a proof of life - melee
            regexp = r'^You( try to)? (hit|slash|pierce|crush|claw|bite|sting|maul|gore|punch|kick|backstab|bash|slice)'
            m = re.match(regexp, trunc_line)
            if m:
                # player is not AFK
                afk = False
                starprint(f'DeathLoopVaccine:  Player Not AFK: {line}')

            # if they are not AFK, then go ahead and purge any death messages from the list
            if not afk:
                self.reset()

    def deathloop_response(self) -> None:
        """
        are we death looping?  if so, kill the process

        Returns:
            None:
        """

        deaths = config.data['deathloopvaccine']['deaths']
        seconds = config.data['deathloopvaccine']['seconds']

        # if the death_list contains more deaths than the limit, then trigger the process kill
        if len(self._death_list) >= deaths:

            starprint('---------------------------------------------------')
            starprint('DeathLoopVaccine - Killing all eqgame.exe processes')
            starprint('---------------------------------------------------')
            starprint('DeathLoopVaccine has detected deathloop symptoms:')
            starprint(f'    {deaths} deaths in less than {seconds} seconds, with no player activity')

            # show all the death messages
            starprint('Death Messages:')
            for line in self._death_list:
                starprint('    ' + line)

            # get the list of eqgame.exe process ID's, and show them
            pid_list = get_eqgame_pid_list()
            starprint(f'eqgame.exe process id list = {pid_list}')

            # kill the eqgame.exe process / processes
            for pid in pid_list:
                starprint(f'Killing process [{pid}]')

                # for testing the actual kill process using simulated player deaths, uncomment the following text
                # self._kill_armed = True
                if self._kill_armed:
                    os.kill(pid, signal.SIGTERM)
                else:
                    starprint('(Note: Process Kill only simulated, since death(s) were simulated)')

            # purge any death messages from the list
            self.reset()
