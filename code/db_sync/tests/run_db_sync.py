#!/usr/bin/python3
"""
DB SYNC
"""
#######################        MANDATORY IMPORTS         #######################

#######################         GENERIC IMPORTS          #######################
import os
import sys
import threading

#######################       THIRD PARTY IMPORTS        #######################

#######################    SYSTEM ABSTRACTION IMPORTS    #######################
from system_logger_tool import sys_log_logger_get_module_logger, SysLogLoggerC, Logger

#######################       LOGGER CONFIGURATION       #######################
cycler_logger = SysLogLoggerC(file_log_levels='./config/db_sync/log_config.yaml',
                              output_sub_folder='db_sync')
log: Logger = sys_log_logger_get_module_logger(__name__)

#######################          MODULE IMPORTS          #######################
sys.path.append(os.path.dirname(__file__)+'/../')
from src.wattrex_cycler_db_sync import DbSyncNodeC

#######################          PROJECT IMPORTS         #######################

#######################              ENUMS               #######################

#######################             CLASSES              #######################

#######################            FUNCTIONS             #######################

if __name__ == '__main__':
    working_flag_event : threading.Event = threading.Event()
    working_flag_event.set()
    db_sync_node = DbSyncNodeC(working_flag=working_flag_event)
    db_sync_node.run()
