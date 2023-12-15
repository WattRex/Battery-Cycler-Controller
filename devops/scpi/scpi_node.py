#!/usr/bin/python3
"""
This is an example of use of the scpi module.
"""
#######################        MANDATORY IMPORTS         #######################
from __future__ import annotations
import sys
import os
#######################         GENsERIC IMPORTS          #######################
from threading import Event
#######################    SYSTEM ABSTRACTION IMPORTS    #######################
# Change path to the root of the project
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname + "/../../")

from system_logger_tool import sys_log_logger_get_module_logger, SysLogLoggerC, Logger
#######################       LOGGER CONFIGURATION       #######################

if __name__ == '__main__':
    cycler_logger = SysLogLoggerC(file_log_levels='./devops/scpi/log_config.yaml',
                                  output_sub_folder='scpi')
log: Logger = sys_log_logger_get_module_logger(__name__)

#######################          MODULE IMPORTS          #######################
from scpi_sniffer import DrvScpiNodeC

#######################            FUNCTIONS             #######################
if __name__ == '__main__':
    # Flag to know in next steps if the scpi is working
    _working_scpi = Event()
    _working_scpi.set()
    #Create the thread for SCPI
    scpi = DrvScpiNodeC(working_flag=_working_scpi, cycle_period=200)
    try:
        scpi.run()
    except KeyboardInterrupt:
        _working_scpi.clear()
        log.info('SCPI node stopped')
        sys.exit(0)
