import re
import time
import logging
from datetime import datetime, timezone, timedelta


# define some ID constants for the derived classes
LOGEVENT_BASE: int = 0
LOGEVENT_VD: int = 1
LOGEVENT_VT: int = 2
LOGEVENT_YAEL: int = 3
LOGEVENT_DAIN: int = 4
LOGEVENT_SEV: int = 5
LOGEVENT_CT: int = 6
LOGEVENT_FTE: int = 7
LOGEVENT_PLAYERSLAIN: int = 8
LOGEVENT_QUAKE: int = 9
LOGEVENT_RANDOM: int = 10
LOGEVENT_ABC: int = 11
LOGEVENT_GRATSS: int = 12
LOGEVENT_TODLO: int = 13
LOGEVENT_GMOTD: int = 14
LOGEVENT_TODHI: int = 15


#########################################################################################################################
#
# Base class
#
# Notes for the developer:
#   - derived classes constructor should correctly populate the following fields, according to whatever event this
#     parser is watching for:
#           self.log_event_ID, a unique integer for each LogEvent class, to help the server side
#           self.short_description, a text description, and
#           self._search_list, a list of regular expression(s) that indicate this event has happened
#   - derived classes can optionally override the _custom_match_hook() method, if special/extra parsing is needed,
#     or if a customized self.short_description is desired.  This method gets called from inside the standard matches()
#     method.  The default base case behavior is to simply return True.
#           see Random_Event() class for a good example, which deals with the fact that Everquest /random events
#           are actually reported in TWO lines of text in the log file
#
#   - See the example derived classes in this file to get a better idea how to set these items up
#
#   - IMPORTANT:  These classes make use of the self.parsing_player field to embed the character name in the report.
#     If and when the parser begins parsing a new log file, it is necessary to sweep through whatever list of LogEvent
#     objects are being maintained, and update the self.parsing_player field in each LogEvent object, e.g. something like:
#
#             for log_event in self.log_event_list:
#                 log_event.parsing_player = name
#
#########################################################################################################################

