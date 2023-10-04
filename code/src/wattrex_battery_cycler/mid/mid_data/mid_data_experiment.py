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
        if ((volt_max is None and
             (volt_min is not None or curr_max is not None or curr_min is not None))
            or (volt_min is None and
            (curr_max is not None or curr_min is not None or volt_max is not None))
            or (curr_max is None and
            (curr_min is not None or volt_max is not None or volt_min is not None))
            or (curr_min is None and
            (volt_max is not None or volt_min is not None or curr_max is not None))):
            log.error("Invalid power range")
            raise ValueError("Invalid power range")
        elif (volt_max is not None and volt_min is not None and volt_max < volt_min):
            log.error("Invalid voltage range")
            raise ValueError("Invalid power range")
        elif (curr_max is not None and curr_min is not None and curr_max < curr_min):
            log.error("Invalid current range")
            raise ValueError("Invalid power range")
        self.volt_max : int|None = volt_max
        self.volt_min : int|None = volt_min
        self.curr_max : int|None = curr_max
        self.curr_min : int|None = curr_min

    def in_range(self, other) -> bool:
        '''
        Check if the current instance is less or equal than the other instance.

        Args:
            other (MidDataPwrRangeC): Instance to compare with

        Returns:
            bool: True if the current values are inside values of the other
                instance, False otherwise
        '''
        res = False
        if (self.volt_max <= other.volt_max and self.volt_min >= other.volt_min and
            self.curr_max <= other.curr_max and self.curr_min >= other.curr_min):
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
