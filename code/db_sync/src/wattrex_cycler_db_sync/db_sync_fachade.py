#!/usr/bin/python3
'''
_______________________________________________________________________________
'''

#######################        MANDATORY IMPORTS         #######################
from __future__ import annotations # pylint: disable=wrong-import-position
from typing import Set
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
from wattrex_driver_db import (DrvDbSqlEngineC, DrvDbTypeE, DrvDbAlarmC, DrvDbCacheExperimentC, # pylint: disable=wrong-import-position
                DrvDbCacheStatusC, DrvDbCacheExtendedMeasureC, DrvDbCacheGenericMeasureC,
                DrvDbMasterGenericMeasureC, DrvDbMasterExtendedMeasureC, DrvDbExpStatusE,
                DrvDbMasterStatusC, DrvDbMasterExperimentC, transform_experiment_db,
                transform_ext_meas_db, transform_gen_meas_db, transform_status_db)
#######################          MODULE IMPORTS          #######################

#######################              ENUMS               #######################

#######################              CLASSES             #######################
class _SyncExpStatus():
    def __init__(self, status: DrvDbExpStatusE) -> None:
        self.status: DrvDbExpStatusE = status
        self.max_pushed_gen: int = -1

class DbSyncFachadeC(): # pylint: disable=too-many-instance-attributes
    '''It is a thread that runs in background and is used to synchronize
    the database with the other nodes.
    '''
    def __init__(self, cred_file:str):
        log.info("Initializing DB Connection...")
        #Remote database
        self.__master_db: DrvDbSqlEngineC = DrvDbSqlEngineC(db_type=DrvDbTypeE.MASTER_DB,
                                                            config_file= cred_file)
        #Local database
        self.__cache_db: DrvDbSqlEngineC = DrvDbSqlEngineC(db_type=DrvDbTypeE.CACHE_DB,
                                                            config_file= cred_file)
        self.__push_gen_meas: Set[DrvDbCacheGenericMeasureC]  = set()
        self.__push_ext_meas: Set[DrvDbCacheExtendedMeasureC]  = set()
        self.__push_status:   Set[DrvDbCacheStatusC] = set()
        self.__push_alarms:   Set[DrvDbAlarmC] = set()
        self.__push_exps:     Set[DrvDbCacheExperimentC]   = set()
        self.__exp_dict: dict[int, _SyncExpStatus] = {}


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
        for exp_id, exp_info in self.__exp_dict.items():
            cache_meas  = self.__cache_db.session.query(DrvDbCacheGenericMeasureC).\
                    filter(DrvDbCacheGenericMeasureC.ExpID == exp_id).\
                    order_by(DrvDbCacheGenericMeasureC.MeasID.asc()).all()

            log.debug(f"Exp {exp_id} has {len(cache_meas)} gen meas")
            if len(cache_meas) > 0:
                to_push_meas = set()
                log.debug(f"Last gen_meas in cache: {cache_meas[-1].MeasID}")
                if exp_info.status in (DrvDbExpStatusE.FINISHED.value,DrvDbExpStatusE.ERROR.value):
                    self.__exp_dict[exp_id].max_pushed_gen = cache_meas[-1].MeasID #pylint: disable= unnecessary-dict-index-lookup
                    to_push_meas = set(cache_meas)
                elif len(cache_meas)>1:
                    last_push_gen_meas = cache_meas[-2].MeasID
                    self.__exp_dict[exp_id].max_pushed_gen = max(last_push_gen_meas, #pylint: disable= unnecessary-dict-index-lookup
                                                                 exp_info.max_pushed_gen)
                    to_push_meas = set(cache_meas[:-1])
                log.debug(f"Last pushed gen_meas: {exp_info.max_pushed_gen}")

                for meas in to_push_meas:
                    meas_add = DrvDbMasterGenericMeasureC()
                    transform_gen_meas_db(source= meas, target= meas_add)
                    self.__push_gen_meas.add(meas)
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
        self.__cache_db.session.expire_all()
        log.info("Pushing external measures...")
        for exp_id, exp_info in self.__exp_dict.items():
            cache_meas = self.__cache_db.session.query(DrvDbCacheExtendedMeasureC).\
                populate_existing().filter(DrvDbCacheExtendedMeasureC.ExpID == exp_id,
                DrvDbCacheExtendedMeasureC.MeasID <= exp_info.max_pushed_gen).all()
            log.debug(f"Exp {exp_id} has {len(cache_meas)} ext meas")
            for meas in cache_meas:
                meas_add = DrvDbMasterExtendedMeasureC()
                transform_ext_meas_db(source= meas, target= meas_add)
                self.__push_ext_meas.add(meas)
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
        cache_meas = self.__cache_db.session.query(DrvDbAlarmC).all()
        for meas in cache_meas:
            self.__push_alarms.add(meas)
            self.__master_db.session.add(meas)


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
        cache_meas = self.__cache_db.session.query(DrvDbCacheStatusC).all()
        for meas in cache_meas:
            meas_add = DrvDbMasterStatusC()
            transform_status_db(source= meas, target= meas_add)
            self.__push_status.add(meas)
            self.__master_db.session.add(meas_add)

    def push_experiments(self) -> None:
        '''Push the experiments to the database.
        '''
        log.info("Pushing experiments...")
        cache_meas = self.__cache_db.session.query(DrvDbCacheExperimentC).populate_existing().all()
        for meas in cache_meas:
            meas_add = DrvDbMasterExperimentC()
            if (meas.ExpID not in self.__exp_dict or (meas.ExpID in self.__exp_dict
                and meas.Status != self.__exp_dict[meas.ExpID].status)):
                if meas.ExpID not in self.__exp_dict:
                    self.__exp_dict[meas.ExpID] = _SyncExpStatus(meas.Status)
                    if meas.Status in (DrvDbExpStatusE.FINISHED.value,DrvDbExpStatusE.ERROR.value):
                        self.__push_exps.add(meas)
                else:
                    self.__exp_dict[meas.ExpID].status = meas.Status
                    self.__push_exps.add(meas)

                log.debug(f"Experiment {meas.ExpID} status changed to {meas.Status}")
                transform_experiment_db(source= meas, target= meas_add)
                self.__master_db.session.merge(meas_add)

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
        self.__master_db.commit_changes(raise_exception= True)
        ## No rollback done in master db

    def delete_pushed_data(self):
        '''Remove the pushed data from the cache database.
        '''
        log.info("Deleting ...")
        for meas in [self.__push_alarms, self.__push_status,
                        self.__push_ext_meas, self.__push_gen_meas]:
            for row in meas:
                self.__cache_db.session.expunge(row)
                self.__cache_db.session.delete(row)
        self.__cache_db.commit_changes(raise_exception= True)

        for exp in self.__push_exps:
            log.debug(f"Deleting experiment {exp.ExpID}")
            self.__exp_dict.pop(exp.ExpID)
            self.__cache_db.session.expunge(exp)
            self.__cache_db.session.delete(exp)
        self.__cache_db.commit_changes(raise_exception= True)

        self.__push_gen_meas   = set()
        self.__push_ext_meas   = set()
        self.__push_status     = set()
        self.__push_alarms     = set()
        self.__push_exps       = set()
