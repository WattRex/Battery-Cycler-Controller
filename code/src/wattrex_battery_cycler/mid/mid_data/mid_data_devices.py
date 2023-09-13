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
    All the errors different from comm error will be interpreted as internal error.
    '''
    COMM_ERROR = -1
    OK = 0
    INTERNAL_ERROR = 1

class MidDataDeviceTypeE(Enum):
    '''
    Allowed power device types in the system.
    '''
    SOURCE      = "Source"
    BISOURCE    = "BiSource"
    LOAD        = "Load"
    METER       = "Meter"
    EPC         = 'Epc'
    SOURCE_LOAD = "Source-Load"
#######################             CLASSES              #######################

class MidDataDeviceStatusC:
    '''Handles status of the driver power.
    '''
    def __init__(self, error: int|MidDataDeviceStatusE, dev_id: int) -> None:
        self.dev_id: int= dev_id
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

class MidDataLinkConfCanC:
    """A class method that implements the MIDDataLinkConCanf class .
    """
    def __init__(self, can_id: int):
        self.can_id = can_id
class MidDataLinkConfSerialC:
    '''
    A class method that implements the MIDDataLinkConSerialf class .
    '''
    # pylint: disable=too-many-arguments
    def __init__(self,
                port: str, separator: str, baudrate: int, bytesize: int,
                parity: str,
                stopbits: int, timeout: float, write_timeout: float,
                inter_byte_timeout: float) -> None:
        # Translation between parity specified by user and parity understable by python serial
        if 'odd' in parity.lower():
            parity = 'O'
        elif 'even' in parity.lower():
            parity = 'E'
        elif 'none' in parity.lower():
            parity = 'N'
        elif 'mark' in parity.lower():
            parity = 'M'
        elif 'space' in parity.lower():
            parity = 'S'
        else:
            log.error("Wrong value for parity")
            raise ValueError("Wrong value for parity")
        self.port = port
        self.separator = separator
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.timeout = timeout
        self.write_timeout = write_timeout
        self.inter_byte_timeout = inter_byte_timeout

class MidDataDeviceC:
    '''
    A class method that implements the MIDDataDevice class .
    '''

    # pylint: disable=too-many-arguments
    def __init__(self, manufacturer : str, model : str, serial_number : str,
                device_type : MidDataDeviceTypeE, iface_name : str, mapping_names : Dict,
                link_configuration: MidDataLinkConfCanC|MidDataLinkConfSerialC) -> None:
        self.manufacturer : str = manufacturer
        self.model : str = model
        self.serial_number : str  = serial_number
        self.device_type : MidDataDeviceTypeE = device_type
        self.iface_name :str = iface_name
        self.mapping_names : Dict = mapping_names
        self.link_conf: MidDataLinkConfCanC|MidDataLinkConfSerialC = link_configuration
