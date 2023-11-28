#!/usr/bin/python3
'''
Class that sync between the cache and the master database.
'''

#######################        MANDATORY IMPORTS         #######################
from sys import path
import os

#######################         GENERIC IMPORTS          #######################
from threading import Event

#######################       THIRD PARTY IMPORTS        #######################

#######################      SYSTEM ABSTRACTION IMPORTS  #######################
path.append(os.getcwd())
from system_logger_tool import Logger, sys_log_logger_get_module_logger # pylint: disable=wrong-import-position
log:Logger = sys_log_logger_get_module_logger(__name__)

from system_shared_tool import SysShdNodeC # pylint: disable=wrong-import-position

#######################          PROJECT IMPORTS         #######################

#######################          MODULE IMPORTS          #######################
from .context import (DEFAULT_CRED_FILEPATH, DEFAULT_SYNC_NODE_NAME, DEFAULT_NODE_PERIOD,
                      DEFAULT_COMP_UNIT)
from .db_sync_fachade import DbSyncFachadeC # pylint: disable=wrong-import-position

#######################              ENUMS               #######################


#######################              CLASSES             #######################
class DbSyncNodeC(SysShdNodeC): #pylint: disable= abstract-method
    '''
    It is a thread that runs in background and is used to synchronize
    the database with the other nodes.
    '''
    def __init__(self, working_flag: Event, comp_unit: int= DEFAULT_COMP_UNIT,
                 cycle_period: int= DEFAULT_NODE_PERIOD,
                 cred_file: str = DEFAULT_CRED_FILEPATH):
        '''Initialize the class.
        Args:
            - comp_unit (int): number of the computational unit.
            - cycle_period (int): period of the sync.
        Returns:
            - None
        Raises:
            - None
        '''
        log.info(f"Initializing {comp_unit} node...") # pylint: disable=logging-fstring-interpolation
        super().__init__(name= DEFAULT_SYNC_NODE_NAME, cycle_period=cycle_period,
                         working_flag= working_flag)
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
        log.critical(f"Stopping {self.name} in CU {self.comp_unit}...")
        self.working_flag.clear()

    def process_iteration(self) -> None:
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
        try:
            self.fachade.commit()
            log.debug("Commit and push of gen and exp done")
            self.fachade.push_ext_meas()
            self.fachade.push_alarms()
            self.fachade.push_status()
            self.fachade.commit()
            log.debug("Commit and push ext, alarms and status done")
            self.fachade.delete_pushed_data()
        except Exception as err:
            log.error((f"Error in trying to commit to master or cache, doing rollback: {err}"))
