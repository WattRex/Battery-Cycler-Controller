#!/usr/bin/python3
"""
Cu Manager
"""
#######################        MANDATORY IMPORTS         #######################

#######################         GENERIC IMPORTS          #######################
from typing import List

#######################       THIRD PARTY IMPORTS        #######################

#######################    SYSTEM ABSTRACTION IMPORTS    #######################
from system_logger_tool import sys_log_logger_get_module_logger, SysLogLoggerC, Logger

#######################       LOGGER CONFIGURATION       #######################
if __name__ == '__main__':
    cycler_logger = SysLogLoggerC(file_log_levels='./log_config.yaml')
log: Logger = sys_log_logger_get_module_logger(__name__)

#######################          MODULE IMPORTS          #######################

#######################          PROJECT IMPORTS         #######################
from wattrex_battery_cycler_datatypes.comm_data import CommDataDeviceC

#######################              ENUMS               #######################

#######################             CLASSES              #######################

class DetectorC:
    def __init__(self) -> None:
        pass

    def process_detection(self) -> List[CommDataDeviceC]:
        # TODO: implement this
        dev = CommDataDeviceC(cu_id=1, comp_dev_id=1, serial_number=1, link_name="ACM0")
        return [dev]
