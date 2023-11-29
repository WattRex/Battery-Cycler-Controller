#!/usr/bin/python3len
'''
Definition of MID STR Facade where database connection methods are defined.
'''
#######################        MANDATORY IMPORTS         #######################
from __future__ import annotations

#######################         GENERIC IMPORTS          #######################
from datetime import datetime
from typing import List, Tuple

#######################       THIRD PARTY IMPORTS        #######################
from sqlalchemy import select, update

#######################      SYSTEM ABSTRACTION IMPORTS  #######################
from system_logger_tool import sys_log_logger_get_module_logger
log = sys_log_logger_get_module_logger(__name__)

#######################          PROJECT IMPORTS         #######################
from wattrex_driver_db import (DrvDbSqlEngineC, DrvDbMasterExperimentC, DrvDbBatteryC,
        DrvDbProfileC, DrvDbCyclerStationC, DrvDbInstructionC, DrvDbExpStatusE, DrvDbAlarmC,
        DrvDbCacheExtendedMeasureC, DrvDbCacheGenericMeasureC, DrvDbCacheStatusC, DrvDbTypeE,
        DrvDbUsedDeviceC, DrvDbCompatibleDeviceC, DrvDbDeviceTypeE, DrvDbLinkConfigurationC,
        DrvDbCacheExperimentC, DrvDbDetectedDeviceC, DrvDbUsedMeasuresC, DrvDbAvailableMeasuresC,
        transform_experiment_db)

from wattrex_battery_cycler_datatypes.cycler_data import (CyclerDataAlarmC, CyclerDataGenMeasC,
            CyclerDataExtMeasC, CyclerDataAllStatusC, CyclerDataExpStatusE, CyclerDataProfileC,
            CyclerDataBatteryC, CyclerDataDeviceC, CyclerDataDeviceTypeE, CyclerDataExperimentC,
            CyclerDataCyclerStationC, CyclerDataInstructionC, CyclerDataPwrRangeC,
            CyclerDataPwrModeE, CyclerDataPwrLimitE, CyclerDataLinkConfC)

#######################          MODULE IMPORTS          #######################
from .mid_str_mapping import (MAPPING_INSTR_LIMIT_MODES, MAPPING_INSTR_DB, MAPPING_INSTR_MODES,
                              MAPPING_ALARM, MAPPING_BATT_DB, MAPPING_CS_DB, MAPPING_DEV_DB,
                              MAPPING_GEN_MEAS, MAPPING_EXPERIMENT, MAPPING_STATUS)

#######################              ENUMS               #######################

#######################             CLASSES              #######################

class MidStrDbElementNotFoundErrorC(Exception):
    """Exception raised for errors when an input not found in the database.

    Attributes:
        message -- explanation of the error
    """
    def __init__(self, message):
        super().__init__(message)

