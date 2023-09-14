#!/usr/bin/python3
'''
_______________________________________________________________________________
'''

#######################        MANDATORY IMPORTS         #######################
from sys import path
import os

#######################         GENERIC IMPORTS          #######################

#######################       THIRD PARTY IMPORTS        #######################

#######################      SYSTEM ABSTRACTION IMPORTS  #######################
path.append(os.getcwd())
from system_logger_tool import SysLogLoggerC, sys_log_logger_get_module_logger # pylint: disable=wrong-import-position
if __name__ == '__main__':
    cycler_logger = SysLogLoggerC(file_log_levels='./log_config.yaml')
log = sys_log_logger_get_module_logger(__name__)

#######################          PROJECT IMPORTS         #######################

#######################          MODULE IMPORTS          #######################
from mid_sync import MidSyncNodeC # pylint: disable=wrong-import-position

#######################              ENUMS               #######################

#######################              CLASSES             #######################

def main():
    '''Main function.'''
    comp_unit = 1
    cycle_period = 1
    node = MidSyncNodeC(comp_unit = comp_unit, cycle_period = cycle_period)
    node.process_iterarion()

if __name__ == '__main__':
    main()
