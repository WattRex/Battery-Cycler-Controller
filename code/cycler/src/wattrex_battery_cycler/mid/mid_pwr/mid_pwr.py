#!/usr/bin/python3
"""
This module will create instances of epc device in order to control
the device and request info from it.
"""
#######################        MANDATORY IMPORTS         #######################
from __future__ import annotations
from typing import List, Tuple, Callable
from enum import Enum
#######################         GENERIC IMPORTS          #######################
from time import time
#######################       THIRD PARTY IMPORTS        #######################

from system_logger_tool import SysLogLoggerC, sys_log_logger_get_module_logger, Logger
if __name__ == '__main__':
    cycler_logger = SysLogLoggerC(file_log_levels= 'log_config.yaml')
log: Logger = sys_log_logger_get_module_logger(__name__)

#######################          PROJECT IMPORTS         #######################
from wattrex_cycler_datatypes.cycler_data import (CyclerDataPwrRangeC, CyclerDataDeviceC, #pylint: disable= wrong-import-position
                        CyclerDataInstructionC, CyclerDataDeviceTypeE, CyclerDataPwrLimitE,
                        CyclerDataGenMeasC, CyclerDataPwrModeE, CyclerDataExpStatusE,
                        CyclerDataAlarmC, CyclerDataAllStatusC)

#######################          MODULE IMPORTS          #######################
from ..mid_dabs import MidDabsPwrDevC
#######################              ENUMS               #######################
class _MidPwrDirectionE(Enum):
    '''Enum to define the direction of the power flow.
    '''
    CHARGE      = 0
    DISCHARGE   = 1
    WAIT        = 2


