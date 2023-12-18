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
from system_logger_tool import Logger, sys_log_logger_get_module_logger
log: Logger = sys_log_logger_get_module_logger(__name__)

#######################       THIRD PARTY IMPORTS        #######################

#######################          PROJECT IMPORTS         #######################
from system_config_tool import sys_conf_update_config_params

#######################          MODULE IMPORTS          #######################

######################             CONSTANTS              ######################
# For further information check out README.md
DEFAULT_CRED_FILEPATH : str = 'devops/.cred.yaml' # Max number of allowed message per chan
DEFAULT_SYNC_NODE_NAME: str = 'SYNC'
DEFAULT_COMP_UNIT: int = 1
DEFAULT_NODE_PERIOD: int = 200 # ms # Period of the node

CONSTANTS_NAMES = ('DEFAULT_CRED_FILEPATH','DEFAULT_SYNC_NODE_NAME', 'DEFAULT_COMP_UNIT',
                   'DEFAULT_NODE_PERIOD')
sys_conf_update_config_params(context=globals(),
                              constants_names=CONSTANTS_NAMES)
