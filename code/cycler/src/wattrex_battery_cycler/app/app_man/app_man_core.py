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
from system_logger_tool import sys_log_logger_get_module_logger, Logger
log: Logger = sys_log_logger_get_module_logger(__name__)

from system_shared_tool import SysShdChanC
#######################          PROJECT IMPORTS         #######################
from wattrex_battery_cycler_datatypes.cycler_data import (CyclerDataExperimentC, CyclerDataProfileC,
                CyclerDataBatteryC, CyclerDataExpStatusE, CyclerDataAllStatusC, CyclerDataAlarmC,
                                CyclerDataGenMeasC, CyclerDataExtMeasC, CyclerDataCyclerStationC,
                                CyclerDataDeviceC)
from mid.mid_str import MidStrReqCmdE, MidStrCmdDataC, MidStrDataCmdE
from mid.mid_pwr import MidPwrControlC

#######################          MODULE IMPORTS          #######################

#######################              ENUMS               #######################
_PERIOD_WAIT_EXP = 10
class AppManCoreStatusE(Enum):
    """Application manager status
    """
    GET_EXP = 0
    PREPARE_EXP = 1
    EXECUTE_EXP = 2
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
        self.state: AppManCoreStatusE = AppManCoreStatusE.GET_EXP

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
        self.__wait_exp_reqst: bool = False
        self.__wait_cs_reqst: bool = False
        self.__iter: int = 0
        ## Power control object
        self.pwr_control: MidPwrControlC= MidPwrControlC(devices= devices,
                        alarm_callback= alarm_callback, battery_limits=None, instruction_set=None)
    @property
    def local_gen_meas(self) -> CyclerDataGenMeasC|None:
        """Return the local general measurements

        Returns:
            CyclerDataGenMeasC: General measurements
        """
        return self.__local_gen_meas

    @property
    def local_ext_meas(self) -> CyclerDataExtMeasC|None:
        """Return the local external measurements

        Returns:
            CyclerDataExtMeasC: External measurements
        """
        return self.__local_ext_meas

    @property
    def local_all_status(self) -> CyclerDataAllStatusC|None:
        """Return the local all status

        Returns:
            CyclerDataAllStatusC: All status
        """
        return self.__local_all_status


    def update_local_data(self, new_gen_meas: CyclerDataGenMeasC, new_ext_meas: CyclerDataExtMeasC,
                          new_all_status: CyclerDataAllStatusC) -> None:
        """Update the local data"""
        self.__local_all_status = new_all_status
        self.__local_ext_meas = new_ext_meas
        self.__local_gen_meas = new_gen_meas

    def process_request(self):
        """Process the requested made to the str node, 2 messages per iteration
        """
        log.debug("Processing request")
        for _ in range(2):
            msg: MidStrCmdDataC = self.__chan_str_data.receive_data_unblocking()
            if msg is not None:
                if msg.error_flag:
                    log.debug(f"Error in the message containing {msg.cmd_type}")
                    if (msg.cmd_type == MidStrDataCmdE.EXP_DATA and
                        any(var is None for var in (msg.battery, msg.profile))):
                        ## The experiment will be set to error
                        self.__write_exp_status(exp_status=CyclerDataExpStatusE.ERROR)
                    elif msg.cmd_type == MidStrDataCmdE.CS_STATUS:
                        ## The cycler station will be set to deprecated
                        self.deprecated_cs()
                    elif msg.cmd_type == MidStrDataCmdE.EXP_STATUS:
                        pass
                else:
                    if msg.cmd_type is MidStrDataCmdE.EXP_DATA:
                        self.experiment = msg.experiment
                        self.battery = msg.battery
                        self.profile = msg.profile
                    elif msg.cmd_type is MidStrDataCmdE.EXP_STATUS:
                        self.exp_status = msg.exp_status
                    elif msg.cmd_type is MidStrDataCmdE.CS_STATUS:
                        self.__deprecated: bool = msg.station_status
                        self.__wait_cs_reqst = False

    def request_cs_status(self) -> None:
        """
        Request the status of the CS by sending a request to the request channel.
        """
        log.debug("Checking CS status")
        request: MidStrCmdDataC = MidStrCmdDataC(cmd_type= MidStrReqCmdE.GET_CS_STATUS)
        self.__chan_str_reqs.send_data(request)
        self.__wait_cs_reqst = True

    def __fetch_new_exp(self) -> None:
        """AI is creating summary for fetch_new_exp

        Raises:
            ValueError: [description]

        Returns:
            Tuple[CyclerDataExperimentC, CyclerDataBatteryC, CyclerDataProfileC]: [description]
        """
        log.debug("Checking for new experiments")
        self.__iter = 0
        request: MidStrCmdDataC = MidStrCmdDataC(cmd_type= MidStrReqCmdE.GET_NEW_EXP)
        self.__chan_str_reqs.send_data(request)
        self.__wait_exp_reqst = True

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
        res = False
        if profile.range.no_voltage() and profile.range.no_current():
            log.debug("Profile no current neither voltages")
            res = True
        elif profile.range.no_current():
            log.debug("Profile no current")
            res = profile.range.in_range_voltage(battery.elec_ranges)
        elif profile.range.no_voltage():
            log.debug("Profile no voltage")
            res = profile.range.in_range_current(battery.elec_ranges)
        else:
            log.debug("Profile with current and voltage")
            res = (profile.range.in_range_current(battery.elec_ranges) and
                profile.range.in_range_voltage(battery.elec_ranges))
        log.critical(f"Validating experiment: {res}")
        return res

    def __write_exp_status(self, exp_status: CyclerDataExpStatusE) -> None:
        """Write the experiment status in the shared memory

        Args:
            exp_status (CyclerDataExpStatusE): Experiment status
        """
        request: MidStrCmdDataC = MidStrCmdDataC(cmd_type= MidStrReqCmdE.SET_EXP_STATUS,
                        exp_status= exp_status)
        self.__chan_str_reqs.send_data(request)

    def deprecated_cs(self):
        """Send a deprecated command to the str node to turn all experiments to error
        """
        request: MidStrCmdDataC = MidStrCmdDataC(cmd_type= MidStrReqCmdE.TURN_DEPRECATED)
        self.__chan_str_reqs.send_data(request)

    def __execute_experiment(self) -> None:
        """Execute the experiment
        """
        # First step is to update the local data in power
        self.pwr_control.update_local_data(self.local_gen_meas, self.local_all_status)
        self.exp_status, self.local_gen_meas.instr_id = self.pwr_control.process_iteration()
        self.__write_exp_status(self.exp_status)

    def execute_machine_status(self) -> None:
        """Execute the machine status
        """
        log.debug("Executing machine status")
        try:
            ## Process machine status
            if self.state == AppManCoreStatusE.GET_EXP:
                ## Wait for cs status to continue
                if ((not self.__wait_cs_reqst and not self.__wait_exp_reqst) or
                    self.__iter> _PERIOD_WAIT_EXP):
                    self.__fetch_new_exp()
                    self.request_cs_status()
                ## Check if the cycler station is deprecated
                if self.__deprecated:
                    log.critical("Cycler station is deprecated")
                    self.deprecated_cs()
                    self.state = AppManCoreStatusE.ERROR
                ## Wait for the experiment and check if the experiment is valid
                if not self.experiment is None and self.__wait_exp_reqst:
                    self.__iter = 0
                    log.debug("Experiment received, validating")
                    if not self.__validate_exp_ranges(self.battery, self.profile):
                        self.exp_status = CyclerDataExpStatusE.ERROR
                        self.__write_exp_status(self.exp_status)
                    else:
                        self.__wait_exp_reqst = False
                        self.state = AppManCoreStatusE.PREPARE_EXP
                elif self.__wait_exp_reqst:
                    self.__iter +=1
            elif self.state == AppManCoreStatusE.PREPARE_EXP:
                ## Set experiment to pwr control
                ## TODO: FUNCTION FOR ALARMS CALLBACK
                log.debug("Preparing experiment")
                self.pwr_control.set_new_experiment(instructions= self.profile.instructions,
                                                    bat_pwr_range= self.battery.elec_ranges)
                ## Check the instructions are the same in order
                ## to execute the correct experiment
                if self.pwr_control.all_instructions == self.profile.instructions:
                    self.state = AppManCoreStatusE.EXECUTE_EXP
            elif self.state == AppManCoreStatusE.EXECUTE_EXP:
                log.debug("Executing experiment")
                self.__execute_experiment()
                ## Check if the experiment has finish and try to get the next one
                log.critical(f"Experiment status: {self.exp_status}")
                if self.exp_status in (CyclerDataExpStatusE.FINISHED,
                                        CyclerDataExpStatusE.ERROR):
                    self.request_cs_status()
                    self.experiment = None
                    self.state = AppManCoreStatusE.GET_EXP
            else:
                log.debug("Error in machine status")
        except Exception as err:
            log.error(f"Error in machine status: {err}")
            self.state = AppManCoreStatusE.ERROR