#
#
class LogEvent:
    """
    Base class that encapsulates all information about any particular event that is detected in a logfile
    """

    #
    #
    def __init__(self):
        """
        constructor
        """

        # boolean for whether a LogEvent class should be checked.
        # controlled by the ini file setting
        self.parse = True
        # self.parse = config.config_data.getboolean('LogEventParser', self.__class__.__name__)

        # list of logging.Logger objects
        self.logger_list = []

        # modify these as necessary in child classes
        self.log_event_ID = LOGEVENT_BASE
        self.short_description = 'Generic Target Name spawn!'
        self._search_list = [
            '^Generic Target Name begins to cast a spell',
            '^Generic Target Name engages (?P<playername>[\\w ]+)!',
            '^Generic Target Name has been slain',
            '^Generic Target Name says',
            '^You have been slain by Generic Target Name'
        ]

        # the actual line from the logfile
        self._matching_line = None

        # timezone info
        self._local_datetime = None
        self._utc_datetime = None

        # parsing player name and field separation character, used in the report() function
        self.parsing_player = 'Unknown'
        self.field_separator = '|'
        self.eqmarker = 'EQ__'

    #
    #
    def matches(self, eq_datetime: datetime, text: str) -> bool:
        """
        Check to see if the passed text matches the search criteria for this LogEvent

        Args:
            eq_datetime: a datetime object constructed from the leading 26 characters of the line of text from the logfile
            text: text of text from the logfile WITHOUT the EQ date-time stamp

        Returns:
            True/False

        """
        # return value
        rv = False

        if self.parse:
            # # cut off the leading date-time stamp info
            # trunc_line = text[27:]

            # walk through the target list and trigger list and see if we have any match
            for trigger in self._search_list:

                # return value m is either None of an object with information about the RE search
                m = re.match(trigger, text)
                if m:

                    # allow for any additional logic to be applied, if needed, by derived classes
                    if self._custom_match_hook(m, eq_datetime, text):
                        rv = True

                        # save the matching text and set the timestamps
                        self._set_timestamps(eq_datetime, text)

        # return self.matched
        return rv

    #
    # send the re.Match info, as well as the datetime stamp and line text, in case the info is needed
    def _custom_match_hook(self, m: re.Match, eq_datetime: datetime, text: str) -> bool:
        """
        provide a hook for derived classes to override this method and specialize the search
        default action is simply return true

        Args:
            m: re.Match object from the search
            eq_datetime: a datetime object constructed from the leading 26 characters of the line of text from the logfile
            text: text of text from the logfile WITHOUT the EQ date-time stamp

        Returns:
            True/False if this is a match
        """
        return True

    def _set_timestamps(self, eq_datetime: datetime, text: str) -> None:
        """
        Utility function to set the local and UTC timestamp information,
        using the EQ timestamp information present in the first 26 characters
        of every Everquest log file text

        Args:
            eq_datetime: a datetime object constructed from the leading 26 characters of the line of text from the logfile
            text: text of text from the logfile WITHOUT the EQ date-time stamp
        """

        # save the matching line by reconstructing the entire EQ log line
        self._matching_line = f"{eq_datetime.strftime('[%a %b %d %H:%M:%S %Y]')} " + text

        # the passed eq_datetime is a naive datetime, i.e. it doesn't know the TZ
        # convert it to an aware datetime, by adding the local tzinfo using replace()
        # time.timezone = offset of the local, non-DST timezone, in seconds west of UTC
        local_tz = timezone(timedelta(seconds=-time.timezone))
        self._local_datetime = eq_datetime.replace(tzinfo=local_tz)

        # now convert it to a UTC datetime
        self._utc_datetime = self._local_datetime.astimezone(timezone.utc)

        # print(f'{eq_datetime}')
        # print(f'{self._local_datetime}')
        # print(f'{self._utc_datetime}')

    #
    #
    def report(self) -> str:
        """
        Return a line of text with all relevant data for this event,
        separated by the field_separation character

        Returns:
            str: single line with all fields
        """
        rv = f'{self.eqmarker}{self.field_separator}'
        rv += f'{self.parsing_player}{self.field_separator}'
        rv += f'{self.log_event_ID}{self.field_separator}'
        rv += f'{self.short_description}{self.field_separator}'
        rv += f'{self._utc_datetime}{self.field_separator}'
        # rv += f'{self._local_datetime}{self.field_separator}'
        rv += f'{self._matching_line}'
        return rv

    #
    #
    def add_logger(self, logger: logging.Logger) -> None:
        """
        Add logger to this object

        Args:
            logger: a logging.Logger object
        """
        self.logger_list.append(logger)

    #
    #
    def log_report(self) -> None:
        """
        send the report for this event to every registered logger
        """
        report_str = self.report()
        for logger in self.logger_list:
            logger.info(report_str)


#########################################################################################################################
#
# Derived classes
#

class VesselDrozlin_Event(LogEvent):
    """
    Parser for Vessel Drozlin spawn
    """

    def __init__(self):
        super().__init__()
        self.log_event_ID = LOGEVENT_VD
        self.short_description = 'Vessel Drozlin spawn!'
        self._search_list = [
            '^Vessel Drozlin begins to cast a spell',
            '^Vessel Drozlin engages (?P<playername>[\\w ]+)!',
            '^Vessel Drozlin has been slain',
            '^Vessel Drozlin says',
            '^You have been slain by Vessel Drozlin'
        ]


class VerinaTomb_Event(LogEvent):
    """
    Parser for Verina Tomb spawn
    """

    def __init__(self):
        super().__init__()
        self.log_event_ID = LOGEVENT_VT
        self.short_description = 'Verina Tomb spawn!'
        self._search_list = [
            '^Verina Tomb begins to cast a spell',
            '^Verina Tomb engages (?P<playername>[\\w ]+)!',
            '^Verina Tomb has been slain',
            '^Verina Tomb says',
            '^You have been slain by Verina Tomb'
        ]


class MasterYael_Event(LogEvent):
    """
    Parser for Master Yael spawn
    """

    def __init__(self):
        super().__init__()
        self.log_event_ID = LOGEVENT_YAEL
        self.short_description = 'Master Yael spawn!'
        self._search_list = [
            '^Master Yael begins to cast a spell',
            '^Master Yael engages (?P<playername>[\\w ]+)!',
            '^Master Yael has been slain',
            '^Master Yael says',
            '^You have been slain by Master Yael'
        ]


class DainFrostreaverIV_Event(LogEvent):
    """
    Parser for Dain Frostreaver IV spawn
    """

    def __init__(self):
        super().__init__()
        self.log_event_ID = LOGEVENT_DAIN
        self.short_description = 'Dain Frostreaver IV spawn!'
        self._search_list = [
            '^Dain Frostreaver IV engages (?P<playername>[\\w ]+)!',
            '^Dain Frostreaver IV says',
            '^Dain Frostreaver IV has been slain',
            '^You have been slain by Dain Frostreaver IV'
        ]