class MidStrFacadeC: #pylint: disable= too-many-instance-attributes
    '''
    This class is used to interface with the database.
    '''
    def __init__(self, cycler_station_id: int,
                 cred_file : str = ".cred.yaml") -> None:
        log.info("Initializing DB Connection...")
        self.cs_id = cycler_station_id
        self.__master_db: DrvDbSqlEngineC = DrvDbSqlEngineC(db_type=DrvDbTypeE.MASTER_DB,
                                                            config_file= cred_file)
        self.__cache_db: DrvDbSqlEngineC = DrvDbSqlEngineC(db_type=DrvDbTypeE.CACHE_DB,
                                                            config_file= cred_file)
        self.all_status: CyclerDataAllStatusC = CyclerDataAllStatusC()
        self.gen_meas: CyclerDataGenMeasC = CyclerDataGenMeasC()
        self.ext_meas: CyclerDataExtMeasC = CyclerDataExtMeasC()
        self.meas_id: int = 0
        self.status_id: int = 0
        self.alarm_id: int = 0

    def get_start_queued_exp(self) -> Tuple[CyclerDataExperimentC|None, CyclerDataBatteryC|None,
                                            CyclerDataProfileC|None]:
        '''
        Get the oldest queued experiment, assigned to the cycler station where this
        cycler would be running, and change its status to RUNNING in database.
        '''
        self.meas_id = 0
        self.status_id = 0
        self.alarm_id = 0
        exp = None
        battery = None
        profile = None
        self.__master_db.session.expire_all()
        self.__master_db.session.close()
        self.__master_db.session.begin()
        exp_result = self.__master_db.session.query(DrvDbMasterExperimentC).populate_existing().\
            filter( DrvDbMasterExperimentC.Status == DrvDbExpStatusE.QUEUED.value,
            DrvDbMasterExperimentC.CSID == self.cs_id).order_by(
                DrvDbMasterExperimentC.DateCreation.asc()).all()
        log.critical(f"Experiment fetched: {exp_result}")
        if len(exp_result) != 0:
            exp_result: DrvDbMasterExperimentC = exp_result[0]
            exp : CyclerDataExperimentC = CyclerDataExperimentC()
            for db_name, att_name in MAPPING_EXPERIMENT.items():
                setattr(exp, att_name, getattr(exp_result,db_name))

            # Get battery info
            battery = self.__get_exp_battery_data(exp_result.BatID)
            # Get profile info
            profile = self.__get_exp_profile_data(exp_result.ProfID)
            # Change experiment status to running and update begin datetime
            exp_db = DrvDbCacheExperimentC()
            transform_experiment_db(source= exp_result, target = exp_db)
            exp_db.Status = DrvDbExpStatusE.RUNNING.value
            exp_db.DateBegin = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            self.__cache_db.session.add(exp_db)
            log.debug(f"Experiment fetched: {exp.__dict__}, {battery.__dict__}, {profile.__dict__}")
        else:
            log.debug("No experiment found")
            log.info(f"No experiment found {exp_result}")
        return exp, battery, profile

    ## All methods that get information will gather the info from the master db
    def get_exp_status(self, exp_id: int) -> CyclerDataExpStatusE|None:
        """Returns the experiment status .
        Args:
            exp_id (int): [description]
        Returns:
            CyclerDataExpStatusE: [description]
        """
        stmt = select(DrvDbMasterExperimentC.Status).where(DrvDbMasterExperimentC.ExpID == exp_id).\
            execution_options(populate_existing=True)
        result: DrvDbExpStatusE = self.__master_db.session.execute(stmt).all()
        if len(result) != 0:
            raise MidStrDbElementNotFoundErrorC(f'Experiment with id {exp_id} not found')
        return CyclerDataExpStatusE(result[0][0])

    def __get_exp_profile_data(self,prof_id: int) -> CyclerDataProfileC|None:
        """AI is creating summary for get_exp_profile_data
        Args:
            exp_id (int): [description]
        Returns:
            CyclerDataProfileC: [description]
        """
        stmt = select(DrvDbProfileC).where(DrvDbProfileC.ProfID == prof_id).\
            execution_options(populate_existing=True)
        result = self.__master_db.session.execute(stmt).all()
        result: DrvDbProfileC = result[0][0]
        profile = CyclerDataProfileC(name= result.Name)
        profile_range = CyclerDataPwrRangeC(curr_max= result.CurrMax, curr_min= result.CurrMin,
                                         volt_max= result.VoltMax, volt_min= result.VoltMin)
        profile.range = profile_range
        instructions= []
        stmt = select(DrvDbInstructionC).where(DrvDbInstructionC.ProfID == result.ProfID)
        result = self.__master_db.session.execute(stmt).all()
        if len(result) != 0:
            for inst_res in result:
                inst_res:DrvDbInstructionC = inst_res[0]
                instruction = CyclerDataInstructionC()
                for db_name, att_name in MAPPING_INSTR_DB.items():
                    if att_name == 'mode':
                        setattr(instruction, att_name,
                                CyclerDataPwrModeE(MAPPING_INSTR_MODES[getattr(inst_res,db_name)]))
                    elif instruction.mode != CyclerDataPwrModeE.WAIT and att_name == 'limit_type':
                        setattr(instruction, att_name,
                            CyclerDataPwrLimitE(MAPPING_INSTR_LIMIT_MODES[getattr(inst_res,db_name)]
                                                ))
                    elif instruction.mode != CyclerDataPwrModeE.WAIT and att_name == 'limit_ref':
                        setattr(instruction, att_name, getattr(inst_res,db_name))
                    else:
                        setattr(instruction, att_name, getattr(inst_res,db_name))
                instructions.append(instruction)
        profile.instructions = instructions
        return profile

    def __get_exp_battery_data(self, bat_id: int) -> CyclerDataBatteryC|None:
        """Get the mid - data of an experiment .
        Args:
            exp_id (int): [description]
        Returns:
            CyclerDataBatteryC: [description]
        """
        battery = None
        stmt = select(DrvDbBatteryC).where(DrvDbBatteryC.BatID == bat_id)
        try:
            result = self.__master_db.session.execute(stmt).one()[0]
        except Exception as err:
            log.exception(err)
            raise Exception(err) from err #pylint: disable= broad-exception-raised
        battery = CyclerDataBatteryC()
        for db_name, att_name in MAPPING_BATT_DB.items():
            setattr(battery, att_name, getattr(result,db_name))
        bat_range = CyclerDataPwrRangeC()
        bat_range.fill_current(result.CurrMax, result.CurrMin)
        bat_range.fill_voltage(result.VoltMax, result.VoltMin)
        battery.elec_ranges = bat_range
        return battery

    def get_cycler_station_status(self) -> bool:
        """Returns if the cycler station is deprecated or not.
        Returns:
            [bool]: [description]
        """
        ## Get cycler station info
        stmt = select(DrvDbCyclerStationC.Deprecated).where(DrvDbCyclerStationC.CSID == self.cs_id)
        result = self.__master_db.session.execute(stmt).one()[0]
        return result

    def get_cycler_station_info(self) -> CyclerDataCyclerStationC|None: #pylint: disable= too-many-locals
        """Returns the name and name of the cycle station for the experiment .
        Returns:
            [CyclerDataCyclerStationC]: [description]
        """
        ## Get cycler station info
        stmt = select(DrvDbCyclerStationC).where(DrvDbCyclerStationC.CSID == self.cs_id)
        result = self.__master_db.session.execute(stmt).one()[0]
        cycler_station = CyclerDataCyclerStationC()
        for key,value in MAPPING_CS_DB.items():
            setattr(cycler_station, value, getattr(result,key))
        ## Get devices used in the cycler station
        stmt = select(DrvDbUsedDeviceC).where(DrvDbUsedDeviceC.CSID == self.cs_id)
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
            device = CyclerDataDeviceC(mapping_names={})
            for db_name, att_name in MAPPING_DEV_DB.items():
                if att_name == "device_type":
                    setattr(device, att_name, CyclerDataDeviceTypeE(getattr(comp_dev_res,db_name)))
                elif db_name in detected_dev_res.__dict__:
                    setattr(device, att_name, getattr(detected_dev_res,db_name))
                else:
                    setattr(device, att_name, getattr(comp_dev_res,db_name))
            stmt = select(DrvDbUsedMeasuresC).where(DrvDbUsedMeasuresC.DevID == res_dev.DevID).\
                where(DrvDbUsedMeasuresC.CSID == self.cs_id)
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
                if len(result) != 0:
                    link_conf = {}
                    for res in result:
                        res: DrvDbLinkConfigurationC = res[0]
                        link_conf[res.Property.lower()] = str(res.Value)
                    device.link_conf = CyclerDataLinkConfC(**link_conf)
            devices.append(device)
        cycler_station.devices= devices
        log.debug(f"Cycler station object, {cycler_station.__dict__}")
        return cycler_station

    ## All methods that write information will write the info into the cache db
    def modify_current_exp(self, exp_status: CyclerDataExpStatusE, exp_id: int) -> None:
        """Modify the current experiment status .
        Args:
            exp_status (CyclerDataExpStatusE): [description]
        """
        if exp_status in (CyclerDataExpStatusE.ERROR,CyclerDataExpStatusE.FINISHED):
            stmt = update(DrvDbCacheExperimentC).where(DrvDbCacheExperimentC.ExpID == exp_id).\
                values(DateFinish= datetime.now(), Status = exp_status.value)
        else:
            stmt = update(DrvDbCacheExperimentC).where(DrvDbCacheExperimentC.ExpID == exp_id).\
                values(Status = exp_status.value)
        self.__cache_db.session.execute(stmt)

    def write_status_changes(self, exp_id: int) -> None:
        """Write the status changes into the cache db .
        Args:
            new_status (CyclerDataAllStatusC): [description]
        """
        status = DrvDbCacheStatusC()
        status.StatusID = self.status_id
        status.Timestamp = datetime.now()
        status.ExpID = exp_id
        for db_name, att_name in MAPPING_STATUS.items():
            setattr(status, db_name, getattr(self.all_status.pwr_dev, att_name))
        self.__cache_db.session.add(status)
        self.status_id += 1

    def write_new_alarm(self, alarms: List[CyclerDataAlarmC], exp_id: int) -> None:
        """Write an alarm into the cache db .
        Args:
            alarm (List[CyclerDataAlarmC]): [description]
        """
        for alarm in alarms:
            alarm_db = DrvDbAlarmC()
            alarm_db.AlarmID = self.alarm_id
            alarm_db.Timestamp = datetime.now()
            alarm_db.ExpID = exp_id
            for db_name, att_name in MAPPING_ALARM.items():
                setattr(alarm_db, db_name, getattr(alarm, att_name))
            self.__cache_db.session.add(alarm_db)
            self.alarm_id += 1

    def write_generic_measures(self, exp_id: int) -> None:
        """Write the generic measures into the cache db .
        Args:
            gen_meas (CyclerDataGenMeasC): [description]
        """
        gen_meas = DrvDbCacheGenericMeasureC()
        gen_meas.Timestamp = datetime.now()
        gen_meas.ExpID = exp_id
        gen_meas.MeasID = self.meas_id
        gen_meas.PowerMode = self.all_status.pwr_mode.name
        for db_name, att_name in MAPPING_GEN_MEAS.items():
            setattr(gen_meas, db_name, getattr(self.gen_meas, att_name))
        self.__cache_db.session.add(gen_meas)

    def write_extended_measures(self, exp_id: int) -> None:
        """Write the extended measures into the cache db .
        Args:
            ext_meas (CyclerDataExtMeasC): [description]
        """
        for key in self.ext_meas.__dict__:
            ext_meas = DrvDbCacheExtendedMeasureC()
            ext_meas.ExpID = exp_id
            ext_meas.UsedMeasID = key.split('_')[-1]
            ext_meas.MeasID = self.meas_id
            ext_meas.Value = getattr(self.ext_meas,key)
            self.__cache_db.session.add(ext_meas)

    def turn_cycler_station_deprecated(self, exp_id: int|None) -> None:
        """Method to turn a cycler station to deprecated.
        """
        self.__master_db.session.expire_all()
        self.__master_db.session.close()
        self.__master_db.session.begin()
        if exp_id is not None:
            stmt = update(DrvDbCacheExperimentC).where(DrvDbCacheExperimentC.ExpID == exp_id).\
                values(DateFinish= datetime.now(), Status = DrvDbExpStatusE.ERROR.value)
            self.__cache_db.session.execute(stmt)
        stmt =  select(DrvDbMasterExperimentC)\
                    .where(DrvDbMasterExperimentC.Status == DrvDbExpStatusE.QUEUED.value)\
                    .where(DrvDbMasterExperimentC.CSID == self.cs_id)\
                    .order_by(DrvDbMasterExperimentC.DateCreation.asc())
        result = self.__master_db.session.execute(stmt).all()

        for exp_result in result:
            exp_result: DrvDbMasterExperimentC = exp_result[0]
            exp_db = DrvDbCacheExperimentC()
            transform_experiment_db(source= exp_result, target = exp_db)
            exp_db.Status = DrvDbExpStatusE.ERROR.value
            exp_db.DateBegin = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            exp_db.DateFinish = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            self.__cache_db.session.add(exp_db)

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
