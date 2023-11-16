#!/usr/bin/python3
"""
Data used for communication protocol between cu and master nodes
"""
#######################        MANDATORY IMPORTS         #######################
from __future__ import annotations

#######################         GENERIC IMPORTS          #######################
from datetime import datetime
from enum import Enum

#######################       THIRD PARTY IMPORTS        #######################

#######################    SYSTEM ABSTRACTION IMPORTS    #######################

#######################       LOGGER CONFIGURATION       #######################

#######################          MODULE IMPORTS          #######################

#######################          PROJECT IMPORTS         #######################

#######################              ENUMS               #######################
class CommDataRegisterTypeE(Enum):
    '''
    Define the message types allowed on protocol used to discover the cu_id of each node
    '''
    DISCOVER = 0
    OFFER = 1
    REQUEST = 2
    ACK = 3


class CommDataMnCmdTypeE(Enum):
    '''
    Define the message types allowed on protocol used to send commands among services of master node
    '''
    LAUNCH = 1
    INF_DEV = 2
    REQ_DETECT = 3


######################             CLASSES              #######################
class CommDataCuC:
    '''
    Class used to store data of a computational unit (CU).
    '''

    def __init__(self, msg_type : CommDataRegisterTypeE, mac : int, user : str,
            ip : str, port : int, hostname : str, cu_id : int = 0):
        # pylint: disable=too-many-arguments
        # pylint: disable=invalid-name
        '''
        Initialize the class with the computational unit (CU) data.

        Args:
            msg_type (CommDataRegisterTypeE): message type
            mac (int): mac of the CU
            user (str): user of the CU
            ip (str): ip of the CU
            port (int): not used
            hostname (str): hostname of the CU
            cu_id (int, optional): CU ID assigned to this CU. Defaults to None.
        '''
        self.msg_type = msg_type
        self.mac = mac
        self.user = user
        self.ip = ip # pylint: disable=invalid-name
        self.port = port
        self.hostname = hostname
        self.cu_id = cu_id

    def __str__(self) -> str:
        '''
        Return a string with the data of the CU.

        Returns:
            str: string with the data of the CU.
        '''
        return f'CU info: \nCU_ID: {self.cu_id}\nMAC: {self.mac}\nUser: {self.user}\n' + \
            f'Hostname: {self.hostname}\nIP: {self.ip}\nPort: {self.port}\nMsgType: {self.msg_type}'


class CommDataHeartbeatC:
    '''
    Class used to store data related with a heartbeat.
    '''

    def __init__(self, cu_id : int):
        '''
        Initialize the class with the heartbeat info.

        Args:
            cu_id (int): [description]
        '''
        self.cu_id = cu_id
        self.timestamp = datetime.utcnow()

    def __str__(self) -> str:
        '''
        Return a string with the data of the Heartbeat.

        Returns:
            str: string with the data of the Heartbeat.
        '''
        return f'Heartbeat info: \nCU_ID: {self.cu_id}\nTimestamp: {self.timestamp}'

class CommDataDeviceC:
    '''
    Class used to store data of a device.
    '''

    def __init__(self, cu_id : int, comp_dev_id : int, serial_number : int,
                link_name : str|int) -> None:
        '''
        Initialize the class with the device info.

        Args:
            cu_id (int): id of the CU
            comp_dev_id (int): ID of the compatible device
            serial_number (int): serial number of the device
            link_name (str): name of the link that the device is connected
        '''
        self.cu_id = cu_id
        self.comp_dev_id = comp_dev_id
        self.serial_number = serial_number
        self.link_name = link_name

    def __str__(self) -> str:
        '''
        Return a string with the data of the Device.

        Returns:
            str: string with the data of the Device.
        '''
        return f'Device info: \nCU_ID: {self.cu_id}\nComp_dev_id: {self.comp_dev_id}\n' + \
            f'SN: {self.serial_number}\nLink name: {self.link_name}'


class CommDataMnCmdDataC:
    '''
    Class used to store data of a command sent among sevices of master node.
    '''
    def __init__(self, cmd_type : CommDataMnCmdTypeE, cu_id : int, **kwargs) -> None:
        if isinstance(cmd_type, CommDataMnCmdTypeE):
            self.cmd_type = cmd_type
            self.cu_id = cu_id
            if cmd_type is CommDataMnCmdTypeE.LAUNCH:
                if 'cs_id' in kwargs:
                    self.cs_id = kwargs['cs_id']
                else:
                    raise ValueError('Missing argument cs_id')
            elif cmd_type is CommDataMnCmdTypeE.INF_DEV:
                if 'devices' in kwargs:
                    self.devices = kwargs['devices']
                else:
                    raise ValueError('Missing argument devices')
            elif cmd_type is CommDataMnCmdTypeE.REQ_DETECT:
                pass
        else:
            raise TypeError(f'cmd_type must be of type CommDataMnCmdTypeE, not {type(cmd_type)}')

#######################            FUNCTIONS             #######################
