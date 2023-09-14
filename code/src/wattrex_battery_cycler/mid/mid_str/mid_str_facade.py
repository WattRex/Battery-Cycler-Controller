#!/usr/bin/python3
'''
Definition of MID STR Facade where database connection methods are defined.
'''
#######################        MANDATORY IMPORTS         #######################
from __future__ import annotations

#######################         GENERIC IMPORTS          #######################
from datetime import datetime
from typing import List

#######################       THIRD PARTY IMPORTS        #######################
from sqlalchemy import select, update, insert, join, text

#######################      SYSTEM ABSTRACTION IMPORTS  #######################
from system_logger_tool import sys_log_logger_get_module_logger
log = sys_log_logger_get_module_logger(__name__)

#######################          PROJECT IMPORTS         #######################
from wattrex_driver_db import DrvDbSqlEngineC, DrvDbMasterExperimentC, DrvDbBatteryC, DrvDbProfileC, \
                        DrvDbCyclerStationC, DrvDbInstructionC, DrvDbExpStatusE, DrvDbAlarmC, \
                        DrvDbCacheExtendedMeasureC, DrvDbCacheGenericMeasureC, DrvDbCacheStatusC,\
                        DrvDbTypeE, DrvDbUsedDeviceC, DrvDbCompatibleDeviceC

#######################          MODULE IMPORTS          #######################
from .mid_str_mapping import mapping_alarm, mapping_status, mapping_gen_meas,\
                            remap_dict, map_cs_db, map_dev_db
from ..mid_data import MidDataAlarmC, MidDataGenMeasC, MidDataExtMeasC, MidDataAllStatusC,\
                MidDataExpStatusE, MidDataProfileC, MidDataBatteryC, MidDataDeviceC,\
                MidDataExperimentC, MidDataCyclerStationC\

#######################              ENUMS               #######################
#
#
# getExpStatus
# getExpProfileData
# getExpBatteryData
# modifyCurrentExp
# writeNewAlarms
# writeGenericMeasures
# writeExtendedMeasures

#######################             CLASSES              #######################

class MidStrDbElementNotFoundErrorC(Exception):
    """Exception raised for errors when an input not found in the database.

    Attributes:
        message -- explanation of the error
    """
    def __init__(self, message):
        super().__init__(message)

