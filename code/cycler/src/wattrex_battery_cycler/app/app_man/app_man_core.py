#!/usr/bin/python3
"""
This modules execute the machine status.
"""
#######################        MANDATORY IMPORTS         #######################
from __future__ import annotations
from typing import Tuple
from enum import Enum
#######################         GENERIC IMPORTS          #######################

#######################       THIRD PARTY IMPORTS        #######################
from system_logger_tool import SysLogLoggerC, sys_log_logger_get_module_logger, Logger
if __name__ == '__main__':
    cycler_logger = SysLogLoggerC(file_log_levels= './config/log_config.yaml')
log: Logger = sys_log_logger_get_module_logger(__name__)

from system_shared_tool import SysShdChanC, SysShdSharedObjC
#######################          PROJECT IMPORTS         #######################

#######################          MODULE IMPORTS          #######################
from mid.mid_str import MidStrReqCmdE, MidStrCmdDataC, MidStrDataCmdE
from wattrex_battery_cycler_datatypes.cycler_data import (CyclerDataExperimentC, CyclerDataProfileC,
                CyclerDataBatteryC, CyclerDataExpStatusE, CyclerDataAllStatusC, CyclerDataAlarmC,
                    CyclerDataGenMeasC, CyclerDataExtMeasC, CyclerDataCyclerStationC)
from mid.mid_pwr import MidPwrControlC
#######################              ENUMS               #######################
class AppManCoreStatusE(Enum):
    """Application manager status
    """
    GETTING_EXP = 0
    EXECUTE = 1
    PREPARING = 2
    ERROR = 3

#########             CLASSES              #######################
def alarm_callback(alarm: CyclerDataAlarmC) -> None:
    log.error("This is a test for alarm callback")
    log.error(f"Received {alarm.__dict__}")
