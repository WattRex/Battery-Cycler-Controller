#!/usr/bin/python3
'''
_______________________________________________________________________________
'''

#######################        MANDATORY IMPORTS         #######################
from __future__ import annotations # pylint: disable=wrong-import-position
from sys import path
import os

#######################         GENERIC IMPORTS          #######################

#######################       THIRD PARTY IMPORTS        #######################
# from sqlalchemy import select, Table, Column, Integer, String, MetaData, ForeignKey, DateTime
from sqlalchemy import *

#######################      SYSTEM ABSTRACTION IMPORTS  #######################
path.append(os.getcwd())
from system_logger_tool import SysLogLoggerC, sys_log_logger_get_module_logger # pylint: disable=wrong-import-position
if __name__ == '__main__':
    cycler_logger = SysLogLoggerC(file_log_levels='./log_config.yaml')
log = sys_log_logger_get_module_logger(__name__)

#######################          PROJECT IMPORTS         #######################
from wattrex_driver_db import DrvDbSqlEngineC # pylint: disable=wrong-import-position
from wattrex_driver_db import *

#######################          MODULE IMPORTS          #######################

#######################              ENUMS               #######################

#######################              CLASSES             #######################
class MidSyncFachadeC():
    '''It is a thread that runs in background and is used to synchronize
    the database with the other nodes.
    '''
    def __init__(self, master_db: DrvDbSqlEngineC, cache_db: DrvDbSqlEngineC):
        log.info("Initializing DB Connection...")
        self._master_db: DrvDbSqlEngineC = master_db #Remote database
        self._cache_db:  DrvDbSqlEngineC = cache_db  #Local database
        self._pushed_gen_meas: list = []
        self._pushed_ext_meas: list = []
        self._pushed_status: list   = []
        self._pushed_alarms: list   = []

        # print('\nCONEXION:')
        # print(self._master_db) #TODO: Checkear conexion
        # print('------------------\n')


    def push_gen_meas(self) -> None:
        '''Push the measures to the database.
        Args:
            - None
        Returns:
            - None
        Raises:
            - None
        '''
        log.info("Pushing general measures...")
        stmt = select(DrvDbCacheGenericMeasureC)
        cache_meas  = self._cache_db.session.execute(stmt).all()
        self._pushed_gen_meas = []
        for meas in cache_meas:
            meas_add = DrvDbMasterGenericMeasureC()
            meas_add.transform(meas[0])
            self._master_db.session.add(meas_add)
            self._pushed_gen_meas.append(meas[0])
        self._master_db.commit_changes()

    def push_ext_meas(self) -> None:
        '''Push the measures to the database.
        Args:
            - None
        Returns:
            - None
        Raises:
            - None
        '''
        log.info("Pushing external measures...")
        stmt = select(DrvDbCacheExtendedMeasureC)
        cache_meas = self._cache_db.session.execute(stmt).all()
        self._pushed_ext_meas = []
        for meas in cache_meas:
            meas_add = DrvDbMasterExtendedMeasureC()
            meas_add.transform(meas[0])
            self._master_db.session.add(meas_add)
            self._pushed_ext_meas.append(meas[0])
        self._master_db.commit_changes()


    def push_alarms(self) -> None:
        '''Push the alarms to the database.
        Args:
            - None
        Returns:
            - None
        Raises:
            - None
        '''
        log.info("Pushing alarms...")
        stmt = select(DrvDbAlarmC)
        cache_meas = self._cache_db.session.execute(stmt).all()
        self._pushed_alarms = []
        for meas in cache_meas:
            self._cache_db.session.expunge(meas[0])
            self._master_db.session.merge(meas[0])
            self._pushed_alarms.append(meas[0])
        self._master_db.commit_changes()


    def push_status(self) -> None:
        '''Push the status to the database.
        Args:
            - None
        Returns:
            - None
        Raises:
            - None
        '''
        log.info("Pushing status...")
        stmt = select(DrvDbCacheStatusC)
        cache_meas = self._cache_db.session.execute(stmt).all()
        self._pushed_status = []
        for meas in cache_meas:
            self._cache_db.session.expunge(meas[0])
            self._master_db.session.merge(meas[0])
            self._pushed_status.append(meas[0])
        self._master_db.commit_changes()


    def update_experiments(self) -> None:
        '''Update the experiments on the database.
        Args:
            - None
        Returns:
            - None
        Raises:
            - None
        '''
        log.info("Updating experiment ID...") # pylint: disable=logging-fstring-interpolation

        stmt = select(DrvDbCacheExperimentC)
        exp_master_db = self._master_db.session.execute(stmt).all()
        self._pushed_exps = self._cache_db.session.execute(stmt).all()

        for row_master_db in exp_master_db:
            master: DrvDbCacheExperimentC = row_master_db[0]
            for pos, row_cache_db in enumerate(self._pushed_exps):
                if master.ExpID == self._pushed_exps[pos][0].ExpID:
                    self._pushed_exps[pos][0].Name          = master.Name
                    self._pushed_exps[pos][0].Description   = master.Description
                    self._pushed_exps[pos][0].CSID          = master.CSID
                    self._pushed_exps[pos][0].BatID         = master.BatID
                    self._pushed_exps[pos][0].ProfID        = master.ProfID


    def update_last_connection(self) -> None:
        ''' Update last connection
        Args:
            - None
        Returns:
            - None
        Raises:
            - None
        '''
        log.info("Updating last connection.")


    def commit(self) -> None:
        '''Confirm the changes made to the indicated database.
        Args:
            - None
        Returns:
            - None
        Raises:
            - None
        '''
        log.info("Commiting changes...")

        for meas in [self._pushed_alarms, self._pushed_status, self._pushed_ext_meas, self._pushed_gen_meas]:
            for m in meas:
                self._cache_db.session.delete(m)
            self._cache_db.commit_changes()

        self._pushed_gen_meas   = []
        self._pushed_ext_meas   = []
        self._pushed_status     = []
        self._pushed_alarms     = []


        # try:
        #     self._master_db.commit_changes()
        #     master_commit = True
        #     log.info("Commiting master changes done.")
        # except Exception as err: # pylint: disable=broad-except
        #     log.error(f"Error while commiting changes to DB: {err}") # pylint: disable=logging-fstring-interpolation
        #     master_commit = False

        # if master_commit:
        #     try:
        #         self._cache_db.commit_changes()
        #         log.info("Commiting cache changes done.")
        #         cache_commit = True
        #     except Exception as err: # pylint: disable=broad-except
        #         log.error(f"Error while commiting changes to DB: {err}") # pylint: disable=logging-fstring-interpolation
        #         cache_commit = False

        #     if cache_commit:
        #         try:
        #             self._cache_db.reset()
        #             log.info("Resetting cache done.")
        #         except Exception as err: # pylint: disable=broad-except
        #             log.error(f"Error while reseting cache: {err}") # pylint: disable=logging-fstring-interpolation