#!/usr/bin/python3
"""
This file test mid_dabs and show how it works.
"""

#######################        MANDATORY IMPORTS         #######################
import os
import sys

#######################         GENERIC IMPORTS          #######################
from time import sleep
#######################      SYSTEM ABSTRACTION IMPORTS  #######################
from system_logger_tool import Logger, SysLogLoggerC, sys_log_logger_get_module_logger
main_logger = SysLogLoggerC(file_log_levels="devops/log_config.yaml")
log: Logger = sys_log_logger_get_module_logger(name="run_cycler")

#######################       THIRD PARTY IMPORTS        #######################
#######################          MODULE IMPORTS          #######################
sys.path.append(os.getcwd()+'/code/cycler/')
from src.wattrex_battery_cycler.app.app_man import AppManNodeC

if __name__ == "__main__":
    manager: AppManNodeC = AppManNodeC(cs_id= 1, cycle_period= 1000)
    try:
        sleep(1)
        manager.run()
    except KeyboardInterrupt:

        manager.stop()
        sleep(1)
