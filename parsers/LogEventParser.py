import logging.handlers

from helpers import Parser
from parsers.LogEvent import *

# todo - store/retrieve this info from config file
# this info is stored in an ini file as shown:
# [rsyslog servers]
# server1 = 192.168.1.127:514
# server2 = ec2-3-133-158-247.us-east-2.compute.amazonaws.com:22514
# server3 = stanvern-hostname:port

# todo - replace this global with info from config file
rsyslog_servers = {'server1': '192.168.1.127:514',
                   'server2': 'ec2-3-133-158-247.us-east-2.compute.amazonaws.com:22514',
                   'server3': 'stanvern-hostname:port'}

# todo - store/retrieve this info from config file
# this info is stored in an ini file as shown:
# [LogEventParser]
# vesseldrozlin_event = True, server1, server2, server3
# verinatomb_event = True, server1, server2, server3
# dainfrostreaveriv_event = True, server1, server2, server3
# severilous_event = True, server1, server2, server3
# cazicthule_event = True, server1, server2, server3
# masteryael_event = True, server1, server2, server3
# fte_event = True, server1, server2, server3
# playerslain_event = True, server1, server2, server3
# earthquake_event = True, server1, server2, server3
# random_event = True, server1, server2, server3
# anythingbutcomms_event = False, server3
# gratss_event = True, server1, server2, server3
# tod_event = True, server1, server2, server3
# gmotd_event = True, server1, server2, server3
# tod_lowfidelity_event = True, server1, server2, server3
# tod_highfidelity_event = True, server1, server2, server3

# todo - replace this global with info from config file
parser_config_dict = {'VesselDrozlin_Event': 'True, server1, server2, server3',
                      'VerinaTomb_Event': 'True, server1, server2, server3',
                      'DainFrostreaverIV_Event': 'True, server1, server2, server3',
                      'Severilous_Event': 'True, server1, server2, server3',
                      'CazicThule_Event': 'True, server1, server2, server3',
                      'MasterYael_Event': 'True, server1, server2, server3',
                      'FTE_Event': 'True, server1, server2, server3',
                      'PlayerSlain_Event': 'True, server1, server2, server3',
                      'Earthquake_Event': 'True, server1, server2, server3',
                      'Random_Event': 'True, server1, server2, server3',
                      'AnythingButComms_Event': 'False, server3',
                      'Gratss_Event': 'True, server1, server2, server3',
                      'TOD_LowFidelity_Event': 'True, server1, server2, server3',
                      'GMOTD_Event': 'True, server1, server2, server3',
                      'TOD_HighFidelity_Event': 'True, server1, server2, server3'}

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
    TOD_LowFidelity_Event(),
    GMOTD_Event(),
    TOD_HighFidelity_Event(),
]


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
        self.logger_dict = {}
        # server_list = config.config_data.options('rsyslog servers')
        # todo - get this info from config file rather than a global dict
        server_list = rsyslog_servers.keys()
        for server in server_list:
            try:
                # host_port_str = config.config_data.get('rsyslog servers', server)
                host_port_str = rsyslog_servers[server]
                host_port_list = host_port_str.split(':')
                host = host_port_list[0]
                # this will throw an exception if the port number isn't an integer
                port = int(host_port_list[1])
                print(f'{host}, {port}')

                # create a handler for the rsyslog communications, with level INFO
                # this will throw an exception if host:port are nonsensical
                log_handler = logging.handlers.SysLogHandler(address=(host, port))
                eq_logger = logging.getLogger(f'{host}:{port}')
                eq_logger.setLevel(logging.INFO)

                # log_handler.setLevel(logging.INFO)
                eq_logger.addHandler(log_handler)

                # create a handler for console, and set level to 100 to ensure it is silent
                # console_handler = logging.StreamHandler(sys.stdout)
                # console_handler.setLevel(100)
                # eq_logger.addHandler(console_handler)
                self.logger_dict[server] = eq_logger

            except ValueError:
                pass

        # print(self.logger_dict)

        # now walk the list of parsers and set their logging parameters
        for log_event in log_event_list:
            # log_settings_str = config.config_data.get('LogEventParser', log_event.__class__.__name__)
            # todo - get this info from config file rather than a global dict
            log_settings_str = parser_config_dict[log_event.__class__.__name__]

            log_settings_list = log_settings_str.split(', ')

            # the 0-th element is a true/false parse flag
            if log_settings_list[0].lower() == 'true':
                log_event.parse = True
            else:
                log_event.parse = False

            # index 1 and beyond are rsyslog servers
            for n, elem in enumerate(log_settings_list):
                if n != 0:
                    server = log_settings_list[n]
                    if server in self.logger_dict.keys():
                        log_event.add_logger(self.logger_dict[server])

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
                log_event.log_report()
