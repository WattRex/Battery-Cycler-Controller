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
from system_logger_tool import sys_log_logger_get_module_logger, SysLogLoggerC, Logger
#######################       LOGGER CONFIGURATION       #######################
if __name__ == '__main__':
    cycler_logger = SysLogLoggerC(file_log_levels=os.environ["R_PATH"]+'/log_config.yaml')
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
        while 1:
            sleep(300)
            print("Elapsed time: 5 minutes")
    except KeyboardInterrupt:
        _working_can.clear()
        # can_queue.terminate()
        # rx_queue.terminate()
        can.join()
        log.info('closing everything')
        sys.exit(0)
