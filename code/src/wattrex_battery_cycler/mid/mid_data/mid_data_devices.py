#!/usr/bin/python3
'''
Definition of MID DATA devices used on battery cycler.
'''
#######################        MANDATORY IMPORTS         #######################
from __future__ import annotations

#######################         GENERIC IMPORTS          #######################
from typing import Dict, List

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

class MidDataLinkConfC: #pylint: disable=too-many-instance-attributes
    '''
    A class method that implements the MIDDataLinkConf class .
    '''
    # pylint: disable=too-many-arguments
    def __init__(self, **kargs) -> None:
        """Constructor of the class, the attributes will be initialized while running
        """
        accepted_attributes = {'baudrate': int, 'parity': str, 'stopbits': int , 'bytesize': int,
            'timeout':float, 'write_timeout': float, 'inter_byte_timeout':float, 'separator':str}
        for key, value in kargs.items():
            key = key.lower()
            if key in accepted_attributes:
                if not  isinstance(value, accepted_attributes[key]):
                    value = accepted_attributes[key](value)
                if key == 'parity':
                    value = value.lower()
                    if 'odd' in value:
                        value = 'O'
                    elif 'even' in value:
                        value = 'E'
                    elif 'none' in value:
                        value = 'N'
                    elif 'mark' in value:
                        value = 'M'
                    elif 'space' in value:
                        value = 'S'
                    else:
                        log.error("Wrong value for parity")
                        raise ValueError("Wrong value for parity")
                if  key == 'separator' and value =='\\n':
                    value = '\n'
                setattr(self, key, value)

class MidDataDeviceC: # pylint: disable=too-many-instance-attributes
    '''
    A class method that implements the MIDDataDevice class .
    '''

    # pylint: disable=too-many-arguments
    def __init__(self, dev_id: int|None = None, manufacturer : str| None= None,
                model :str| None= None, serial_number : str| None= None,
                device_type : MidDataDeviceTypeE| None= None, iface_name : str| None= None,
                mapping_names : Dict| None= None,
                link_configuration: MidDataLinkConfC|None = None) -> None:
        """Initialize the attributes of the device .

        Args:
            manufacturer (str, optional): [description]. Defaults to None.
            model (str, optional): [description]. Defaults to None.
            serial_number (str, optional): [description]. Defaults to None.
            device_type (MidDataDeviceTypeE, optional): [description]. Defaults to None.
            iface_name (str, optional): [Name needed to communicate,in case of serial will be the
              port while in can will be the can id]. Defaults to None.
            mapping_names (Dict, optional): [description]. Defaults to None.
            link_configuration (MidDataLinkConfSerialC, optional): [description]. Defaults to None.
        """
        ## Check if is initialized to none
        if device_type is not None:
            device_type = MidDataDeviceTypeE(device_type)
        self.dev_id : int|None = dev_id
        self.manufacturer : str| None= manufacturer
        self.model : str| None = model
        self.serial_number : str| None = serial_number
        self.device_type : MidDataDeviceTypeE|None = device_type
        self.iface_name :str| None = iface_name
        self.mapping_names : Dict| None = mapping_names
        self.link_conf: MidDataLinkConfC|None = link_configuration

class MidDataCyclerStationC:
    '''
    Cycler station information.
    '''
    def __init__(self, cs_id: int| None= None, name: str| None= None,
                devices: List[MidDataDeviceC]| None= None, deprecated: bool|None = None):
        '''
        Initialize CyclerStation instance with the given parameters.

        Args:
            name (str): Name of the cycler station
            cs_id (str): ID of the cycler station
            devices (List[MidDataDeviceC]): List of devices included in the cycler station
            deprecated (bool, optional): Flag that indicates if the cycler station is deprecated
        '''
        self.name : str| None = name
        self.cs_id : int| None = cs_id
        self.devices : List[MidDataDeviceC]| None = devices
        self.deprecated: bool|None = deprecated
