#!/usr/bin/python3
"""
Script that gather info from system used to register de computational unit
"""
#######################        MANDATORY IMPORTS         #######################

#######################         GENERIC IMPORTS          #######################
from os import getenv
from uuid import getnode
from socket import socket, AF_INET, SOCK_DGRAM, gethostname

#######################       THIRD PARTY IMPORTS        #######################

#######################    SYSTEM ABSTRACTION IMPORTS    #######################
from system_logger_tool import sys_log_logger_get_module_logger, SysLogLoggerC, Logger

#######################       LOGGER CONFIGURATION       #######################
if __name__ == '__main__':
    cycler_logger = SysLogLoggerC(file_log_levels='./log_config.yaml')
log: Logger = sys_log_logger_get_module_logger(__name__)

#######################          PROJECT IMPORTS         #######################
from wattrex_cycler_datatypes.comm_data import CommDataCuC, CommDataRegisterTypeE

#######################          MODULE IMPORTS          #######################

#######################              ENUMS               #######################

#######################             CLASSES              #######################

#######################            FUNCTIONS             #######################

def get_cu_info() -> CommDataCuC:
    """
    Function that gather info from system used to register the computational unit
    """
    cu_info = CommDataCuC(msg_type=CommDataRegisterTypeE.DISCOVER,\
        mac=getnode(), user=getenv('USER', ''), ip=__get_local_ip(),\
        port=22, hostname=gethostname())

    return cu_info


def __get_local_ip() -> str:
    """
    Function that returns the local ip
    """
    s = socket(AF_INET, SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('192.255.255.255', 1))
        ip_address = s.getsockname()[0]
    except Exception as exc:
        log.debug(exc)
        ip_address = '127.0.0.1'
    finally:
        s.close()
    return ip_address


if __name__ == "__main__":
    log.info(get_cu_info())