class Severilous_Event(LogEvent):
    """
    Parser for Severilous spawn
    """

    def __init__(self):
        super().__init__()
        self.log_event_ID = LOGEVENT_SEV
        self.short_description = 'Severilous spawn!'
        self._search_list = [
            '^Severilous begins to cast a spell',
            '^Severilous engages (?P<playername>[\\w ]+)!',
            '^Severilous has been slain',
            '^Severilous says',
            '^You have been slain by Severilous'
        ]


class CazicThule_Event(LogEvent):
    """
    Parser for Cazic Thule spawn
    """

    def __init__(self):
        super().__init__()
        self.log_event_ID = LOGEVENT_CT
        self.short_description = 'Cazic Thule spawn!'
        self._search_list = [
            '^Cazic Thule engages (?P<playername>[\\w ]+)!',
            '^Cazic Thule has been slain',
            '^Cazic Thule says',
            '^You have been slain by Cazic Thule',
            "Cazic Thule  shouts 'Denizens of Fear, your master commands you to come forth to his aid!!"
        ]


class FTE_Event(LogEvent):
    """
    Parser for general FTE messages
    overrides _additional_match_logic() for additional info to be captured
    """

    def __init__(self):
        super().__init__()
        self.log_event_ID = LOGEVENT_FTE
        self.short_description = 'FTE'
        self._search_list = [
            '^(?P<target_name>[\\w ]+) engages (?P<playername>[\\w ]+)!'
        ]

    # overload the default base class behavior to add some additional logic
    def _custom_match_hook(self, m: re.Match, eq_datetime: datetime, text: str) -> bool:
        if m:
            target_name = m.group('target_name')
            playername = m.group('playername')
            self.short_description = f'FTE: {target_name} engages {playername}'
            return True


class PlayerSlain_Event(LogEvent):
    """
    Parser for player has been slain
    """

    def __init__(self):
        super().__init__()
        self.log_event_ID = LOGEVENT_PLAYERSLAIN
        self.short_description = 'Player Slain!'
        self._search_list = [
            '^You have been slain by (?P<target_name>[\\w ]+)'
        ]


class Earthquake_Event(LogEvent):
    """
    Parser for Earthquake
    """

    def __init__(self):
        super().__init__()
        self.log_event_ID = LOGEVENT_QUAKE
        self.short_description = 'Earthquake!'
        self._search_list = [
            '^The Gods of Norrath emit a sinister laugh as they toy with their creations'
        ]


class Random_Event(LogEvent):
    """
    Parser for Random (low-high)
    overrides _additional_match_logic() for additional info to be captured
    """

    def __init__(self):
        super().__init__()
        self.playername = None
        self.low = -1
        self.high = -1
        self.value = -1
        self.log_event_ID = LOGEVENT_RANDOM
        self.short_description = 'Random!'
        self._search_list = [
            '\\*\\*A Magic Die is rolled by (?P<playername>[\\w ]+)\\.',
            '\\*\\*It could have been any number from (?P<low>[0-9]+) to (?P<high>[0-9]+), but this time it turned up a (?P<value>[0-9]+)\\.'
        ]

    # overload the default base class behavior to add some additional logic
    def _custom_match_hook(self, m: re.Match, eq_datetime: datetime, text: str) -> bool:
        rv = False
        if m:
            # if m is true, and contains the playername group, this represents the first text of the random dice roll event
            # save the playername for later
            if 'playername' in m.groupdict().keys():
                self.playername = m.group('playername')
            # if m is true but doesn't have the playername group, then this represents the second text of the random dice roll event
            else:
                self.low = m.group('low')
                self.high = m.group('high')
                self.value = m.group('value')
                self.short_description = f'Random roll: {self.playername}, {self.low}-{self.high}, Value={self.value}'
                rv = True

        return rv


