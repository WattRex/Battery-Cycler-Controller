#!/usr/bin/python3
'''
Definition of MID DATA devices used on battery cycler.
'''
#######################        MANDATORY IMPORTS         #######################
from __future__ import annotations

#######################         GENERIC IMPORTS          #######################
from typing import Dict

#######################       THIRD PARTY IMPORTS        #######################
from enum import Enum

#######################      SYSTEM ABSTRACTION IMPORTS  #######################
from system_logger_tool import sys_log_logger_get_module_logger
log = sys_log_logger_get_module_logger(__name__)


#######################          PROJECT IMPORTS         #######################

#######################          MODULE IMPORTS          #######################


#######################              ENUMS               #######################
class MidDataDeviceStatusE(Enum):
    '''
    Device status types.
    '''
    COMM_ERROR = -1
    OK = 0
    INTERNAL_ERROR = 1

class MidDataDeviceTypeE(Enum):
    '''
    Allowed power device types in the system.
    '''
    SOURCE = "Source"
    BISOURCE = "BiSource"
    LOAD = "Load"
    METER = "Meter"

#######################             CLASSES              #######################

class MidDataDeviveStatusC:
    '''Handles status of the driver power.
    '''
    def __init__(self, error: int|MidDataDeviceStatusE) -> None:
        if isinstance(error, MidDataDeviceStatusE):
            self.__status = error
            self.__error_code = error.value
        else:
            self.__error_code = error
            if error > 0:
                self.__status = MidDataDeviceStatusE.INTERNAL_ERROR
            else:
                self.__status = MidDataDeviceStatusE(error)

    def __str__(self) -> str:
        result = f"Error code: {self.__error_code} \t Status: {self.__status}"
        return result

    def __eq__(self, cmp_obj: Enum) -> bool:
        return self.__status == cmp_obj

    @property
    def error_code(self) -> int:
        '''The error code associated with this request .
        Args:
            - None
        Returns:
            - (int): The error code associated with this request.
        Raises:
            - None
        '''
        return self.__error_code

    @property
    def value(self) -> int:
        ''' Value of status.
        Args:
            - None
        Returns:
            - (int): Value of status.
        Raises:
            - None
        '''
        return self.__status.value

    @property
    def name(self) -> str:
        ''' Name of status.
        Args:
            - None
        Returns:
            - (int): name of status.
        Raises:
            - None
        '''
        return self.__status.name

class MidDataDeviceC:
    '''
    A class method that implements the MIDDataDevice class .
    '''

    # pylint: disable=too-many-arguments
    def __init__(self, manufacturer : str, model : str, serial_number : str,
                device_type : MidDataDeviceTypeE, iface_name : str, mapping_names : Dict) -> None:
        self.manufacturer : str = manufacturer
        self.model : str = model
        self.serial_number : str  = serial_number
        self.device_type : MidDataDeviceTypeE = device_type
        self.iface_name :str = iface_name
        self.mapping_names : Dict = mapping_names