#######################             CLASSES              #######################
class MidPwrControlC: #pylint: disable= too-many-instance-attributes
    '''Instanciates an object enable to measure.
    '''
    def __init__(self, alarm_callback: Callable, devices: list [CyclerDataDeviceC],
            battery_limits: CyclerDataPwrRangeC|None,
            instruction_set: List[CyclerDataInstructionC]|None) -> None:

        self.pwr_dev  : MidDabsPwrDevC = MidDabsPwrDevC(devices)
        self.pwr_limits: CyclerDataPwrRangeC|None = battery_limits
        self.all_instructions     : List[CyclerDataInstructionC]|None = instruction_set
        self.actual_inst       : CyclerDataInstructionC = CyclerDataInstructionC(instr_id= None,
                                                        mode= CyclerDataPwrModeE.DISABLE,
                                                        ref=0, limit_type= CyclerDataPwrLimitE.TIME,
                                                        limit_ref= 0)
        self.instr_init_time: int = 0
        self.local_gen_meas: CyclerDataGenMeasC = CyclerDataGenMeasC()
        self.local_status: CyclerDataAllStatusC = CyclerDataAllStatusC()
        self.__last_mode: CyclerDataPwrModeE = CyclerDataPwrModeE.WAIT
        self.__pwr_direction: _MidPwrDirectionE = _MidPwrDirectionE.WAIT
        self.__alarm_callback: Callable = alarm_callback

    def __check_security_limits(self) -> bool:
        """Checks if the measures are within the limits of the battery pwr limits .

        Returns:
            bool: [True if the measures are within the limits of the battery pwr limits,
                otherwise false]
        """
        sec_limits = True
        if ((self.local_gen_meas.voltage > self.pwr_limits.volt_max or
             self.local_gen_meas.voltage < self.pwr_limits.volt_min) or
            (self.local_gen_meas.current > self.pwr_limits.curr_max or
             self.local_gen_meas.current < self.pwr_limits.curr_min)):
            log.error((f"Local measures: {self.local_gen_meas.voltage}mV, "
                       f"{self.local_gen_meas.current}mA"))
            log.error(f"Voltage limits: {self.pwr_limits.volt_max}mV, {self.pwr_limits.volt_min}mV")
            log.error(f"Current limits: {self.pwr_limits.curr_max}mA, {self.pwr_limits.curr_min}mA")
            sec_limits = False
        return sec_limits

    def __check_instr_limits(self) -> bool:
        """Checks if the current instruction is in the appropriate way .
        Returns:
            bool: [Return True if the instruction is in the appropriate way otherwise False]
        """
        inst_limits = True
        if self.actual_inst.mode is not CyclerDataPwrModeE.CP_MODE:
            if self.actual_inst.limit_type is CyclerDataPwrLimitE.TIME:
                if self.actual_inst.limit_ref > (int(time())-self.instr_init_time):
                    inst_limits = False
            elif self.__pwr_direction is _MidPwrDirectionE.CHARGE:
                if (self.actual_inst.limit_type is CyclerDataPwrLimitE.VOLTAGE and
                        self.actual_inst.limit_ref < self.local_gen_meas.voltage):
                    inst_limits = False
                elif (self.actual_inst.limit_type is CyclerDataPwrLimitE.CURRENT and
                        self.actual_inst.limit_ref < self.local_gen_meas.current):
                    inst_limits = False
                elif (self.actual_inst.limit_type is CyclerDataPwrLimitE.POWER and
                        self.actual_inst.limit_ref < self.local_gen_meas.power):
                    inst_limits = False
            elif self.__pwr_direction is _MidPwrDirectionE.DISCHARGE:
                if (self.actual_inst.limit_type is CyclerDataPwrLimitE.VOLTAGE and
                        self.actual_inst.limit_ref > self.local_gen_meas.voltage):
                    inst_limits = False
                elif (self.actual_inst.limit_type is CyclerDataPwrLimitE.CURRENT and
                        self.actual_inst.limit_ref > self.local_gen_meas.current):
                    inst_limits = False
                elif (self.actual_inst.limit_type is CyclerDataPwrLimitE.POWER and
                        self.actual_inst.limit_ref > self.local_gen_meas.power):
                    inst_limits = False
        else:
            log.error("The CP mode is not valid without epc device")
            raise ValueError("The CP mode is not valid without epc device")
        return inst_limits

    def __get_pwr_direction(self) ->None:
        self.__pwr_direction = _MidPwrDirectionE.WAIT
        if (self.actual_inst.mode is CyclerDataPwrModeE.CC_MODE or
            self.actual_inst.mode is CyclerDataPwrModeE.CP_MODE):
            if self.actual_inst.ref >= 0:
                self.__pwr_direction = _MidPwrDirectionE.CHARGE
            else:
                self.__pwr_direction = _MidPwrDirectionE.DISCHARGE
        elif self.actual_inst.mode is CyclerDataPwrModeE.CV_MODE:
            if self.local_gen_meas.voltage < self.actual_inst.ref:
                self.__pwr_direction = _MidPwrDirectionE.CHARGE
            else:
                self.__pwr_direction = _MidPwrDirectionE.DISCHARGE

    def __apply_instruction(self) -> None:
        """Function to apply the instruction to the device
        """
        if self.actual_inst.instr_id is not None:
            if self.actual_inst.mode is CyclerDataPwrModeE.CV_MODE:
                self.pwr_dev.set_cv_mode(volt_ref= self.actual_inst.ref,
                        limit_type= self.actual_inst.limit_type,
                        limit_ref= self.actual_inst.limit_ref)
            elif self.actual_inst.mode is CyclerDataPwrModeE.CC_MODE:
                self.pwr_dev.set_cc_mode(current_ref= self.actual_inst.ref,
                                        limit_ref= self.actual_inst.limit_ref,
                                        limit_type= self.actual_inst.limit_type)
            elif self.actual_inst.mode is CyclerDataPwrModeE.CP_MODE:
                self.pwr_dev.set_cp_mode(self.actual_inst.ref,
                                        limit_type= self.actual_inst.limit_type,
                                        limit_ref = self.actual_inst.limit_ref)
            elif self.actual_inst.mode is CyclerDataPwrModeE.WAIT:
                self.pwr_dev.set_wait_mode(time_ref= self.actual_inst.ref)
            elif self.actual_inst.mode is CyclerDataPwrModeE.DISABLE:
                self.pwr_dev.disable()
            else:
                log.error("The mode is not valid")
                raise ValueError("The mode is not valid")
            self.__get_pwr_direction()

    def update_local_data(self, new_gen_meas: CyclerDataGenMeasC,
                           new_status: CyclerDataAllStatusC) -> None:
        """Function to update the local data with the given data

        Args:
            new_gen_meas (CyclerDataGenMeasC): [description]
        """
        self.local_gen_meas = new_gen_meas
        self.local_status = new_status

    def set_new_experiment(self, instructions: List[CyclerDataInstructionC],
                        bat_pwr_range: CyclerDataPwrRangeC) -> None:
        """Function to set a new experiment, it will clear the previous one
        adding the new instruction set and battery limits

        Args:
            instructions (List[CyclerDataInstructionC]): [description]
            bat_pwr_range (CyclerDataPwrRangeC): [description]
        """
        self.all_instructions = instructions
        self.actual_inst.instr_id = None
        self.pwr_limits = bat_pwr_range

    def process_iteration(self) -> Tuple[CyclerDataExpStatusE, int]: #pylint: disable= too-many-branches
        """Processes a single instruction .

        Returns:
            Tuple[CyclerDataExpStatusE, int]: [description]
        """
        status = CyclerDataExpStatusE.QUEUED
        # Check if the security limits are correct
        if self.__check_security_limits():
            # Clear differentiation if the experiment is done with epc or without
            if self.pwr_dev.device_type is CyclerDataDeviceTypeE.EPC:
                # The epc device always start in Disable mode,
                # no need to check if instruction is not loaded
                # When the epc goes back to disable means the last instruction is done
                if (self.local_status.pwr_mode is CyclerDataPwrModeE.DISABLE and
                    self.__last_mode is not CyclerDataPwrModeE.DISABLE):
                    # Check if there are more instructions to read
                    if len(self.all_instructions) > 0:
                        self.actual_inst = self.all_instructions.pop(0)
                        log.warning(f"New instruction: {self.actual_inst.__dict__}")
                        self.__apply_instruction()
                        self.__last_mode = CyclerDataPwrModeE.DISABLE
                        status = CyclerDataExpStatusE.RUNNING
                    else:
                        self.actual_inst.instr_id = None
                        status = CyclerDataExpStatusE.FINISHED
                elif (self.local_status.pwr_mode is not CyclerDataPwrModeE.DISABLE and
                    self.__last_mode is CyclerDataPwrModeE.DISABLE):
                    self.__last_mode = self.actual_inst.mode
                    status = CyclerDataExpStatusE.RUNNING
                else:
                    status = CyclerDataExpStatusE.RUNNING
            else:
                intrs_limits = False
                if self.actual_inst.instr_id > -1:
                    intrs_limits = self.__check_instr_limits()
                if not intrs_limits:
                    # if surpassed check if there is more instructions
                    if len(self.all_instructions) > 0:
                        self.actual_inst = self.all_instructions.pop(0)
                        self.__apply_instruction()
                        self.instr_init_time = int(time())
                    else:
                        status = CyclerDataExpStatusE.FINISHED
                else:
                    status = CyclerDataExpStatusE.RUNNING
        else:
            status = CyclerDataExpStatusE.ERROR
            # TODO: Add alarms callback #pylint: disable= fixme
            self.__alarm_callback(CyclerDataAlarmC(code= 0, value=0))
        return status, self.actual_inst.instr_id

    def close(self):
        """Close connection in serial with the device"""
        try:
            self.pwr_dev.close()
        except Exception as err:
            log.error(f"Error while closing device: {err}")
            raise Exception("Error while closing device") from err #pylint: disable= broad-exception-raised
