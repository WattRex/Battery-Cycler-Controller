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
from sqlalchemy import select, update, insert

#######################      SYSTEM ABSTRACTION IMPORTS  #######################
from system_logger_tool import sys_log_logger_get_module_logger
log = sys_log_logger_get_module_logger(__name__)

#######################          PROJECT IMPORTS         #######################
from wattrex_driver_db import (DrvDbSqlEngineC, DrvDbMasterExperimentC, DrvDbBatteryC, 
        DrvDbProfileC, DrvDbCyclerStationC, DrvDbInstructionC, DrvDbExpStatusE, DrvDbAlarmC,
        DrvDbCacheExtendedMeasureC, DrvDbCacheGenericMeasureC, DrvDbCacheStatusC, DrvDbTypeE,
        DrvDbUsedDeviceC, DrvDbCompatibleDeviceC, DrvDbDeviceTypeE, DrvDbLinkConfigurationC,
        DrvDbCacheExperimentC)

#######################          MODULE IMPORTS          #######################
from .mid_str_mapping import (mapping_alarm, mapping_status, mapping_gen_meas, map_inst_db,
        map_cs_db, map_dev_db, map_batt_range_db, map_batt_db, mapping_experiment, map_instr_modes,
        map_instr_limit_modes, remap_dict)
