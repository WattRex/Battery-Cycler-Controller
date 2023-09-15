#!/usr/bin/python3
## TODO: COMMENT CODE TO KNOW WHAT IS BEING DONE IN EACH FUNCTION
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
                        DrvDbTypeE, DrvDbUsedDeviceC, DrvDbCompatibleDeviceC, DrvDbDeviceTypeE

#######################          MODULE IMPORTS          #######################
from .mid_str_mapping import mapping_alarm, mapping_status, mapping_gen_meas, map_inst_db,\
                            remap_dict, map_cs_db, map_dev_db, map_batt_range_db, map_batt_db
from ..mid_data import MidDataAlarmC, MidDataGenMeasC, MidDataExtMeasC, MidDataAllStatusC,\
                MidDataExpStatusE, MidDataProfileC, MidDataBatteryC, MidDataDeviceC,\
                MidDataExperimentC, MidDataCyclerStationC, MidDataInstructionC\

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
        ## TODO: NOT WELL REVIEW, PROBABLY NOT WORKING AS EXPECTED, CHECK WHAT RETURNS EXACTLY
        self.meas_id = 0
        exp = {}
        battery = {}
        profile = {}
        try:
            stmt =  select(DrvDbMasterExperimentC)\
                        .where(DrvDbMasterExperimentC.Status == DrvDbExpStatusE.QUEUED)\
                        .where(DrvDbMasterExperimentC.CSID == cycler_station_id)\
                        .order_by(DrvDbMasterExperimentC.DateCreation.asc())
            result = self.__master_db.session.execute(stmt).first()
            if result is None:
                raise MidStrDbElementNotFoundErrorC(("No experiment found for cycler station "
                                                    f"with ID: {cycler_station_id}"))
            exp : DrvDbMasterExperimentC = result[0]
            # Get battery info
            stmt =  select(DrvDbBatteryC)\
                        .where(DrvDbBatteryC.BatID == exp.BatID)
            result = self.__master_db.session.execute(stmt).first()
            if result is None:
                raise MidStrDbElementNotFoundErrorC(("No battery found with ID: {exp.BatID}"))
            battery = result[0]
            # Get profile info
            stmt =  select(DrvDbProfileC)\
                        .where(DrvDbProfileC.ProfID == exp.ProfID)
            result = self.__master_db.session.execute(stmt).first()
            if result is None:
                raise MidStrDbElementNotFoundErrorC(("No profile found with ID: {exp.ProfID}"))
            profile = result[0]

            # Change experiment status to running and update begin datetime
            stmt = update(DrvDbCacheExperimentC).where(DrvDbCacheExperimentC.ExpID == exp.ExpID)\
                        .values(Status=DrvDbExpStatusE.RUNNING, DateBegin=datetime.utcnow())
            self.__cache_db.session.execute(stmt)
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
        return MidDataExpStatusE(result.Status.value)

    def get_exp_profile_data(self,exp_id: int) -> MidDataProfileC:
        """AI is creating summary for get_exp_profile_data
        Args:
            exp_id (int): [description]
        Returns:
            MidDataProfileC: [description]
        """
        stmt = select(DrvDbMasterExperimentC).where(DrvDbMasterExperimentC.ExpID == exp_id)
        result = self.__master_db.session.execute(stmt).one()[0]
        if result is None:
            raise MidStrDbElementNotFoundErrorC(f'Experiment with id {exp_id} not found')
        stmt = select(DrvDbProfileC).where(DrvDbProfileC.ProfID == result.ProfID)
        result = self.__master_db.session.execute(stmt).one()[0]
        if result is None:
            raise MidStrDbElementNotFoundErrorC(f'Profile with id {result.ProfID} not found')
        profile = MidDataProfileC(name= result.Name)
        instructions= []
        stmt = select(DrvDbInstructionC).where(DrvDbInstructionC.ProfID == result.ProfID)
        result = self.__master_db.session.execute(stmt).all()[0]
        if result is None:
            raise MidStrDbElementNotFoundErrorC((f'Instructions for profile {result.ProfID} '
                                                 'not found'))
        for inst_res in result:
            instruction = MidDataInstructionC()
            for db_name, att_name in map_inst_db.items():
                setattr(instruction, att_name, getattr(inst_res,db_name))
            instructions.append(instruction)
        profile.instructions = instructions
        return profile

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
        battery = MidDataBatteryC()
        for db_name, att_name in map_batt_db.items():
            setattr(battery, att_name, getattr(result,db_name))
        bat_range = MidDataPwrRangeC()
        for db_name, att_name in map_batt_range_db.items():
            setattr(bat_range, att_name, getattr(result,db_name))
        battery.elec_ranges = bat_range
        return battery

    def get_cycler_station_info(self, cycler_id: int) -> MidDataCyclerStationC:
        """Returns the name and name of the cycle station for the experiment .
        Returns:
            [MidDataCyclerStationC]: [description]
        """
        ## Get cycler station info
        stmt = select(DrvDbCyclerStationC).where(DrvDbCyclerStationC.CSID == cycler_id)
        result = self.__master_db.session.execute(stmt).one()[0]
        if result is None:
            raise MidStrDbElementNotFoundErrorC(f'Cycler station with id {cycler_id} not found')
        log.debug(f"Cycler station with id {cycler_id} found, {result.__dict__}")
        cycler_station = MidDataCyclerStationC()
        for key,value in map_cs_db.items():
            setattr(cycler_station, value, getattr(result,key))
        ## Get devices used in the cycler station
        stmt = select(DrvDbUsedDeviceC, DrvDbCompatibleDeviceC).join(DrvDbCompatibleDeviceC,
            DrvDbUsedDeviceC.CompDevID == DrvDbCompatibleDeviceC.CompDevID).where(
                DrvDbUsedDeviceC.CSID == result.CSID)
        result = self.__master_db.session.execute(stmt).all()[0]
        devices= []
        for dev_res in result:
            log.debug(f"Device found, {dev_res.__dict__}")
            device = MidDataDeviceC()
            for db_name, att_name in map_dev_db.items():
                setattr(device, att_name, getattr(dev_res,db_name))
            if dev_res.DeviceType is not DrvDbDeviceTypeE.EPC:
                ## Get link configuration if needed
                stmt = select(DrvDbLinkConfC).where(DrvDbLinkConfC.CompDevID == dev_res.CompDevID)
                result = self.__master_db.session.execute(stmt).all()[0]
                if result is None:
                    raise MidStrDbElementNotFoundErrorC((f'Link configuration for device '
                                                        f'{dev_res.CompDevID} not found'))
                link_conf = MidDataLinkConfC()
                for db_name, att_name in map_link_conf_db.items():
                    setattr(link_conf, att_name, getattr(result,db_name))
                device.link_conf = link_conf            
            devices.append(device)
        log.critical(f"Cycler station object, {cycler_station.__dict__}")
        cycler_station.devices= devices
        return cycler_station

    ## All methods that write information will write the info into the cache db
    def modify_current_exp(self, exp_status: MidDataExpStatusE, exp_id: int) -> None:
        """Modify the current experiment status .
        Args:
            exp_status (MidDataExpStatusE): [description]
        """
        stmt = update(DrvDbCacheExperimentC).where(DrvDbCacheExperimentC.ExpID == exp_id).\
            values(Timestamp= datetime.now(), Status = exp_status)
        self.__cache_db.session.execute(stmt)

    def write_status_changes(self, all_status: MidDataAllStatusC, exp_id: int) -> None:
        """Write the status changes into the cache db .
        Args:
            new_status (MidDataAllStatusC): [description]
        """
        stmt = update(DrvDbCacheStatusC).where(DrvDbCacheStatusC.ExpID == exp_id).\
            values(Timestamp= datetime.now(), **remap_dict(all_status.__dict__, mapping_status))
        self.__cache_db.session.execute(stmt)

    def write_new_alarm(self, alarms: List[MidDataAlarmC], exp_id: int) -> None:
        """Write an alarm into the cache db .
        Args:
            alarm (List[MidDataAlarmC]): [description]
        """
        for alarm in alarms:
            stmt = insert(DrvDbAlarmC).values(Timestamp= datetime.now(), ExpID = exp_id,
                                              **remap_dict(alarm.__dict__,mapping_alarm))
            self.__cache_db.session.execute(stmt)

    def write_generic_measures(self, gen_meas: MidDataGenMeasC, exp_id: int) -> None:
        """Write the generic measures into the cache db .
        Args:
            gen_meas (MidDataGenMeasC): [description]
        """
        
        stmt = insert(DrvDbCacheGenericMeasureC).values(Timestamp= datetime.now(), ExpID = exp_id,
                        MeasID= self.meas_id, **remap_dict(gen_meas.__dict__, mapping_gen_meas))
        self.__cache_db.session.execute(stmt)
        self.meas_id += 1

    def write_extended_measures(self, ext_meas: MidDataExtMeasC, exp_id: int) -> None:
        """Write the extended measures into the cache db .
        Args:
            ext_meas (MidDataExtMeasC): [description]
        """
        try:
            stmt = insert(DrvDbCacheExtendedMeasureC).values(Timestamp= datetime.now(), MeasType= 0,
                        MeasID= self.meas_id, Value= ext_meas.hs_current, ExpID= exp_id)
            self.__cache_db.session.execute(stmt)
        except AttributeError:
            log.error("Could not write extended measures into the cache db")

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
