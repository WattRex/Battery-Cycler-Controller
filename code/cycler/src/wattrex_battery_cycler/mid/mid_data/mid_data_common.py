#!/usr/bin/python3
'''
Definition of MID DATA devices used on battery cycler.
'''
#######################        MANDATORY IMPORTS         #######################
from __future__ import annotations
#######################         GENERIC IMPORTS          #######################

#######################       THIRD PARTY IMPORTS        #######################

#######################      SYSTEM ABSTRACTION IMPORTS  #######################
from system_logger_tool import sys_log_logger_get_module_logger
log = sys_log_logger_get_module_logger(__name__)


#######################          PROJECT IMPORTS         #######################

#######################          MODULE IMPORTS          #######################
from .mid_data_experiment import MidDataPwrModeE
from .mid_data_devices import MidDataDeviceStatusC
#######################              ENUMS               #######################

#######################             CLASSES              #######################

class MidDataAllStatusC:
    '''
    Class that gather status of all used devices.
    '''

    def __init__(self):
        '''
        Intialize the instance with the given status.
        '''
        # Power device is the main device, the  status will be overwriten by the devices in use
        self.pwr_dev : MidDataDeviceStatusC| None = None
        self.pwr_mode : MidDataPwrModeE| None = None

class MidDataGenMeasC:
    '''
    Class used to store generic power measures.
    '''

    def __init__(self, voltage: int= 0,
                 current: int= 0, power: int= 0, instr_id: int|None = None) -> None:
        '''
        Initialize the instance with the given measures.

        Args:
            voltage (int): measured voltage in the battery
            current (int): instant current in the battery
            power (int): active power applied to the battery in a given instant
            timestamp (datetime): instante when the measures has been taken
        '''
        self.voltage : int = voltage
        self.current : int = current
        self.power : int = power
        self.instr_id : int|None = instr_id

class MidDataExtMeasC:
    '''
    Class used to store extended mesaures specified by the user.
    '''

    def __init__(self):
        '''
        Initialize the with the specified extended measures.
        '''
