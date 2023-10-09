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
        DrvDbCacheExperimentC, DrvDbDetectedDeviceC, DrvDbUsedMeasuresC, DrvDbAvailableMeasuresC)

#######################          MODULE IMPORTS          #######################
from .mid_str_mapping import (mapping_alarm, mapping_status, mapping_gen_meas, mapping_instr_db,
        mapping_cs_db, mapping_dev_db, mapping_batt_db, mapping_experiment, mapping_instr_modes,
        mapping_instr_limit_modes, remapping_dict)
from ..mid_data import (MidDataAlarmC, MidDataGenMeasC, MidDataExtMeasC, MidDataAllStatusC,
            MidDataExpStatusE, MidDataProfileC, MidDataBatteryC, MidDataDeviceC, MidDataDeviceTypeE,
            MidDataExperimentC, MidDataCyclerStationC, MidDataInstructionC, MidDataPwrRangeC,
            MidDataPwrModeE, MidDataPwrLimitE, MidDataLinkConfC)

#######################              ENUMS               #######################

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
        self.all_status: MidDataAllStatusC = MidDataAllStatusC()
        self.gen_meas: MidDataGenMeasC = MidDataGenMeasC()
        self.ext_meas: MidDataExtMeasC = MidDataExtMeasC()
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
            try:
                for db_name, att_name in mapping_experiment.items():
                    setattr(exp, att_name, getattr(exp_result,db_name))
            except: 
                log.error("Error MAPPING experiment")

            # Get battery info
            battery = self.get_exp_battery_data(exp.exp_id)
            # Get profile info
            profile = self.get_exp_profile_data(exp.exp_id)
            try:
                # Change experiment status to running and update begin datetime
                exp_dict= {'ExpID': exp.exp_id, 'CSID': cycler_station_id, 'Name': exp.name,
                    'BatID': exp_result.BatID, 'ProfID': exp_result.ProfID,
                    'Description': exp_result.Description, 'Status': DrvDbExpStatusE.RUNNING.value,
                    'DateBegin': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                    'DateCreation': exp_result.DateCreation}
                a = DrvDbCacheExperimentC(**exp_dict)
                self.__cache_db.session.add(a)
                log.debug(f"DEBUG COMMIT {a.__dict__}")
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
                for db_name, att_name in mapping_instr_db.items():
                    if att_name == 'mode':
                        setattr(instruction, att_name,
                                MidDataPwrModeE(mapping_instr_modes[getattr(inst_res,db_name)]))
                    elif instruction.mode != MidDataPwrModeE.WAIT and att_name == 'limit_type':
                        setattr(instruction, att_name,
                                MidDataPwrLimitE(mapping_instr_limit_modes[getattr(inst_res,db_name)]))
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
        for db_name, att_name in mapping_batt_db.items():
            setattr(battery, att_name, getattr(result,db_name))
        bat_range = MidDataPwrRangeC()
        bat_range.fill_current(result.CurrMax, result.CurrMin)
        bat_range.fill_voltage(result.VoltMax, result.VoltMin)
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
        for key,value in mapping_cs_db.items():
            setattr(cycler_station, value, getattr(result,key))
        ## Get devices used in the cycler station
        stmt = select(DrvDbUsedDeviceC).where(DrvDbUsedDeviceC.CSID == cycler_id)
        result = self.__master_db.session.execute(stmt).all()
        log.debug(result)
        devices= []
        for res_dev in result:
            res_dev: DrvDbUsedDeviceC = res_dev[0]
            log.debug(f"Device found, {res_dev.__dict__}")
            stmt = select(DrvDbDetectedDeviceC, DrvDbCompatibleDeviceC).join(DrvDbCompatibleDeviceC,
                DrvDbDetectedDeviceC.CompDevID == DrvDbCompatibleDeviceC.CompDevID).where(
                    DrvDbDetectedDeviceC.DevID == res_dev.DevID)
            result = self.__master_db.session.execute(stmt).one()
            detected_dev_res = result[0]
            comp_dev_res = result[1]
            device = MidDataDeviceC(mapping_names={})
            for db_name, att_name in mapping_dev_db.items():
                if att_name == "device_type":
                    # log.debug(f"device type: {MidDataDeviceTypeE(getattr(comp_dev_res,db_name))}")
                    setattr(device, att_name, MidDataDeviceTypeE(getattr(comp_dev_res,db_name)))
                elif db_name in detected_dev_res.__dict__:
                    setattr(device, att_name, getattr(detected_dev_res,db_name))
                else:
                    setattr(device, att_name, getattr(comp_dev_res,db_name))
            stmt = select(DrvDbUsedMeasuresC).where(DrvDbUsedMeasuresC.DevID == res_dev.DevID and
                                                    DrvDbUsedMeasuresC.CSID == cycler_id)
            ext_meas_res = self.__master_db.session.execute(stmt).all()
            for ext_meas in ext_meas_res:
                ext_meas: DrvDbUsedMeasuresC = ext_meas[0]
                stmt = select(DrvDbAvailableMeasuresC).where(
                    DrvDbAvailableMeasuresC.MeasType == ext_meas.MeasType and
                    DrvDbAvailableMeasuresC.CompDevID == comp_dev_res.CompDevID)
                available_meas = self.__master_db.session.execute(stmt).one()
                available_meas: DrvDbAvailableMeasuresC = available_meas[0]
                device.mapping_names[available_meas.MeasName] = int(ext_meas.UsedMeasID)
            if comp_dev_res.DeviceType is not DrvDbDeviceTypeE.EPC.value:
                ## Get link configuration if needed
                stmt = select(DrvDbLinkConfigurationC).where(
                    DrvDbLinkConfigurationC.CompDevID == detected_dev_res.CompDevID)
                result = self.__master_db.session.execute(stmt).all()
                if result is None:
                    raise MidStrDbElementNotFoundErrorC((f'Link configuration for device '
                                                        f'{comp_dev_res.CompDevID} not found'))
                link_conf = {}
                for res in result:
                    res: DrvDbLinkConfigurationC = res[0]
                    link_conf[res.Property.lower()] = str(res.Value)
                device.link_conf = MidDataLinkConfC(**link_conf)
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
            values(Timestamp= datetime.now(), Status = exp_status.value)
        self.__cache_db.session.execute(stmt)

    def write_status_changes(self, exp_id: int) -> None:
        """Write the status changes into the cache db .
        Args:
            new_status (MidDataAllStatusC): [description]
        """
        status = DrvDbCacheStatusC()
        status.Timestamp = datetime.now()
        status.ExpID = exp_id
        for db_name, att_name in mapping_status.items():
            setattr(status, db_name, getattr(self.all_status.pwr_dev, att_name))
        self.__cache_db.session.add(status)
        # stmt = update(DrvDbCacheStatusC).where(DrvDbCacheStatusC.ExpID == exp_id).\
        #     values(Timestamp= datetime.now(),
        #            **remapping_dict(self.all_status.pwr_dev.__dict__, mapping_status))
        # self.__cache_db.session.execute(stmt)

    def write_new_alarm(self, alarms: List[MidDataAlarmC], exp_id: int) -> None:
        """Write an alarm into the cache db .
        Args:
            alarm (List[MidDataAlarmC]): [description]
        """
        for alarm in alarms:
            stmt = insert(DrvDbAlarmC).values(Timestamp= datetime.now(), ExpID = exp_id,
                                              **remapping_dict(alarm.__dict__,mapping_alarm))
            self.__cache_db.session.execute(stmt)

    def write_generic_measures(self, exp_id: int) -> None:
        """Write the generic measures into the cache db .
        Args:
            gen_meas (MidDataGenMeasC): [description]
        """
        try:
            gen_meas = DrvDbCacheGenericMeasureC()
            gen_meas.Timestamp = datetime.now()
            gen_meas.ExpID = exp_id
            gen_meas.MeasID = self.meas_id
            gen_meas.PwrMode = self.all_status.pwr_mode.name
            for db_name, att_name in mapping_gen_meas.items():
                setattr(gen_meas, db_name, getattr(self.gen_meas, att_name))
            self.__cache_db.session.add(gen_meas)
            # stmt = insert(DrvDbCacheGenericMeasureC).values(Timestamp= datetime.now(), ExpID = exp_id,
            #                 MeasID= self.meas_id, PowerMode= self.all_status.pwr_mode,
            #                 **remapping_dict(self.gen_meas.__dict__, mapping_gen_meas))
            # self.__cache_db.session.execute(stmt)
            self.meas_id += 1
            self.commit_changes()
        except Exception as err:
            log.warning(err)

    def write_extended_measures(self, exp_id: int) -> None:
        """Write the extended measures into the cache db .
        Args:
            ext_meas (MidDataExtMeasC): [description]
        """
        try:
            for key in self.ext_meas.__dict__:
                ext_meas = DrvDbCacheExtendedMeasureC()
                ext_meas.ExpID = exp_id
                log.warning(f"key: {key}, value: {getattr(self.ext_meas,key)}")
                ext_meas.UsedMeasID = key.split('_')[-1]
                ext_meas.MeasID = self.meas_id
                ext_meas.Value = getattr(self.ext_meas,key)
                self.__cache_db.session.add(ext_meas)
                # stmt = insert(DrvDbCacheExtendedMeasureC).values(UsedMeasID= key.split('_')[0],
                #             MeasID= self.meas_id,
                #             Value= getattr(self.ext_meas,key), ExpID= exp_id)
                # self.__cache_db.session.execute(stmt)
                self.commit_changes()
        except AttributeError as err:
            log.error(f"Could not write extended measures into the cache db {err}")

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
