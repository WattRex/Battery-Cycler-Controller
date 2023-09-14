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
        self._pushed_gen_meas: DrvDbGenericMeasureC     = None
        self._pushed_ext_meas: DrvDbExtendedMeasureC    = None
        self._pushed_status: DrvDbStatusC               = None
        self._pushed_alarms: DrvDbAlarmC                = None
        self._pushed_exps: DrvDbExperimentC             = None
        self._id_gen_meas: int = None

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
        stmt = select([func.max(DrvDbGenericMeasureC.__dict__['ExpID']).label('numero_mas_alto')])
        self._id_gen_meas = self._cache_db.session.execute(stmt).all()[0][0]
        stmt = select(DrvDbGenericMeasureC)
        self._pushed_gen_meas = self._cache_db.session.execute(stmt).all()


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
        stmt = select(DrvDbExtendedMeasureC).where(DrvDbExtendedMeasureC.__dict__['ExpID'] <= self._id_gen_meas)
        self._pushed_ext_meas = self._cache_db.session.execute(stmt).all()


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
        self._pushed_alarms = self._cache_db.session.execute(stmt).all()


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
        stmt = select(DrvDbStatusC)
        self._pushed_status = self._cache_db.session.execute(stmt).all()


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

        stmt = select(DrvDbExperimentC)
        exp_master_db = self._master_db.session.execute(stmt).all()
        self._pushed_exps = self._cache_db.session.execute(stmt).all()

        for row_master_db in exp_master_db:
            master: DrvDbExperimentC = row_master_db[0]
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


    def _delete_pushed_data(self) -> None:
        ''' Deleting sent data
        Args:
            - None
        Returns:
            - None
        Raises:
            - None
        '''
        log.info("Deleting sent data.")
        self._pushed_gen_meas   = None
        self._pushed_ext_meas   = None
        self._pushed_status     = None
        self._pushed_alarms     = None
        self._pushed_exps       = None
        self._id_gen_meas       = None


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

        self._add_db(self._pushed_exps)     #ADD EXPERIMENTS
        self._add_db(self._pushed_gen_meas) #ADD GENERIC MEAS
        self._add_db(self._pushed_ext_meas) #ADD EXTEND MEAS
        self._add_db(self._pushed_alarms)   #ADD ALARMS
        self._add_db(self._pushed_status)   #ADD STATUS
        self._master_db.commit_changes()
        self._delete_pushed_data()


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


    def _add_db(self, dates: list) -> None:
        if isinstance(dates, list):
            for row in dates:
                self._cache_db.session.expunge(row[0])
                self._master_db.session.merge(row[0])
