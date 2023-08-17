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
    def __init__(self, mode : MidDataPwrModeE, ref : int,
                limit_type : MidDataPwrLimitE, limit_ref : int):
        '''
        Initialize Instruction.

        Args:
            mode (MidDataPwrModeE): power mode applied (CV, CC, CP, etc)
            ref (int): reference applied on this power mode
            limit_type (MidDataPwrLimitE): limit that that triggers the end of
                this instruction
            limit_ref (int): limit reference to be reached to instruction completion
        '''
        self.mode : MidDataPwrModeE = mode
        self.ref : int = ref
        self.limit_type : MidDataPwrLimitE = limit_type
        self.limit_ref : int = limit_ref


class MidDataExperimentC:
    '''
    Experiment relate information.
    '''
    def __init__(self, exp_id : int, name : str, date_begin : datetime,
                date_finish : datetime, status : MidDataExpStatusE):
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
        self.exp_id : int = exp_id
        self.name : str = name
        self.date_begin : datetime = date_begin
        self.date_finish : datetime = date_finish
        self.status : MidDataExpStatusE = status

class MidDataPwrRangeC:
    '''
    Power range that specify operational limits for voltage and current.
    '''
    def __init__(self, volt_max : int, volt_min : int, curr_max : int,
                curr_min : int):
        '''
        Initialize the class .

        Args:
            volt_max (int): [description]
            volt_min (int): [description]
            curr_max (int): [description]
            curr_min (int): [description]
        '''
        self.volt_max : int = volt_max
        self.volt_min : int = volt_min
        self.curr_max : int = curr_max
        self.curr_min : int = curr_min


class MidDataProfileC:
    '''
    The class of MidDataProfileC is a class that is used for the MIDDataProfileC .
    '''
    def __init__(self, name : str, power_range : MidDataPwrRangeC,
            instructions : List[MidDataInstructionC]):
        '''
        Initialize the class .

        '''
        self.name : str = name
        self.instructions : List[MidDataInstructionC] = instructions
        self.range : MidDataPwrRangeC = power_range


class MidDataAlarmC:
    """
    Alarm triggered to notify that an unexpected event has occurred
    during cycler operation.
    """
    def __init__(self, timestamp : datetime, code : int, value : int):
        '''
        Initialize Alarm instance with the raising timestamp and with the
        associated alarm code. It also contains the value that triggered the alarm.

        Args:
            timestamp (datetime): Timestamp when the alarm was raised
            code (int): Code of the alarm
            value (int): Value that triggered the alarm
        '''
        self.timestamp : datetime = timestamp
        self.code : int = code
        self.value : int = value
