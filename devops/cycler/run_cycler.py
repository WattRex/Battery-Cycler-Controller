#!/usr/bin/python3
"""
Cu Manager
"""
#######################        MANDATORY IMPORTS         #######################

#######################         GENERIC IMPORTS          #######################
import os
import sys
import threading
from time import sleep

#######################       THIRD PARTY IMPORTS        #######################

#######################    SYSTEM ABSTRACTION IMPORTS    #######################
from system_logger_tool import sys_log_logger_get_module_logger, SysLogLoggerC, Logger

#######################       LOGGER CONFIGURATION       #######################
CS_ID = os.getenv("CSID")
if __name__ == '__main__':
    cycler_logger = SysLogLoggerC(file_log_levels='./devops/cycler/log_config.yaml', output_sub_folder=f'cycler_{CS_ID}')
log: Logger = sys_log_logger_get_module_logger(__name__)

#######################          MODULE IMPORTS          #######################
# from wattrex_battery_cycler_cu_manager import CuManagerNodeC

#######################          PROJECT IMPORTS         #######################

#######################              ENUMS               #######################

#######################             CLASSES              #######################

#######################            FUNCTIONS             #######################
if __name__ == '__main__':
    # working_flag_event : threading.Event = threading.Event()
    # working_flag_event.set()
    # cu_manager_node = CuManagerNodeC(working_flag=working_flag_event,
    #                                       cycle_period=1000,
    #                                       cu_id_file_path='./devops/cu_manager/cu_id')
    # cu_manager_node.run()

    while 1:
        log.critical('Ha pasado 1 minuto desde que pasó el último')
        sleep(1)