from ..mid_data import (MidDataAlarmC, MidDataGenMeasC, MidDataExtMeasC, MidDataAllStatusC,
            MidDataExpStatusE, MidDataProfileC, MidDataBatteryC, MidDataDeviceC, MidDataDeviceTypeE,
            MidDataExperimentC, MidDataCyclerStationC, MidDataInstructionC, MidDataPwrRangeC,
            MidDataPwrModeE, MidDataPwrLimitE)

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

    def get_start_queued_exp(self, cycler_station_id: int) -> MidDataExperimentC:
        '''
        Get the oldest queued experiment, assigned to the cycler station where this 
        cycler would be running, and change its status to RUNNING in database.
        '''
        ## TODO: NOT WELL REVIEW, PROBABLY NOT WORKING AS EXPECTED, CHECK WHAT RETURNS EXACTLY
        self.meas_id = 0
        exp = None
        battery = None
        profile = None
        try:
            stmt =  select(DrvDbMasterExperimentC)\
                        .where(DrvDbMasterExperimentC.Status == DrvDbExpStatusE.QUEUED.value)\
                        .where(DrvDbMasterExperimentC.CSID == cycler_station_id)\
                        .order_by(DrvDbMasterExperimentC.DateCreation.asc())
            exp_result = self.__master_db.session.execute(stmt).first()[0]
            if exp_result is None:
                raise MidStrDbElementNotFoundErrorC(("No experiment found for cycler station "
                                                    f"with ID: {cycler_station_id}"))
            exp : MidDataExperimentC = MidDataExperimentC()
            for db_name, att_name in mapping_experiment.items():
                setattr(exp, att_name, getattr(exp_result,db_name))

            # Get battery info
            battery = self.get_exp_battery_data(exp.exp_id)
            # Get profile info
            profile = self.get_exp_profile_data(exp.exp_id)
            try:
                # Change experiment status to running and update begin datetime
                # log.debug(exp_result_dict)
                # exp_dict= {'ExpID': exp.exp_id, 'CSID': cycler_station_id, 'Name': exp.name,
                #     'BatID': exp_result.BatID, 'ProfID': exp_result.ProfID,
                #     'Description': exp_result.Description, 'Status': DrvDbExpStatusE.RUNNING.value,
                #     'DateBegin': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                #     'DateCreation': exp_result.DateCreation}
                exp_dict= {'ExpID': 1, 'CSID': 1, 'Name': 'Pruebas 1', 'BatID': 2, 'ProfID': 1,
               'Description': 'Pruebas manager1', 'Status': 'RUNNING',
               'DateBegin': '2023-09-27 10:18:38',
               'DateCreation': datetime(2023, 9, 20, 14, 0, 9)}
                a = DrvDbCacheExperimentC(**exp_dict)
                self.__cache_db.session.add(a)
                log.critical(f"DEBUG COMMIT {a.__dict__}")
                # stmt = insert(DrvDbCacheExperimentC).values(ExpID= exp.exp_id, Name= exp.name,
                #     Status= DrvDbExpStatusE.RUNNING.value, CSID= cycler_station_id,
                #     DateBegin= datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                #     DateCreation= exp_result.DateCreation)
                # log.critical(f"Statement: {stmt.inline()}")
                # self.__cache_db.session.execute(stmt)
                self.commit_changes()
            except Exception as err:
                log.error(f"Error updating experiment in cache {err}")
                # raise RuntimeError(f"Error updating experiment in cache {err}")
        except Exception as err: #pylint: disable=broad-except
            # TODO: not catch own raised exceptions
            # print(err)
            # print("Error on GetQueuedExperimentById. Performing rollback...")
            # self.session.rollback()
            log.error(f"Error fetching experiment {err}")
            # raise RuntimeError(f"Error fetching experiment {err}")
        finally:
            log.debug(f"Experiment fetched: {exp.__dict__}, {battery.__dict__}, {profile.__dict__}")
            return exp, battery, profile

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
        profile_range = MidDataPwrRangeC(curr_max= result.CurrMax, curr_min= result.CurrMin,
                                         volt_max= result.VoltMax, volt_min= result.VoltMin)
        profile.range = profile_range
        instructions= []
        stmt = select(DrvDbInstructionC).where(DrvDbInstructionC.ProfID == result.ProfID)
        result = self.__master_db.session.execute(stmt).all()
        if result is None:
            raise MidStrDbElementNotFoundErrorC((f'Instructions for profile {result.ProfID} '
                                                 'not found'))
        try:
            for inst_res in result:
                inst_res:DrvDbInstructionC = inst_res[0]
                instruction = MidDataInstructionC()
                for db_name, att_name in map_inst_db.items():
                    if att_name == 'mode':
                        setattr(instruction, att_name,
                                MidDataPwrModeE(map_instr_modes[getattr(inst_res,db_name)]))
                    elif instruction.mode != MidDataPwrModeE.WAIT and att_name == 'limit_type':
                        setattr(instruction, att_name,
                                MidDataPwrLimitE(map_instr_limit_modes[getattr(inst_res,db_name)]))
                    elif instruction.mode != MidDataPwrModeE.WAIT and att_name == 'limit_ref':
                        setattr(instruction, att_name, getattr(inst_res,db_name))
                    else:
                        setattr(instruction, att_name, getattr(inst_res,db_name))
                instructions.append(instruction)
        except Exception as err:
            log.error(f"Error fetching instructions {err}")
            raise RuntimeError(f"Error fetching instructions {err}")
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
        stmt = select(DrvDbBatteryC).where(DrvDbBatteryC.BatID == result.BatID)
        result = self.__master_db.session.execute(stmt).one()[0]
        if result is None:
            raise MidStrDbElementNotFoundErrorC(f'Battery with id {result.BatID} not found')
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
        result = self.__master_db.session.execute(stmt).one()
        # log.debug(result)
        if result is None:
            raise MidStrDbElementNotFoundErrorC(f'Cycler station with id {cycler_id} not found')
        result = result[0]
        # log.debug(f"Cycler station with id {cycler_id} found, {result.__dict__}")
        cycler_station = MidDataCyclerStationC()
        for key,value in map_cs_db.items():
            setattr(cycler_station, value, getattr(result,key))
        ## Get devices used in the cycler station
        stmt = select(DrvDbUsedDeviceC, DrvDbCompatibleDeviceC).join(DrvDbCompatibleDeviceC,
            DrvDbUsedDeviceC.CompDevID == DrvDbCompatibleDeviceC.CompDevID).where(
                DrvDbUsedDeviceC.CSID == result.CSID)
        result = self.__master_db.session.execute(stmt).all()
        devices= []
        # log.debug(result)
        for devices_res in result:
            used_dev_res = devices_res[0]
            comp_dev_res = devices_res[1]
            device = MidDataDeviceC()
            ## TODO: FILL CORRECTLY THE MAPPING NAMES ATTRIBUTE GET INFO FROM DB 
            device.mapping_names = {'hs_voltage': 'HIGH_SIDE_VOLTAGE', 'temp_body': 'TEMP_1',
                'temp_anod': 'TEMP_2', 'temp_amb': 'TEMP_3'}
            for db_name, att_name in map_dev_db.items():
                if att_name == "device_type":
                    # log.debug(f"device type: {MidDataDeviceTypeE(getattr(comp_dev_res,db_name))}")
                    setattr(device, att_name, MidDataDeviceTypeE(getattr(comp_dev_res,db_name)))
                elif db_name in used_dev_res.__dict__:
                    setattr(device, att_name, getattr(used_dev_res,db_name))
                else:
                    setattr(device, att_name, getattr(comp_dev_res,db_name))
            if comp_dev_res.DeviceType is not DrvDbDeviceTypeE.EPC.value:
                ## Get link configuration if needed
                stmt = select(DrvDbLinkConfigurationC).where(
                    DrvDbLinkConfigurationC.CompDevID == used_dev_res.CompDevID)
                result = self.__master_db.session.execute(stmt).all()
                if result is None:
                    raise MidStrDbElementNotFoundErrorC((f'Link configuration for device '
                                                        f'{comp_dev_res.CompDevID} not found'))
                link_conf = MidDataLinkConfC()
                for res in result:
                    res: DrvDbLinkConfigurationC = res[0]
                    print("res: ", res.__dict__)
                    att_name:str = res.Property.lower()
                    att_value = str(res.Value)
                    if att_value.isdecimal():
                        att_value = int(att_value)
                    elif len(att_value.rsplit('.'))<=2:
                        att_value = float(att_value)
                    setattr(link_conf, att_name, att_value)
                device.link_conf = link_conf
            # log.debug(f"Device created, {device.__dict__}")
            devices.append(device)
        cycler_station.devices= devices
        log.debug(f"Cycler station object, {cycler_station.__dict__}")
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
