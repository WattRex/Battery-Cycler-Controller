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

DEFAULT_PERIOD_CYCLE_MAN: int   = 800 # Express in milliseconds
DEFAULT_CS_MNG_NODE_NAME: str   = 'MANAGER'
DEFAULT_PERIOD_WAIT_EXP: int    = 10 # Periods of the cycle manager


CONSTANTS_NAMES = ('DEFAULT_PERIOD_CYCLE_MAN', 'DEFAULT_CS_MNG_NODE_NAME',
                   'DEFAULT_PERIOD_WAIT_EXP')
sys_conf_update_config_params(context=globals(),
                              constants_names=CONSTANTS_NAMES)
