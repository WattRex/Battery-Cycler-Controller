#!/usr/bin/python3
'''
Definition of MID DATA experiment related info.
'''
#######################        MANDATORY IMPORTS         #######################
from __future__ import annotations

#######################         GENERIC IMPORTS          #######################
from typing import List

#######################       THIRD PARTY IMPORTS        #######################
from enum import Enum
from datetime import datetime

#######################      SYSTEM ABSTRACTION IMPORTS  #######################
from system_logger_tool import sys_log_logger_get_module_logger
log = sys_log_logger_get_module_logger(__name__)


#######################          PROJECT IMPORTS         #######################

#######################          MODULE IMPORTS          #######################
#######################              ENUMS               #######################

class MidDataExpStatusE(Enum):
    '''
    Reachable states in an experiment.
    '''
    QUEUED      = "QUEUED"
    RUNNING     = "RUNNING"
    PAUSED      = "PAUSED"
    FINISHED    = "FINISHED"
    ERROR       = "ERROR"

class MidDataPwrModeE(Enum):
    '''
    Types of modes that can be applied to a instruction on an experiment.
    '''
    WAIT    = 0
    CV_MODE = 1
    CC_MODE = 2
    CP_MODE = 3
    DISABLE = 4

class MidDataPwrLimitE(Enum):
    '''
    Types of limits that can be applied to a instruction on an experiment.
    '''
    TIME    = 0
    VOLTAGE = 1
    CURRENT = 2
    POWER   = 3


#######################             CLASSES              #######################
class MidDataInstructionC:
    '''
    Instruction to applied on experiments.
    '''
    def __init__(self, instr_id: int| None= None, mode : MidDataPwrModeE| None= None,
                ref : int| None= None, limit_type : MidDataPwrLimitE| None= None,
                limit_ref : int| None= None):
        '''
        Initialize Instruction.

        Args:
            mode (MidDataPwrModeE): power mode applied (CV, CC, CP, etc)
            ref (int): reference applied on this power mode
            limit_type (MidDataPwrLimitE): limit that that triggers the end of
                this instruction
            limit_ref (int): limit reference to be reached to instruction completion
        '''
        self.instr_id : int| None= instr_id
        self.mode : MidDataPwrModeE| None = mode
        self.ref : int| None = ref
        self.limit_type : MidDataPwrLimitE| None = limit_type
        self.limit_ref : int| None = limit_ref


class MidDataExperimentC:
    '''
    Experiment relate information.
    '''
    def __init__(self, exp_id : int|None= None, name : str|None= None,
                date_begin : datetime|None= None, date_finish : datetime|None= None,
                status : MidDataExpStatusE|None= None):
        '''
        Initialize Experiment instance with the given parameters.

        Args:
            exp_id (int): experiment ID used to distinguish between experiments
            name (str): Name that the used given to the experiment
            date_begin (datetime): Date when the experiment started
            date_finish (datetime): Date when the experiment finished. If the
                experiment is not finished, this value is None
            status (MidDataExpStatusE): Current status of the experiment
        '''
        self.exp_id : int|None = exp_id
        self.name : str|None = name
        self.date_begin : datetime|None = date_begin
        self.date_finish : datetime|None = date_finish
        self.status : MidDataExpStatusE|None = status

class MidDataPwrRangeC:
    '''
    Power range that specify operational limits for voltage and current.
    '''
    def __init__(self, volt_max : int|None = None, volt_min : int|None = None,
                curr_max : int|None = None, curr_min : int|None = None):
        '''
        Initialize the class .

        Args:
            volt_max (int): [description]
            volt_min (int): [description]
            curr_max (int): [description]
            curr_min (int): [description]
        '''
        self.fill_voltage(volt_max, volt_min)
        self.fill_current(curr_max, curr_min)

    def fill_voltage(self, volt_max : int, volt_min : int) -> None:
        '''
        Fill voltage limits.

        Args:
            volt_max (int): Maximum voltage
            volt_min (int): Minimum voltage
        '''
        error_detected = True
        if volt_max is None and volt_min is None:
            error_detected = False
        elif volt_max is not None and volt_min is not None:
            if volt_max > volt_min:
                error_detected = False
        if error_detected:
            msg = "Invalid voltage range"
            log.error(msg)
            raise ValueError(msg)

        self.__volt_max = volt_max
        self.__volt_min = volt_min

    def fill_current(self, curr_max : int, curr_min : int) -> None:
        '''
        Fill current limits.

        Args:
            curr_max (int): Maximum current
            curr_min (int): Minimum current
        '''
        error_detected = True
        if curr_max is None and curr_min is None:
            error_detected = False
        elif curr_max is not None and curr_min is not None:
            if curr_max > curr_min:
                error_detected = False
        if error_detected:
            msg = "Invalid current range"
            log.error(msg)
            raise ValueError(msg)

        self.__curr_max = curr_max
        self.__curr_min = curr_min

    @property
    def curr_max(self) -> int|None:
        '''
        Get max current.

        Returns:
            int: Max Current
        '''
        return self.__curr_max

    @property
    def curr_min(self) -> int|None:
        '''
        Get min current.

        Returns:
            int: Min Current
        '''
        return self.__curr_min

    @property
    def volt_max(self) -> int|None:
        '''
        Get max voltage.

        Returns:
            int: Max Voltage
        '''
        return self.__volt_max

    @property
    def volt_min(self) -> int|None:
        '''
        Get min voltage.

        Returns:
            int: Min Voltage
        '''
        return self.__volt_min

    def in_range_voltage(self, aux_pwr_range: MidDataPwrRangeC) -> bool:
        '''
        Check if the actual instance is less or equal than the other instance.

        Args:
            other (MidDataPwrRangeC): Instance to compare with

        Returns:
            bool: True if the voltage values are inside values of the other
                instance, False otherwise
        '''
        res = False
        if (self.volt_max is not None and aux_pwr_range.volt_max is not None and
            self.volt_max <= aux_pwr_range.volt_max and self.volt_min >= aux_pwr_range.volt_min):
            res = True
        return res

    def in_range_current(self, aux_pwr_range: MidDataPwrRangeC) -> bool:
        '''
        Check if the actual instance is less or equal than the other instance.

        Args:
            other (MidDataPwrRangeC): Instance to compare with

        Returns:
            bool: True if the current values are inside values of the other
                instance, False otherwise
        '''
        res = False
        if (self.curr_max is not None and aux_pwr_range.curr_max is not None and
            self.curr_max <= aux_pwr_range.curr_max and self.curr_min >= aux_pwr_range.curr_min):
            res = True
        return res

class MidDataProfileC:
    '''
    The class of MidDataProfileC is a class that is used for the MIDDataProfileC .
    '''
    def __init__(self, name : str|None = None, power_range : MidDataPwrRangeC|None = None,
            instructions : List[MidDataInstructionC]|None = None):
        '''
        Initialize the class .

        '''
        self.name : str|None = name
        self.instructions : List[MidDataInstructionC]|None = instructions
        self.range : MidDataPwrRangeC|None = power_range


class MidDataAlarmC:
    """
    Alarm triggered to notify that an unexpected event has occurred
    during cycler operation.
    """
    def __init__(self, timestamp : datetime|None = None, code : int|None = None,
                value : int|None = None):
        '''
        Initialize Alarm instance with the raising timestamp and with the
        associated alarm code. It also contains the value that triggered the alarm.

        Args:
            timestamp (datetime): Timestamp when the alarm was raised
            code (int): Code of the alarm
            value (int): Value that triggered the alarm
        '''
        self.timestamp : datetime|None = timestamp
        self.code : int|None = code
        self.value : int|None = value