class MidStrFacadeC:
    '''
    This class is used to interface with the database.
    '''
    def __init__(self, master_file : str = ".cred.yaml", cache_file : str = ".cred.yaml") -> None:
        log.info("Initializing DB Connection...")
        self.__master_db: DrvDbSqlEngineC = DrvDbSqlEngineC(db_type=DrvDbTypeE.MASTER_DB,
                                                            config_file= master_file)
        self.__cache_db: DrvDbSqlEngineC = DrvDbSqlEngineC(db_type=DrvDbTypeE.CACHE_DB,
                                                            config_file= cache_file)
        self.meas_id: int = 0

    def get_start_queued_exp(self, cycler_station_id) -> MidDataExperimentC:
        '''
        Get the oldest queued experiment, assigned to the cycler station where this 
        cycler would be running, and change its status to RUNNING in database.
        '''
        self.meas_id = 0
        exp = {}
        battery = {}
        profile = {}
        try:
            stmt =  select(DrvDbMasterExperimentC)\
                        .where(DrvDbMasterExperimentC.Status == DrvDbExpStatusE.QUEUED)\
                        .where(DrvDbMasterExperimentC.CSID == cycler_station_id)\
                        .order_by(DrvDbMasterExperimentC.DateCreation.asc())
            result = self.__master_db.session.execute(stm).first()
            if result is None:
                raise MidStrDbElementNotFoundErrorC(("No experiment found for cycler station "
                                                    f"with ID: {cycler_station_id}"))
            exp : DrvDbMasterExperimentC = result[0]
            # Get battery info
            stmt =  select(DrvDbBatteryC)\
                        .where(DrvDbBatteryC.BatID == exp.BatID)
            result = self.__master_db.session.execute(stm).first()
            if result is None:
                raise MidStrDbElementNotFoundErrorC(("No battery found with ID: {exp.BatID}"))
            battery = result[0]
            # Get profile info
            stmt =  select(DrvDbProfileC)\
                        .where(DrvDbProfileC.ProfID == exp.ProfID)
            result = self.__master_db.session.execute(stm).first()
            if result is None:
                raise MidStrDbElementNotFoundErrorC(("No profile found with ID: {exp.ProfID}"))
            profile = result[0]

            # Change experiment status to running and update begin datetime
            stmt = update(DrvDbCacheExperimentC).where(DrvDbCacheExperimentC.ExpID == exp.ExpID)\
                        .values(Status=DrvDbExpStatusE.RUNNING, DateBegin=datetime.utcnow())
            self.__cache_db.session.execute(stm)
        except Exception as err: #pylint: disable=broad-except
            # TODO: not catch own raised exceptions
            # print(err)
            # print("Error on GetQueuedExperimentById. Performing rollback...")
            # self.session.rollback()
            pass
        finally:
            return MidDataExperimentC(**exp.__dict__), MidDataBatteryC(**battery.__dict__),\
                        MidDataProfileC(**profile.__dict__)

    ## All methods that get information will gather the info from the master db
    def get_exp_status(self, exp_id: int) -> MidDataExpStatusE:
        """Returns the experiment status .
        Args:
            exp_id (int): [description]
        Returns:
            MidDataExpStatusE: [description]
        """
        stmt = select(DrvDbMasterExperimentC).where(DrvDbMasterExperimentC.ExpID == exp_id)
        result = self.__master_db.session.execute(stmt).one()[0]
        if result is None:
            raise MidStrDbElementNotFoundErrorC(f'Experiment with id {exp_id} not found')
        return MidDataExpStatusE(result.get("Status"))

    def get_exp_profile_data(self,exp_id: int) -> MidDataProfileC:
        """AI is creating summary for get_exp_profile_data
        Args:
            exp_id (int): [description]
        Returns:
            MidDataProfileC: [description]
        """
        stmt = select(DrvDbMasterExperimentC).where(DrvDbMasterExperimentC.ExpID == exp_id)
        result = self.__master_db.session.execute(stm).one()[0]
        if result is None:
            raise MidStrDbElementNotFoundErrorC(f'Experiment with id {exp_id} not found')
        return MidDataProfileC(**result.get("Profile"))

    def get_exp_battery_data(self, exp_id: int) -> MidDataBatteryC:
        """Get the mid - data of an experiment .
        Args:
            exp_id (int): [description]
        Returns:
            MidDataBatteryC: [description]
        """
        stmt = select(DrvDbMasterExperimentC).where(DrvDbMasterExperimentC.ExpID == exp_id)
        result = self.__master_db.session.execute(stmt).one()[0]
        if result is None:
            raise MidStrDbElementNotFoundErrorC(f'Experiment with id {exp_id} not found')
        return MidDataBatteryC(**result.get("Battery"))

    def get_cycler_station_info(self, exp_id: int) -> MidDataCyclerStationC:
        """Returns the name and name of the cycle station for the experiment .
        Returns:
            [type]: [description]
        """
        stmt = select(DrvDbMasterExperimentC).where(DrvDbMasterExperimentC.ExpID == exp_id)
        result = self.__master_db.session.execute(stmt).one()[0]
        if result is None:
            raise MidStrDbElementNotFoundErrorC(f'Experiment with id {exp_id} not found')
        log.debug(f"Experiment with id {exp_id} found, {result.__dict__}")
        stmt = select(DrvDbCyclerStationC).where(DrvDbCyclerStationC.CSID == result.CSID)
        result = self.__master_db.session.execute(stmt).one()[0]
        if result is None:
            raise MidStrDbElementNotFoundErrorC(f'Cycler station with id {result.CSID} not found')
        log.debug(f"Cycler station with id {result.CSID} found, {result.__dict__}")
        ## TODO: Check what is going to return exactly this function (ask Marius and Javi)
        cycler_station = MidDataCyclerStationC()
        for key,value in map_cs_db.items():
            setattr(cycler_station, value, result.__getattribute__(key))
        stmt = select(DrvDbUsedDeviceC, DrvDbCompatibleDeviceC).join(DrvDbCompatibleDeviceC,
            DrvDbUsedDeviceC.CompDevID == DrvDbCompatibleDeviceC.CompDevID).where(
                DrvDbUsedDeviceC.CSID == result.CSID)
        log.warning(f"Statement to execute, {stmt}")
        result = self.__master_db.session.execute(stmt).all()[0]
        devices= []
        log.critical(f"Devices found, {result[0].__dict__} - {result[1].__dict__}")
        for dev_res in result:
            log.debug(f"Device found, {dev_res.__dict__}")
            for key,value in map_dev_db.items():
                device = MidDataDeviceC()
                setattr(device, value, dev_res.__getattribute__(key))
            devices.append(device)
        log.critical(f"Cycler station object, {cycler_station.__dict__}")
        return cycler_station

    ## All methods that write information will write the info into the cache db
    def modify_current_exp(self, exp_status: MidDataExperimentC) -> None:
        """Modify the current experiment status .
        Args:
            exp_status (MidDataExpStatusE): [description]
        """
        stmt = update(DrvDbCacheExperimentC).where(DrvDbCacheExperimentC.ExpID == exp_status.exp_id).\
            values(Timestamp= datetime.now(), Status = exp_status.status)
        self.__cache_db.session.execute(stmt)

    def write_status_changes(self, all_status: MidDataAllStatusC) -> None:
        """Write the status changes into the cache db .
        Args:
            new_status (MidDataAllStatusC): [description]
        """
        stmt = update(DrvDbCacheStatusC).where(DrvDbCacheStatusC.ExpID == all_status.exp_id).\
            values(Timestamp= datetime.now(), **remap_dict(all_status.__dict__, mapping_status))
        self.__cache_db.session.execute(stmt)

    def write_new_alarm(self, alarms: List[MidDataAlarmC]) -> None:
        """Write an alarm into the cache db .
        Args:
            alarm (List[MidDataAlarmC]): [description]
        """
        for alarm in alarms:
            stmt = insert(DrvDbAlarmC).values(Timestamp= datetime.now(),
                                              **remap_dict(alarm.__dict__,mapping_alarm))
            self.__cache_db.session.execute(stmt)

    def write_generic_measures(self, gen_meas: MidDataGenMeasC) -> None:
        """Write the generic measures into the cache db .
        Args:
            gen_meas (MidDataGenMeasC): [description]
        """
        
        stmt = insert(DrvDbCacheGenericMeasureC).values(Timestamp= datetime.now(), MeasID= self.meas_id,
                                                **remap_dict(gen_meas.__dict__, mapping_gen_meas))
        self.__cache_db.session.execute(stmt)
        self.meas_id += 1

    def write_extended_measures(self, ext_meas: MidDataExtMeasC) -> None:
        """Write the extended measures into the cache db .
        Args:
            ext_meas (MidDataExtMeasC): [description]
        """
        if ext_meas__dict__.get("hs_voltage") is not None:
            stmt = insert(DrvDbCacheExtendedMeasureC).values(Timestamp= datetime.now(),
                                    MeasID= self.meas_id, Value= ext_meas.hs_voltage, MeasType= 0)
            self.__cache_db.session.execute(stmt)

    def commit_changes(self):
        """Commit changes made to the cache database.
        """
        self.__cache_db.commit_changes()

    def reset_db_connection(self):
        """Reset the connection to the both database.
        """
        # Closing connection to databases
        self.__cache_db.reset()
        self.__master_db.reset()

    def close_db_connection(self):
        """Close the connection to the both databases.
        """
        # Closing connection to databases
        self.__cache_db.close_connection()
        self.__master_db.close_connection()
