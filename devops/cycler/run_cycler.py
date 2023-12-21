#!/usr/bin/python3
"""
Cu Manager
"""
#######################        MANDATORY IMPORTS         #######################

#######################         GENERIC IMPORTS          #######################
import os
import sys
from threading import Event

#######################       THIRD PARTY IMPORTS        #######################

#######################    SYSTEM ABSTRACTION IMPORTS    #######################
from system_logger_tool import sys_log_logger_get_module_logger, SysLogLoggerC, Logger

#######################       LOGGER CONFIGURATION       #######################
CS_ID = os.getenv("CSID")
if __name__ == '__main__':
    cycler_logger = SysLogLoggerC(file_log_levels='./devops/cycler/log_config.yaml',
                                  output_sub_folder=f'cycler_{CS_ID}')
log: Logger = sys_log_logger_get_module_logger(__name__)
log.critical(f'CS_ID: {CS_ID}')

#######################          MODULE IMPORTS          #######################
# sys.path.append(os.getcwd()+'/code/cycler/')
# from src.wattrex_battery_cycler.app.app_man import AppManNodeC
from wattrex_battery_cycler.app.app_man import AppManNodeC

#######################          PROJECT IMPORTS         #######################

#######################              ENUMS               #######################

#######################             CLASSES              #######################

#######################            FUNCTIONS             #######################
if __name__ == '__main__':
    working_flag_event : Event = Event()
    working_flag_event.set()
    cs_manager: AppManNodeC = AppManNodeC(cs_id= CS_ID, working_flag= working_flag_event)
    log.critical('Starting the manager')
    try:
        cs_manager.run()
    except KeyboardInterrupt:
        working_flag_event.clear()
