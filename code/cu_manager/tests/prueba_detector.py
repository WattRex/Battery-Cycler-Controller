#!/usr/bin/python3
from os import getenv
from time import sleep
from threading import Event

from system_logger_tool import Logger, SysLogLoggerC, sys_log_logger_get_module_logger
if __name__ == '__main__':
    cycler_logger = SysLogLoggerC(file_log_levels='./devops/log_config.yaml',
                                  output_sub_folder='detector')
log: Logger = sys_log_logger_get_module_logger(__name__)

from dev_detector import DetectorC
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
for ea in detector.det_ea:
    log.info(f"Detected bms: {ea.link_name}")
