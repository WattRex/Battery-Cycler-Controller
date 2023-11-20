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
from mid_sync import MidSyncNodeC, MidSyncFachadeC # pylint: disable=wrong-import-position
from wattrex_driver_db import *

#######################              ENUMS               #######################

#######################              CLASSES             #######################

def main():
    '''Main function.'''
    # comp_unit = 1
    # cycle_period = 1
    # node = MidSyncNodeC(comp_unit = comp_unit, cycle_period = cycle_period)
    # node.process_iterarion()

    master_db = DrvDbSqlEngineC(db_type = DrvDbTypeE.MASTER_DB, config_file='./mid_sync/.server_cred.yaml') #Remote database
    
    
    cache_db = DrvDbSqlEngineC(db_type = DrvDbTypeE.CACHE_DB,\
                                config_file='./mid_sync/.cache_cred.yaml')   #Local database
    fachade = MidSyncFachadeC(master_db = master_db, cache_db = cache_db)
    fachade.push_gen_meas()
    log.warning('Gen meas OK')
    # fachade.push_ext_meas()
    # log.warning('Ext meas OK')
    # fachade.update_experiments()
    # log.warning('Upd exp OK')
    # fachade.push_alarms()
    # log.warning('Alarms OK')
    # fachade.push_status()
    # log.warning('Status OK')
    # fachade.commit()
    # log.warning('Commit OK')

if __name__ == '__main__':
    main()