class AnythingButComms_Event(LogEvent):
    """
    Parser for Comms Filter
    allows filtering on/off the various communications channels
    """

    def __init__(self):
        super().__init__()
        self.parse = False

        # individual communication channel exclude flags,
        # just in case wish to customize this later for finer control, for whatever reason
        # this is probably overkill...
        exclude_tell = True
        exclude_say = True
        exclude_group = True
        exclude_auc = True
        exclude_ooc = True
        exclude_shout = True
        exclude_guild = True

        # tells
        # [Sun Sep 18 15:22:41 2022] You told Snoiche, 'gotcha'
        # [Sun Sep 18 15:16:43 2022] Frostclaw tells you, 'vog plz'
        # [Thu Aug 18 14:31:34 2022] Azleep -> Berrma: have you applied?
        # [Thu Aug 18 14:31:48 2022] Berrma -> Azleep: ya just need someone to invite i believe
        tell_regex = ''
        if exclude_tell:
            tell_regex1 = "You told [\\w]+, '"
            tell_regex2 = "[\\w]+ tells you, '"
            tell_regex3 = "[\\w]+ -> [\\w]+:"
            # note that the tell_regexN bits filter tells IN, and then we surround it with (?! ) to filter then OUT
            tell_regex = f'(?!^{tell_regex1}|{tell_regex2}|{tell_regex3})'

        # say
        # [Sat Aug 13 15:36:21 2022] You say, 'lfg'
        # [Sun Sep 18 15:17:28 2022] Conceded says, 'where tf these enchs lets goo'
        say_regex = ''
        if exclude_say:
            say_regex1 = "You say, '"
            say_regex2 = "[\\w]+ says, '"
            say_regex = f'(?!^{say_regex1}|{say_regex2})'

        # group
        # [Fri Aug 12 18:12:46 2022] You tell your party, 'Mezzed << froglok ilis knight >>'
        # [Fri Aug 12 18:07:08 2022] Mezmurr tells the group, 'a << myconid reaver >> is slowed'
        group_regex = ''
        if exclude_group:
            group_regex1 = "You tell your party, '"
            group_regex2 = "[\\w]+ tells the group, '"
            group_regex = f'(?!^{group_regex1}|{group_regex2})'

        # auction
        # [Wed Jul 20 15:39:25 2022] You auction, 'wts Smoldering Brand // Crystal Lined Slippers // Jaded Electrum Bracelet // Titans Fist'
        # [Wed Sep 21 17:54:28 2022] Dedguy auctions, 'WTB Crushed Topaz'
        auc_regex = ''
        if exclude_auc:
            auc_regex1 = "You auction, '"
            auc_regex2 = "[\\w]+ auctions, '"
            auc_regex = f'(?!^{auc_regex1}|{auc_regex2})'

        # ooc
        # [Sat Aug 20 22:19:09 2022] You say out of character, 'Sieved << a scareling >>'
        # [Sun Sep 18 15:25:39 2022] Piesy says out of character, 'Come port with the Puffbottom Express and <Dial a Port>! First-Class travel'
        ooc_regex = ''
        if exclude_ooc:
            ooc_regex1 = "You say out of character, '"
            ooc_regex2 = "[\\w]+ says out of character, '"
            ooc_regex = f'(?!^{ooc_regex1}|{ooc_regex2})'

        # shout
        # [Fri Jun 04 16:16:41 2021] You shout, 'I'M SORRY WILSON!!!'
        # [Sun Sep 18 15:21:05 2022] Abukii shouts, 'ASSIST --       Cleric of Zek '
        shout_regex = ''
        if exclude_shout:
            shout_regex1 = "You shout, '"
            shout_regex2 = "[\\w]+ shouts, '"
            shout_regex = f'(?!^{shout_regex1}|{shout_regex2})'

        # guild
        # [Fri Aug 12 22:15:07 2022] You say to your guild, 'who got fright'
        # [Fri Sep 23 14:18:03 2022] Kylarok tells the guild, 'whoever was holding the chain coif for Pocoyo can nvermind xD'
        guild_regex = ''
        if exclude_guild:
            guild_regex1 = "You say to your guild, '"
            guild_regex2 = "[\\w]+ tells the guild, '"
            guild_regex = f'(?!^{guild_regex1}|{guild_regex2})'

        # put them all together
        # if we weren't interested in being able to filter only some channels, then this could
        # all be boiled down to just
        #       (?!^[\\w]+ (told|tell(s)?|say(s)?|auction(s)?|shout(s)?|-> [\\w]+:))
        self.log_event_ID = LOGEVENT_ABC
        self.short_description = 'Comms Filter'
        self._search_list = [
            f'{tell_regex}{say_regex}{group_regex}{auc_regex}{ooc_regex}{shout_regex}{guild_regex}',
        ]


