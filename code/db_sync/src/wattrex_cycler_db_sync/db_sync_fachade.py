#!/usr/bin/python3
'''
_______________________________________________________________________________
'''

#######################        MANDATORY IMPORTS         #######################
from __future__ import annotations # pylint: disable=wrong-import-position
from typing import List
from sys import path
import os

#######################         GENERIC IMPORTS          #######################

#######################       THIRD PARTY IMPORTS        #######################
from sqlalchemy import select, Table, Column, Integer, String, MetaData, ForeignKey, DateTime

#######################      SYSTEM ABSTRACTION IMPORTS  #######################
path.append(os.getcwd())
from system_logger_tool import SysLogLoggerC, sys_log_logger_get_module_logger # pylint: disable=wrong-import-position
if __name__ == '__main__':
    cycler_logger = SysLogLoggerC(file_log_levels='./log_config.yaml')
log = sys_log_logger_get_module_logger(__name__)

#######################          PROJECT IMPORTS         #######################
from wattrex_driver_db import (DrvDbSqlEngineC, DrvDbTypeE, DrvDbAlarmC, DrvDbCacheExperimentC, # pylint: disable=wrong-import-position
                DrvDbCacheStatusC, DrvDbCacheExtendedMeasureC, DrvDbCacheGenericMeasureC,
                DrvDbAlarmC, DrvDbMasterGenericMeasureC, DrvDbMasterExtendedMeasureC,
                DrvDbMasterStatusC, DrvDbMasterExperimentC, transform_experiment_db,
                transform_ext_meas_db, transform_gen_meas_db, transform_status_db)
#######################          MODULE IMPORTS          #######################

#######################              ENUMS               #######################

#######################              CLASSES             #######################

class DbSyncFachadeC():
    '''It is a thread that runs in background and is used to synchronize
    the database with the other nodes.
    '''
    # def __init__(self, master_db: DrvDbSqlEngineC, cache_db: DrvDbSqlEngineC):
    def __init__(self, cred_file:str):
        log.info("Initializing DB Connection...")
        #Remote database
        self.__master_db: DrvDbSqlEngineC = DrvDbSqlEngineC(db_type=DrvDbTypeE.MASTER_DB,
                                                            config_file= cred_file)
        #Local database
        self.__cache_db: DrvDbSqlEngineC = DrvDbSqlEngineC(db_type=DrvDbTypeE.CACHE_DB,
                                                            config_file= cred_file)
        self.__push_gen_meas: List[DrvDbCacheGenericMeasureC]  = []
        self.__push_ext_meas: List[DrvDbCacheExtendedMeasureC]  = []
        self.__push_status:   List[DrvDbCacheStatusC] = []
        self.__push_alarms:   List[DrvDbAlarmC] = []
        self.__push_exps:     List[DrvDbCacheExperimentC]   = []

        # print('\nCONEXION:')
        # print(self.__master_db) #TODO: Checkear conexion
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
        stmt = select(DrvDbCacheGenericMeasureC).limit(100)
        cache_meas  = self.__cache_db.session.execute(stmt).all()
        for meas in cache_meas:
            meas_add = DrvDbMasterGenericMeasureC()
            transform_gen_meas_db(source= meas[0], target= meas_add)
            self.__push_gen_meas.append(meas[0])
            self.__master_db.session.add(meas_add)

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
        stmt = select(DrvDbCacheExtendedMeasureC).limit(100)
        cache_meas = self.__cache_db.session.execute(stmt).all()
        for meas in cache_meas:
            meas_add = DrvDbMasterExtendedMeasureC()
            transform_ext_meas_db(source= meas[0], target= meas_add)
            self.__push_ext_meas.append(meas[0])
            self.__master_db.session.add(meas_add)

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
        stmt = select(DrvDbAlarmC).limit(100)
        cache_meas = self.__cache_db.session.execute(stmt).all()
        for meas in cache_meas:
            # self.__cache_db.session.expunge(meas[0])
            self.__push_alarms.append(meas[0])
            self.__master_db.session.merge(meas[0])


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
        stmt = select(DrvDbCacheStatusC).limit(100)
        cache_meas = self.__cache_db.session.execute(stmt).all()
        for meas in cache_meas:
            meas_add = DrvDbMasterStatusC()
            transform_status_db(source= meas[0], target= meas_add)
            # self.__cache_db.session.expunge(meas[0])
            self.__push_status.append(meas[0])
            self.__master_db.session.merge(meas[0])
        # self.__master_db.commit_changes()
    
    def push_experiments(self) -> None:
        '''Push the experiments to the database.
        '''
        log.info("Pushing experiments...")
        stmt = select(DrvDbCacheExperimentC).limit(100)
        cache_meas = self.__cache_db.session.execute(stmt).all()
        for meas in cache_meas:
            meas_add = DrvDbMasterExperimentC()
            transform_experiment_db(source= meas[0], target= meas_add)
            # self.__cache_db.session.expunge(meas[0])
            self.__push_exps.append(meas[0])
            self.__master_db.session.merge(meas_add)


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
        try:
            self.__master_db.commit_changes(raise_exception= True)
            ## No rollback done in master db
            for meas in [self.__push_alarms, self.__push_status,
                        self.__push_ext_meas, self.__push_gen_meas]:
                for row in meas:
                    self.__cache_db.session.delete(row)
                self.__cache_db.commit_changes()

            self.__push_gen_meas   = []
            self.__push_ext_meas   = []
            self.__push_status     = []
            self.__push_alarms     = []
            self.__push_exps       = []
        except Exception as err:
            log.error("Error commiting changes: %s", err)
