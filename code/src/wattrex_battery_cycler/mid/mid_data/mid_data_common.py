#!/usr/bin/python3
'''
Definition of MID DATA devices used on battery cycler.
'''
#######################        MANDATORY IMPORTS         #######################
from __future__ import annotations

#######################         GENERIC IMPORTS          #######################
from datetime import datetime

#######################       THIRD PARTY IMPORTS        #######################

#######################      SYSTEM ABSTRACTION IMPORTS  #######################
from system_logger_tool import sys_log_logger_get_module_logger
log = sys_log_logger_get_module_logger(__name__)


#######################          PROJECT IMPORTS         #######################

#######################          MODULE IMPORTS          #######################
from .mid_data_experiment import MidDataPwrModeE
from .mid_data_devices import MidDataDeviveStatusC
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
        # One attribute for each device, all of them initialized to OK
        self.epc_status : MidDataDeviveStatusC = MidDataDeviveStatusC(0)
        self.source_status : MidDataDeviveStatusC = MidDataDeviveStatusC(0)
        self.load_status : MidDataDeviveStatusC = MidDataDeviveStatusC(0)
        self.bisource_status : MidDataDeviveStatusC = MidDataDeviveStatusC(0)
        self.meter_status : MidDataDeviveStatusC = MidDataDeviveStatusC(0)

class MidDataGenMeasC:
    '''
    Class used to store generic power measures.
    '''

    def __init__(self, voltage: int, current: int,
        power: int) -> None:
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

class MidDataExtMeasC:
    '''
    Class used to store extended mesaures specified by the user.
    '''

    def __init__(self):
        '''
        Initialize the with the specified extended measures.
        '''
        self.pwr_mode: MidDataPwrModeE
