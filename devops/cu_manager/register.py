#!/usr/bin/python3
"""
Script that gather info from system used to register de computational unit
"""
#######################        MANDATORY IMPORTS         #######################

#######################         GENERIC IMPORTS          #######################

#######################       THIRD PARTY IMPORTS        #######################

#######################    SYSTEM ABSTRACTION IMPORTS    #######################
from system_logger_tool import sys_log_logger_get_module_logger, SysLogLoggerC, Logger

#######################       LOGGER CONFIGURATION       #######################
if __name__ == '__main__':
    cycler_logger = SysLogLoggerC(file_log_levels='./log_config.yaml')
log: Logger = sys_log_logger_get_module_logger(__name__)

#######################          PROJECT IMPORTS         #######################
from comm_data import CommDataCuC, CommDataRegisterTypeE

#######################          MODULE IMPORTS          #######################
import context

#######################              ENUMS               #######################

#######################             CLASSES              #######################

#######################            FUNCTIONS             #######################

def get_cu_info() -> CommDataCuC:
    """
    Function that gather info from system used to register de computational unit
    """
    # TODO: implement this function
    cu_info = CommDataCuC(msg_type=CommDataRegisterTypeE.REQUEST,\
        mac='dc:a6:32:61:68:14', user='plc', ip='192.168.0.80',\
        port=1883, hostname="plc", cu_id=1)

    return cu_info