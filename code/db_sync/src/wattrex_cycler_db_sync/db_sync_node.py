#!/usr/bin/python3
'''
_______________________________________________________________________________
'''

#######################        MANDATORY IMPORTS         #######################
from sys import path
import os

#######################         GENERIC IMPORTS          #######################
from threading import Event

#######################       THIRD PARTY IMPORTS        #######################

#######################      SYSTEM ABSTRACTION IMPORTS  #######################
path.append(os.getcwd())
from system_logger_tool import SysLogLoggerC, sys_log_logger_get_module_logger # pylint: disable=wrong-import-position
if __name__ == '__main__':
    cycler_logger = SysLogLoggerC(file_log_levels='./log_config.yaml')
log = sys_log_logger_get_module_logger(__name__)
from system_shared_tool import SysShdNodeC # pylint: disable=wrong-import-position

#######################          PROJECT IMPORTS         #######################
from wattrex_driver_db import * 

#######################          MODULE IMPORTS          #######################
from .context import DEFAULT_CRED_FILE
from .db_sync_fachade import DbSyncFachadeC # pylint: disable=wrong-import-position

#######################              ENUMS               #######################


#######################              CLASSES             #######################
class DbSyncNodeC(SysShdNodeC): #TODO: No reconode el SysShdNodeC
    '''
    It is a thread that runs in background and is used to synchronize
    the database with the other nodes.
    '''
    def __init__(self, working_flag: Event, comp_unit: int, cycle_period: int,
                 cred_file: str = DEFAULT_CRED_FILE):
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
        super().__init__(name= "Sync_Node", cycle_period=cycle_period, working_flag= working_flag)
        self.comp_unit: int = comp_unit
        self.fachade: DbSyncFachadeC = DbSyncFachadeC(cred_file= cred_file)

    def stop(self) -> None:
        '''Stop the thread.
        Args:
            - None
        Returns:
            - None
        Raises:
            - None
        '''
        log.info(f"Stopping {self.name} in CU {self.comp_unit}...")
        self.working_flag.clear()

    def process_iterarion(self) -> None:
        '''Process the iteration.
        Args:
            - None
        Returns:
            - None
        Raises:
            - None
        '''
        log.info("Processing iteration for experiment...") # pylint: disable=logging-fstring-interpolation
        self.fachade.push_experiments()
        self.fachade.push_gen_meas()
        self.fachade.push_ext_meas()
        self.fachade.push_alarms()
        self.fachade.push_status()
        self.fachade.commit()
        self.fachade.update_last_connection()
