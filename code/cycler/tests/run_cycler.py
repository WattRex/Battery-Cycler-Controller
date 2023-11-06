#!/usr/bin/python3
"""
This file test mid_dabs and show how it works.
"""

#######################        MANDATORY IMPORTS         #######################
import os
import sys
from subprocess import run, PIPE

#######################         GENERIC IMPORTS          #######################
from threading import Event
from time import sleep
#######################      SYSTEM ABSTRACTION IMPORTS  #######################
from system_logger_tool import Logger, SysLogLoggerC, sys_log_logger_get_module_logger
main_logger = SysLogLoggerC(file_log_levels="devops/log_config.yaml")
log: Logger = sys_log_logger_get_module_logger(name="run_cycler")

#######################       THIRD PARTY IMPORTS        #######################
from can_sniffer import DrvCanNodeC
# from scpi_sniffer import DrvScpiHandlerC
#######################          MODULE IMPORTS          #######################
sys.path.append(os.getcwd()+'/code/cycler/')
from src.wattrex_battery_cycler.app.app_man import AppManNodeC

if __name__ == "__main__":
    working_can: Event= Event()
    manager: AppManNodeC = AppManNodeC(cs_id= 1, cycle_period= 1000)
    try:
        run(["sudo", "ip", "link", "set", "up", "txqueuelen", "100000", "can0", "type", "can",
            "bitrate", "125000",], stdout=PIPE, stderr=PIPE)
        can: DrvCanNodeC = DrvCanNodeC(tx_buffer_size= 200, cycle_period= 30,
                                       working_flag= working_can)
        can.start()
        sleep(1)
        manager.run()
    except KeyboardInterrupt:

        manager.stop()
        sleep(1)
        working_can.clear()
        sleep(1)
        run(["sudo", "ip", "link", "set", "down", "can0"], stdout=PIPE, stderr=PIPE)
