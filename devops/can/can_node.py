#!/usr/bin/python3
"""
This is an example of use of the can module.
"""
#######################        MANDATORY IMPORTS         #######################
from __future__ import annotations
import sys
import os
#######################         GENsERIC IMPORTS          #######################
from time import sleep
from threading import Event
#######################    SYSTEM ABSTRACTION IMPORTS    #######################
# Change path to the root of the project
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname + "/../../")

from system_logger_tool import sys_log_logger_get_module_logger, SysLogLoggerC, Logger
#######################       LOGGER CONFIGURATION       #######################

if __name__ == '__main__':
    cycler_logger = SysLogLoggerC(file_log_levels='./devops/can/log_config.yaml', output_sub_folder='can')
log: Logger = sys_log_logger_get_module_logger(__name__)

#######################          MODULE IMPORTS          #######################
from can_sniffer import DrvCanNodeC


#######################            FUNCTIONS             #######################
if __name__ == '__main__':
    # Flag to know if the can is working
    _working_can = Event()
    _working_can.set()
    #Create the thread for CAN
    can = DrvCanNodeC(tx_buffer_size= 150, working_flag=_working_can)
    try:
        can.run()
    except KeyboardInterrupt:
        _working_can.clear()
        log.info('CAN node stopped')
        sys.exit(0)
