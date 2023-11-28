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
        self.max_gen_meas: int = -1
        self.max_ext_meas: int = -1


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
        self.__push_gen_meas: List[DrvDbCacheGenericMeasureC]  = []
        self.__push_ext_meas: List[DrvDbCacheExtendedMeasureC]  = []
        self.__push_status:   List[DrvDbCacheStatusC] = []
        self.__push_alarms:   List[DrvDbAlarmC] = []
        self.__push_exps:     List[DrvDbCacheExperimentC]   = []
        # self.__last_exp_status: dict[int, [DrvDbExpStatusE, int, int]] ={}
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
                    filter(DrvDbCacheGenericMeasureC.ExpID == exp_id,
                    DrvDbCacheGenericMeasureC.MeasID > exp_info.max_gen_meas).all()
            max_id = -1
            log.warning(f"Exp {exp_id} has {len(cache_meas)} gen meas")
            for meas in cache_meas:
                if meas not in self.__push_gen_meas:
                    if meas.MeasID > max_id:
                        max_id = meas.MeasID
                    meas_add = DrvDbMasterGenericMeasureC()
                    transform_gen_meas_db(source= meas, target= meas_add)
                    self.__push_gen_meas.append(meas)
                    self.__master_db.session.add(meas_add)
            if max_id > exp_info.max_gen_meas or max_id == -1:
                log.warning(f"Modificando el valor de max_gen_meas de {exp_info.max_gen_meas} a {max_id}")
                self.__exp_dict[exp_id].max_gen_meas = max_id



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
                filter(DrvDbCacheExtendedMeasureC.ExpID<= exp_id,
                DrvDbCacheExtendedMeasureC.MeasID <= exp_info.max_gen_meas,
                DrvDbCacheGenericMeasureC.MeasID >exp_info.max_ext_meas).\
                order_by(DrvDbCacheExtendedMeasureC.MeasID).all()
            max_id = -1
            log.warning(f"Exp {exp_id} has {len(cache_meas)} ext meas")
            for meas in cache_meas:
                if meas not in self.__push_ext_meas:
                    if meas.MeasID > max_id:
                        max_id = meas.MeasID
                    meas_add = DrvDbMasterExtendedMeasureC()
                    transform_ext_meas_db(source= meas, target= meas_add)
                    self.__push_ext_meas.append(meas)
                    self.__master_db.session.add(meas_add)
            if max_id > exp_info.max_ext_meas or max_id == -1:
                log.warning(f"Modificando el valor de max_ext_meas de {exp_info.max_ext_meas} a {max_id}")
                self.__exp_dict[exp_id].max_ext_meas = max_id

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
            if meas not in self.__push_alarms:
                self.__push_alarms.append(meas)
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
            if meas not in self.__push_status:
                meas_add = DrvDbMasterStatusC()
                transform_status_db(source= meas, target= meas_add)
                self.__push_status.append(meas)
                self.__master_db.session.add(meas_add)

    def push_experiments(self) -> None:
        '''Push the experiments to the database.
        '''
        log.info("Pushing experiments...")
        cache_meas = self.__cache_db.session.query(DrvDbCacheExperimentC).all()
        for meas in cache_meas:
            meas_add = DrvDbMasterExperimentC()
            # if (meas.ExpID not in self.__last_exp_status or (meas.ExpID in self.__last_exp_status
            #     and meas.Status != self.__last_exp_status[meas.ExpID])):
            if (meas.ExpID not in self.__exp_dict or (meas.ExpID in self.__exp_dict
                and meas.Status != self.__exp_dict[meas.ExpID].status)):
                if meas.ExpID not in self.__exp_dict:
                    self.__exp_dict[meas.ExpID] = _SyncExpStatus(meas.Status)
                else:
                    self.__exp_dict[meas.ExpID].status = meas.Status
                log.info(f"Experiment {meas.ExpID} status changed to {meas.Status}")
                transform_experiment_db(source= meas, target= meas_add)
                self.__push_exps.append(meas)
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
        for meas,name in zip([self.__push_alarms, self.__push_status,
                        self.__push_ext_meas, self.__push_gen_meas, self.__push_exps],
                        ['alarms', 'status', 'ext_meas', 'gen_meas', 'exps']):
            for row in meas:
                if name == 'exps':
                    log.error(f"Exp {row.ExpID} is {row.Status}, ext meas: {self.__exp_dict[row.ExpID].max_ext_meas}, gen meas: {self.__exp_dict[row.ExpID].max_gen_meas}")
                    if (row.Status in (DrvDbExpStatusE.FINISHED.value, DrvDbExpStatusE.ERROR.value)
                        and self.__exp_dict[row.ExpID].max_gen_meas == -1):
                        log.critical(f"Removing exp {row.ExpID} from cache")
                        # self.__last_exp_status.pop(row.ExpID)
                        self.__exp_dict.pop(row.ExpID)
                        self.__cache_db.session.expunge(row)
                        self.__cache_db.session.delete(row)

                elif name == 'gen_meas':
                    log.warning(f"Removing gen meas {row.MeasID}, from exp {row.ExpID}, is below {self.__exp_dict[row.ExpID].max_ext_meas}")
                    if (row.MeasID < self.__exp_dict[row.ExpID].max_ext_meas or
                        self.__exp_dict[row.ExpID].max_ext_meas == -1):
                        self.__cache_db.session.expunge(row)
                        self.__cache_db.session.delete(row)
                        # meas.remove(row)
                else:
                    self.__cache_db.session.expunge(row)
                    self.__cache_db.session.delete(row)
                    # meas.remove(row)
            log.info(f"Deleting {name}...")
            self.__cache_db.commit_changes(raise_exception= True)

        self.__push_gen_meas   = []
        self.__push_ext_meas   = []
        self.__push_status     = []
        self.__push_alarms     = []
        self.__push_exps       = []
