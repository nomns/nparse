import logging
import logging.handlers

from helpers import Parser
from parsers.LogEvent import *


# list of rsyslog (host, port) information
# todo - move this info to config file
# todo - add Stanvern server rsyslog hostname/port to this list
remote_list = [
    ('192.168.1.127', 514),
    ('ec2-3-133-158-247.us-east-2.compute.amazonaws.com', 22514),
]


#
# create a global list of parsers
#
log_event_list = [
    VesselDrozlin_Event(),
    VerinaTomb_Event(),
    MasterYael_Event(),
    DainFrostreaverIV_Event(),
    Severilous_Event(),
    CazicThule_Event(),
    FTE_Event(),
    PlayerSlain_Event(),
    Earthquake_Event(),
    Random_Event(),
    AnythingButComms_Event(),
    Gratss_Event(),
    TOD_Event(),
    GMOTD_Event(),
]


#
# todo - replace this with code to retrieve settings from config file
# todo - this code just turns them all on, except for the ABC parser
for log_entry in log_event_list:
    # parse_dict[log_entry.__class__.__name] = True
    if log_entry.log_event_ID == LOGEVENT_ABC:
        log_entry.parse = False
    else:
        log_entry.parse = True


#################################################################################################
#
# class to do all the LogEvent work
#
class LogEventParser(Parser):

    # ctor
    def __init__(self):
        super().__init__()

        super().__init__()
        # self.name = 'logeventparser'
        self.name = self.__class__.__name__

        # set up a custom logger to use for rsyslog comms
        self.logger_list = []
        for (host, port) in remote_list:
            eq_logger = logging.getLogger(f'{host}:{port}')
            eq_logger.setLevel(logging.INFO)

            # create a handler for the rsyslog communications
            log_handler = logging.handlers.SysLogHandler(address=(host, port))
            eq_logger.addHandler(log_handler)
            self.logger_list.append(eq_logger)

    def set_char_name(self, name: str) -> None:
        """
        override base class setter function to also sweep through list of parse targets
        and set their parsing player names

        Args:
            name: player whose log file is being parsed
        """

        # todo - gotta get nparse to call this whenever it switches log files/toons
        global log_event_list
        for log_event in log_event_list:
            log_event.parsing_player = name

    #
    #
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

        # the global list of log_events
        global log_event_list

        # check current text for matches in any of the list of Parser objects
        # if we find a match, then send the event report to the remote aggregator
        for log_event in log_event_list:
            if log_event.matches(timestamp, text):
                report_str = log_event.report()

                # send the info to the remote log aggregator
                for logger in self.logger_list:
                    logger.info(report_str)
