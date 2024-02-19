#!/usr/bin/python3
"""
This script is used to test the functionality of the DetectorC class 
in the wattrex_battery_cycler_cu_manager module.
It initializes a DetectorC object with a cu_id of 69 and calls the 
process_detection() method to detect EPCs, BMSs, and EAs.
The detected EPCs, BMSs, and EAs are logged using the Logger 
class from the system_logger_tool module.
"""
import sys
import os
# from os import getenv
# from time import sleep
# from threading import Event

from system_logger_tool import Logger, SysLogLoggerC, sys_log_logger_get_module_logger
if __name__ == '__main__':
    cycler_logger = SysLogLoggerC(file_log_levels='./devops/log_config.yaml',
                                  output_sub_folder='detector')
log: Logger = sys_log_logger_get_module_logger(__name__)

sys.path.append(os.getcwd()+'/code/cu_manager/')
from src.wattrex_cycler_cu_manager.detect import DetectorC
# from can_sniffer import DrvCanNodeC

# can_working_flag = Event()
# can_working_flag.set()
# can = DrvCanNodeC(tx_buffer_size= 100, working_flag = can_working_flag,
#                     cycle_period= 50)
# can.start()
# sleep(2)
detector = DetectorC(cu_id=69)
detector.process_detection()
for epc in detector.det_epc:
    log.info(f"Detected epc: {epc.link_name}")
for bms in detector.det_bms:
    log.info(f"Detected bms: {bms.link_name}")
for ea in detector.det_source:
    log.info(f"Detected ea: {ea.link_name}")
for load in detector.det_load:
    log.info(f"Detected load: {load.link_name}")
for bisource in detector.det_bisource:
    log.info(f"Detected bisource: {bisource.link_name}")