class AppManCoreC:
    """Manage the cycler station.
    """
    def __init__(self, shared_gen_meas: SysShdSharedObjC, shared_ext_meas: SysShdSharedObjC,
                shared_all_status: SysShdSharedObjC, str_reqs: SysShdChanC,
                str_data: SysShdChanC, str_alarms: SysShdChanC) -> None:
        ##
        self.state: AppManCoreStatusE = AppManCoreStatusE.GETTING_EXP

        ## Attributes related with experiment
        self.profile: CyclerDataProfileC|None = None
        self.experiment: CyclerDataExperimentC|None = None
        self.battery: CyclerDataBatteryC|None = None
        self.exp_status: CyclerDataExpStatusE = CyclerDataExpStatusE.QUEUED
        ## Attributes related with measurements
        self.__shd_gen_meas = shared_gen_meas
        self.__shd_ext_meas = shared_ext_meas
        self.__shd_all_status  = shared_all_status
        self.__local_all_status: CyclerDataAllStatusC|None = None
        self.__local_gen_meas: CyclerDataGenMeasC|None = None
        self.__local_ext_meas: CyclerDataExtMeasC|None = None
        ## Channel attributes to receive and send info
        self.__chan_alarms = str_alarms
        self.__chan_str_reqs = str_reqs
        self.__chan_str_data = str_data

        ## Power control object
        self.pwr_control: MidPwrControlC= MidPwrControlC(devices= self.get_cs_info().devices,
                                        alarm_callback= alarm_callback)

    def get_cs_info(self) -> CyclerDataCyclerStationC:
        """Get the cycler station info from the database

        Returns:
            CyclerDataCyclerStationC: Cycler station info
        """
        request: MidStrCmdDataC = MidStrCmdDataC(cmd= MidStrReqCmdE.GET_CS)
        self.__chan_str_reqs.send_data(request)
        response: MidStrCmdDataC = self.__chan_str_data.receive_data()
        if response.cmd != MidStrDataCmdE.CS_DATA:
            raise ValueError(("Unexpected response from MID_STR, expected CS_DATA "
                              f"and got {response.cmd}"))
        return response.station

    def __fetch_new_exp(self) -> Tuple[CyclerDataExperimentC, CyclerDataBatteryC, CyclerDataProfileC]:
        """AI is creating summary for fetch_new_exp

        Raises:
            ValueError: [description]

        Returns:
            Tuple[CyclerDataExperimentC, CyclerDataBatteryC, CyclerDataProfileC]: [description]
        """
        log.debug("Checking for new experiments")
        request: MidStrCmdDataC = MidStrCmdDataC(cmd= MidStrReqCmdE.GET_NEW_EXP)
        self.__chan_str_reqs.send_data(request)
        response: MidStrCmdDataC = self.__chan_str_data.receive_data()
        if response.cmd != MidStrDataCmdE.EXP_DATA:
            raise ValueError(("Unexpected response from MID_STR, expected EXP_DATA "
                              f"and got {response.cmd}"))
        return response.experiment, response.battery, response.profile

    def __validate_exp_ranges(self, battery: CyclerDataBatteryC,
                       profile: CyclerDataProfileC) -> bool:
        """Returns True if the experiment is valid, which means the electric range of the profile
        is between the limits of the battery.

        Args:
            battery (CyclerDataBatteryC): [description]
            profile (CyclerDataProfileC): [description]

        Returns:
            bool: [description]
        """
        # Check if the profile range is inside the battery range
        return profile.range.in_range(battery.elec_ranges)

    def __write_exp_status(self, exp_status: CyclerDataExpStatusE) -> None:
        """Write the experiment status in the shared memory

        Args:
            exp_status (CyclerDataExpStatusE): Experiment status
        """
        request: MidStrCmdDataC = MidStrCmdDataC(cmd= MidStrReqCmdE.SET_EXP_STATUS,
                        exp_status= exp_status)
        self.__chan_str_reqs.send_data(request)

    def __execute_experiment(self) -> None:
        """Execute the experiment
        """
        log.debug("Executing experiment")
        # First step is to update the local data in power
        self.pwr_control.update_local_data(self.__local_gen_meas, self.__local_all_status)
        self.exp_status, self.__local_gen_meas.inst_id = self.pwr_control.process_iteration()
        self.__write_exp_status(self.exp_status)

    def __sync_shd_data(self):
        """Update the local and global data arrays of the local and global data .
        """
        log.debug("Updating local and global data")
        self.__local_gen_meas : CyclerDataGenMeasC = self.__shd_gen_meas.\
            merge_included_tags(self.__local_gen_meas, ['voltage','current','power']) # type: ignore
        self.__local_ext_meas : CyclerDataExtMeasC = self.__shd_ext_meas.read() # type: ignore
        self.__local_all_status : CyclerDataAllStatusC = self.__shd_all_status.read() # type: ignore

    def execute_machine_status(self) -> None:
        """Execute the machine status
        """
        log.debug("Executing machine status")
        try:
            if self.state == AppManCoreStatusE.GETTING_EXP:
                log.debug("Getting experiment")
                # Despite the status check if the cs is deprecated
                cs_station_info = self.get_cs_info()
                if cs_station_info.deprecated:
                    log.critical("Cycler station is deprecated")
                    self.state = AppManCoreStatusE.ERROR
                self.experiment, self.battery, self.profile = self.__fetch_new_exp()
                if not self.experiment is None:
                    if not self.__validate_exp_ranges(self.battery, self.profile):
                        self.exp_status = CyclerDataExpStatusE.ERROR
                        self.__write_exp_status(self.exp_status)
                    else:
                        self.state = AppManCoreStatusE.PREPARING

            elif self.state == AppManCoreStatusE.PREPARING:
                ## Get devices in cycler station and creates pwr control object, every time a experiment
                # is fetch a new instante is created
                ## TODO: FUNCTION FOR ALARMS CALLBACK  
                log.debug("Preparing experiment")
                self.pwr_control.set_new_experiment(instructions= self.profile.instructions,
                                                    bat_pwr_range= self.battery.elec_ranges)
                
                self.state = AppManCoreStatusE.EXECUTE
            elif self.state == AppManCoreStatusE.EXECUTE:
                log.debug("Executing experiment")
                self.__sync_shd_data()
                self.__execute_experiment()
                if self.exp_status == (CyclerDataExpStatusE.FINISHED, CyclerDataExpStatusE.ERROR):
                    self.state = AppManCoreStatusE.GETTING_EXP
            else: 
                log.debug("Error in machine status")
        except Exception as err:
            log.error(f"Error in machine status: {err}")
            self.state = AppManCoreStatusE.ERROR
