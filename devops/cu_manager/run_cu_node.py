#!/usr/bin/python3
"""
Cu Manager
"""
#######################        MANDATORY IMPORTS         #######################

#######################         GENERIC IMPORTS          #######################
import sys, os
import threading

#######################       THIRD PARTY IMPORTS        #######################

#######################    SYSTEM ABSTRACTION IMPORTS    #######################
from system_logger_tool import sys_log_logger_get_module_logger, SysLogLoggerC, Logger

#######################       LOGGER CONFIGURATION       #######################
if __name__ == '__main__':
    cycler_logger = SysLogLoggerC(file_log_levels='./log_config.yaml')
log: Logger = sys_log_logger_get_module_logger(__name__)

#######################          MODULE IMPORTS          #######################
from wattrex_battery_cycler_cu_manager import CuManagerNodeC

#######################          PROJECT IMPORTS         #######################

#######################              ENUMS               #######################

#######################             CLASSES              #######################

#######################            FUNCTIONS             #######################

if __name__ == '__main__':
    working_flag_event : threading.Event = threading.Event()
    working_flag_event.set()
    cu_manager_node = CuManagerNodeC(working_flag=working_flag_event,
                                          cycle_period=1000,
                                          cu_id_file_path='./devops/.cu_id')
    cu_manager_node.run()
