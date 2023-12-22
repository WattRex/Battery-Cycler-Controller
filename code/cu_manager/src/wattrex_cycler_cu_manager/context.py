#!/usr/bin/python3
'''
This module manages the constants variables.
Those variables are used in the scripts inside the module and can be modified
in a config yaml file specified in the environment variable with name declared
in system_config_tool.
'''

#######################        MANDATORY IMPORTS         #######################
from __future__ import annotations
#######################         GENERIC IMPORTS          #######################

#######################      SYSTEM ABSTRACTION IMPORTS  #######################
from system_logger_tool import Logger, SysLogLoggerC, sys_log_logger_get_module_logger
if __name__ == "__main__":
    cycler_logger = SysLogLoggerC(file_log_levels='./log_config.yaml')
log: Logger = sys_log_logger_get_module_logger(__name__)

#######################       THIRD PARTY IMPORTS        #######################

#######################          PROJECT IMPORTS         #######################
from system_config_tool import sys_conf_update_config_params

#######################          MODULE IMPORTS          #######################

######################             CONSTANTS              ######################
# For further information check out README.md
DEFAULT_TX_CAN_NAME     : str = 'TX_CAN'            # Default tx_can system queue name
DEFAULT_TX_SCPI_NAME    : str = 'TX_SCPI'           # Default tx_scpi system queue name
DEFAULT_RX_CAN_NAME     : str = 'RX_CAN_QUEUE'      # Default rx_can system queue name
DEFAULT_DETECT_TIMEOUT  : int = 2                   # Default time to read asked devices answers
DEFAULT_DEV_PATH        : str = '/dev/wattrex/'     # Default path to the devices
DEFAULT_SCPI_QUEUE_PREFIX : str = 'DET_'             # Default prefix for the scpi queues
DEFAULT_CU_ID_PATH      : str = './config/cu_manager/.cu_id'
# Default path to credential file for rabbitmq
DEFAULT_CRED_PATH       : str = './config/.cred.yaml'

CONSTANTS_NAMES = ('DEFAULT_TX_CAN_NAME', 'DEFAULT_TX_SCPI_NAME',
                   'DEFAULT_RX_CAN_NAME', 'DEFAULT_DETECT_TIMEOUT',
                   'DEFAULT_DEV_PATH', 'DEFAULT_SCPI_QUEUE_PREFIX',
                   'DEFAULT_CU_ID_PATH', 'DEFAULT_CRED_PATH')

sys_conf_update_config_params(context=globals(),
                              constants_names=CONSTANTS_NAMES,
                              section='wattrex_cycler_cu_manager')