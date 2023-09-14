#!/usr/bin/python3
'''
_______________________________________________________________________________
'''

#######################        MANDATORY IMPORTS         #######################
from sys import path
import os

#######################         GENERIC IMPORTS          #######################
import threading

#######################       THIRD PARTY IMPORTS        #######################

#######################      SYSTEM ABSTRACTION IMPORTS  #######################
path.append(os.getcwd())
from system_logger_tool import SysLogLoggerC, sys_log_logger_get_module_logger # pylint: disable=wrong-import-position
if __name__ == '__main__':
    cycler_logger = SysLogLoggerC(file_log_levels='./log_config.yaml')
log = sys_log_logger_get_module_logger(__name__)
from system_shared_tool import SysShdSharedObjC, SysShdChanC # pylint: disable=wrong-import-position

#######################          PROJECT IMPORTS         #######################
from wattrex_driver_db import DrvDbSqlEngineC 

#######################          MODULE IMPORTS          #######################
from mid_sync import MidSyncFachadeC # pylint: disable=wrong-import-position

#######################              ENUMS               #######################


#######################              CLASSES             #######################
class MidSyncNodeC(SysShdNodeC):
    '''
    It is a thread that runs in background and is used to synchronize
    the database with the other nodes.
    '''
    def __init__(self, comp_unit: int, cycle_period: int):
        '''Initialize the class.
        Args:
            - comp_unit (int): _____________
            - cycle_period (int): period of the cycler station.
        Returns:
            - None
        Raises:
            - None
        '''
        log.info(f"Initializing {comp_unit} node...") # pylint: disable=logging-fstring-interpolation
        master_db = DrvDbSqlEngineC(config_file='./mid_sync/.server_cred.yaml') #Remote database
        cache_db = DrvDbSqlEngineC(config_file='./mid_sync/.cache_cred.yaml')   #Local database

        self.comp_unit: int = comp_unit
        self.fachade: MidSyncFachadeC = MidSyncFachadeC(master_db = master_db, cache_db = cache_db)
        self.working_flag: threading.Event = None
        self.cycle_period: int = cycle_period


    def process_iterarion(self) -> None:
        '''Process the iteration.
        Args:
            - None
        Returns:
            - None
        Raises:
            - None
        '''
        log.info(f"Processing iteration for experiment ID: {self.current_exp_id} ...") # pylint: disable=logging-fstring-interpolation
        self.fachade.push_gen_meas()
        self.fachade.push_ext_meas()
        self.fachade.update_experiments()
        self.fachade.push_alarms()
        self.fachade.push_status()
        self.fachade.commit()
