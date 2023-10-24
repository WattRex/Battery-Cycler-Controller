#!/usr/bin/python3
"""
Data used for communication protocol between cu and master nodes
"""
#######################        MANDATORY IMPORTS         #######################

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


#######################             CLASSES              #######################
class CommDataCuC:
    '''
    Class used to store data of a computational unit (CU).
    '''

    def __init__(self, msg_type : CommDataRegisterTypeE, mac : int, user : str,
            ip : str, port : int, hostname : str, cu_id : int = None):
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

class CommDataDeviceC:
    '''
    Class used to store data of a device.
    '''

    def __init__(self, cu_id : int, comp_dev_id : int, serial_number : int,
                link_name : int) -> None:
        '''
        Initialize the class with the device info.

        Args:
            cu_id (int): id of the CU
            comp_dev_id (int): ID of the compatible device
            serial_number (int): serial number of the device
            link_name (int): name of the link that the device is connected
        '''
        self.cu_id = cu_id
        self.comp_dev_id = comp_dev_id
        self.serial_number = serial_number
        self.link_name = link_name

#######################            FUNCTIONS             #######################