class Gratss_Event(LogEvent):
    """
    Parser for gratss messages
    """

    def __init__(self):
        super().__init__()
        self.log_event_ID = LOGEVENT_GRATSS
        self.short_description = 'Possible Gratss sighting!'
        self._search_list = [
            ".*gratss(?i)",
        ]


class TOD_HighFidelity_Event(LogEvent):
    """
    Parser for tod messages

    Low fidelity version:  if someone says 'tod' in one of the channels
    High fidelity version: the phrase 'XXX has been slain', where XXX is one of the known targets of interest
    """

    def __init__(self):
        super().__init__()
        self.log_event_ID = LOGEVENT_TODHI
        self.short_description = 'TOD'
        self._search_list = [
            '^(?P<target_name>[\\w ]+) has been slain',
        ]

        self.known_targets = [
            'Kelorek`Dar',
            'Vaniki',
            'Vilefang',
            'Zlandicar',
            'Narandi the Wretched',
            'Lodizal',
            'Stormfeather',
            'Dain Frostreaver IV',
            'Derakor the Vindicator',
            'Keldor Dek`Torek',
            'King Tormax',
            'The Statue of Rallos Zek',
            'The Avatar of War',
            'Tunare',
            'Lord Yelinak',
            'Master of the Guard',
            'The Final Arbiter',
            'The Progenitor',
            'An angry goblin',
            'Casalen',
            'Dozekar the Cursed',
            'Essedera',
            'Grozzmel',
            'Krigara',
            'Lepethida',
            'Midayor',
            'Tavekalem',
            'Ymmeln',
            'Aaryonar',
            'Cekenar',
            'Dagarn the Destroyer',
            'Eashen of the Sky',
            'Ikatiar the Venom',
            'Jorlleag',
            'Lady Mirenilla',
            'Lady Nevederia',
            'Lord Feshlak',
            'Lord Koi`Doken',
            'Lord Kreizenn',
            'Lord Vyemm',
            'Sevalak',
            'Vulak`Aerr',
            'Zlexak',
            'Gozzrem',
            'Lendiniara the Keeper',
            'Telkorenar',
            'Wuoshi',
            'Druushk',
            'Hoshkar',
            'Nexona',
            'Phara Dar',
            'Silverwing',
            'Xygoz',
            'Lord Doljonijiarnimorinar',
            'Velketor the Sorcerer',
            'Guardian Kozzalym',
            'Klandicar',
            'Myga NE PH',
            'Myga ToV PH',
            'Scout Charisa',
            'Sontalak',
            'Gorenaire',
            'Vessel Drozlin',
            'Severilous',
            'Venril Sathir',
            'Trakanon',
            'Talendor',
            'Faydedar',
            'a shady goblin',
            'Phinigel Autropos',
            'Lord Nagafen',
            'Zordak Ragefire',
            'Verina Tomb',
            'Lady Vox',
            'A dracoliche',
            'Cazic Thule',
            'Dread',
            'Fright',
            'Terror',
            'Wraith of a Shissir',
            'Innoruuk',
            'Noble Dojorn',
            'Nillipuss',
            'Master Yael',
            'Sir Lucan D`Lere',
        ]

    # overload the default base class behavior to add some additional logic
    def _custom_match_hook(self, m: re.Match, eq_datetime: datetime, text: str) -> bool:
        rv = False
        if m:
            # reset the description in case it has been set to something else
            self.short_description = 'TOD'
            if 'target_name' in m.groupdict().keys():
                target_name = m.group('target_name')
                if target_name in self.known_targets:
                    # since we saw the 'has been slain' message,
                    # change the short description to a more definitive TOD message
                    rv = True
                    self.short_description = f'TOD, High Fidelity: {target_name}'

        return rv


class TOD_LowFidelity_Event(LogEvent):

    """
    Parser for tod messages

    Low fidelity version:  if someone says 'tod' in one of the channels
    High fidelity version: the phrase 'XXX has been slain', where XXX is one of the known targets of interest
    """

    def __init__(self):
        super().__init__()
        self.log_event_ID = LOGEVENT_TODLO
        self.short_description = 'Possible TOD sighting!'
        self._search_list = [
            ".*tod(?i)",
        ]


class GMOTD_Event(LogEvent):
    """
    Parser for GMOTD messages
    """

    def __init__(self):
        super().__init__()
        self.log_event_ID = LOGEVENT_GMOTD
        self.short_description = 'GMOTD'
        self._search_list = [
            '^GUILD MOTD:',
        ]
