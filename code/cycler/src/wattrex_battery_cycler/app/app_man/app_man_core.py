#!/usr/bin/python3
"""
This modules execute the machine status.
"""
#######################        MANDATORY IMPORTS         #######################
from __future__ import annotations
from typing import Tuple, List
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
from mid.mid_pwr import MidPwrControlC
from wattrex_battery_cycler_datatypes.cycler_data import (CyclerDataExperimentC, CyclerDataProfileC,
                CyclerDataBatteryC, CyclerDataExpStatusE, CyclerDataAllStatusC, CyclerDataAlarmC,
                                CyclerDataGenMeasC, CyclerDataExtMeasC, CyclerDataCyclerStationC,
                                CyclerDataDeviceC)
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
    """Callback for alarms raised along the different nodes

    Args:
        alarm (CyclerDataAlarmC): [description]
    """
    log.error("This is a test for alarm callback")
    log.error(f"Received {alarm.__dict__}")

class AppManCoreC:
    """Manage the cycler station.
    """
    def __init__(self, devices: List[CyclerDataDeviceC], str_reqs: SysShdChanC,
                str_data: SysShdChanC, str_alarms: SysShdChanC) -> None:
        ##
        self.state: AppManCoreStatusE = AppManCoreStatusE.GETTING_EXP

        ## Attributes related with experiment
        self.profile: CyclerDataProfileC|None = None
        self.experiment: CyclerDataExperimentC|None = None
        self.battery: CyclerDataBatteryC|None = None
        self.exp_status: CyclerDataExpStatusE = CyclerDataExpStatusE.QUEUED
        ## Attributes related with measurements
        self.__local_all_status: CyclerDataAllStatusC|None = None
        self.__local_gen_meas: CyclerDataGenMeasC|None = None
        self.__local_ext_meas: CyclerDataExtMeasC|None = None
        ## Channel attributes to receive and send info
        self.__chan_alarms = str_alarms
        self.__chan_str_reqs = str_reqs
        self.__chan_str_data = str_data
        self.__deprecated: bool = False
        ## Power control object
        self.pwr_control: MidPwrControlC= MidPwrControlC(devices= devices,
                        alarm_callback= alarm_callback)

    def process_request(self):
        """Process the requested made to the str node, 2 messages per iteration
        """
        for _ in range(2):
            if not self.__chan_str_data.is_empty():
                msg: MidStrCmdDataC = self.__chan_str_data.receive_data()
                if msg.error_flag:
                    log.warning(f"Error in the message containing {msg.cmd_type}")
                else:
                    if msg.cmd_type is MidStrDataCmdE.EXP_DATA:
                        self.experiment = msg.experiment
                        self.battery = msg.battery
                        self.profile = msg.profile
                    elif msg.cmd_type is MidStrDataCmdE.EXP_STATUS:
                        self.exp_status = msg.exp_status
                    elif msg.cmd_type is MidStrDataCmdE.CS_STATUS:
                        self.__deprecated: bool = msg.station.deprecated

    def request_cs_status(self) -> None:
        """
        Request the status of the CS by sending a request to the request channel.
        """
        log.debug("Checking CS status")
        request: MidStrCmdDataC = MidStrCmdDataC(cmd= MidStrReqCmdE.GET_CS_STATUS)
        self.__chan_str_reqs.send_data(request)

    def __fetch_new_exp(self) -> None:
        """AI is creating summary for fetch_new_exp

        Raises:
            ValueError: [description]

        Returns:
            Tuple[CyclerDataExperimentC, CyclerDataBatteryC, CyclerDataProfileC]: [description]
        """
        log.debug("Checking for new experiments")
        request: MidStrCmdDataC = MidStrCmdDataC(cmd= MidStrReqCmdE.GET_NEW_EXP)
        self.__chan_str_reqs.send_data(request)
        # response: MidStrCmdDataC = self.__chan_str_data.receive_data()
        # if response.error_flag:
        #     raise ValueError(("Error in response from MID STR"))
        # elif response.cmd_type != MidStrDataCmdE.EXP_DATA:
        #     raise ValueError(("Unexpected response from MID_STR, expected EXP_DATA "
        #                       f"and got {response.cmd_type}"))
        # return response.experiment, response.battery, response.profile

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
        res = (profile.range.in_range_current(battery.elec_ranges) and
               profile.range.in_range_voltage(battery.elec_ranges))
        return res

    def __write_exp_status(self, exp_status: CyclerDataExpStatusE) -> None:
        """Write the experiment status in the shared memory

        Args:
            exp_status (CyclerDataExpStatusE): Experiment status
        """
        request: MidStrCmdDataC = MidStrCmdDataC(cmd_type= MidStrReqCmdE.SET_EXP_STATUS,
                        exp_status= exp_status)
        self.__chan_str_reqs.send_data(request)

    def __deprecated_cs(self):
        """Send a deprecated command to the str node to turn all experiments to error
        """
        request: MidStrCmdDataC = MidStrCmdDataC(cmd_type= MidStrReqCmdE.TURN_DEPRECATED)
        self.__chan_str_reqs.send_data(request)

    def __execute_experiment(self) -> None:
        """Execute the experiment
        """
        log.debug("Executing experiment")
        # First step is to update the local data in power
        self.pwr_control.update_local_data(self.__local_gen_meas, self.__local_all_status)
        self.exp_status, self.__local_gen_meas.instr_id = self.pwr_control.process_iteration()
        self.__write_exp_status(self.exp_status)

    def execute_machine_status(self) -> None:
        """Execute the machine status
        """
        log.debug("Executing machine status")
        try:
            ### Check always if the cycler station is deprecated
            if self.__deprecated:
                log.critical("Cycler station is deprecated")
                self.__deprecated_cs()
                self.state = AppManCoreStatusE.ERROR
            if self.state == AppManCoreStatusE.GETTING_EXP:
                log.debug("Getting experiment")
                self.__fetch_new_exp()
                if not self.experiment is None:
                    if not self.__validate_exp_ranges(self.battery, self.profile):
                        self.exp_status = CyclerDataExpStatusE.ERROR
                        self.__write_exp_status(self.exp_status)
                    else:
                        self.state = AppManCoreStatusE.PREPARING

            elif self.state == AppManCoreStatusE.PREPARING:
                ## Set experiment to pwr control
                ## TODO: FUNCTION FOR ALARMS CALLBACK
                log.debug("Preparing experiment")
                self.pwr_control.set_new_experiment(instructions= self.profile.instructions,
                                                    bat_pwr_range= self.battery.elec_ranges)
                if self.pwr_control.instructions == self.profile.instructions:
                    self.state = AppManCoreStatusE.EXECUTE
            elif self.state == AppManCoreStatusE.EXECUTE:
                log.debug("Executing experiment")
                self.__execute_experiment()
                if self.exp_status == (CyclerDataExpStatusE.FINISHED, CyclerDataExpStatusE.ERROR):
                    self.request_cs_status()
                    self.state = AppManCoreStatusE.GETTING_EXP
            else:
                log.debug("Error in machine status")
        except Exception as err:
            log.error(f"Error in machine status: {err}")
            self.state = AppManCoreStatusE.ERROR
