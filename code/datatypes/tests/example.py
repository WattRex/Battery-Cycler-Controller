#!/usr/bin/python3
"""
Data used for communication protocol between cu and master nodes
"""
#######################        MANDATORY IMPORTS         #######################

#######################         GENERIC IMPORTS          #######################
from time import sleep
from pickle import dumps, loads

#######################       THIRD PARTY IMPORTS        #######################

#######################    SYSTEM ABSTRACTION IMPORTS    #######################
from system_logger_tool import sys_log_logger_get_module_logger, SysLogLoggerC, Logger

#######################       LOGGER CONFIGURATION       #######################
if __name__ == '__main__':
    cycler_logger = SysLogLoggerC(file_log_levels='./log_config.yaml')
log: Logger = sys_log_logger_get_module_logger(__name__)

#######################          MODULE IMPORTS          #######################
from comm_data import CommDataHeartbeatC

#######################          PROJECT IMPORTS         #######################
from wattrex_driver_mqtt import DrvMqttDriverC

#######################              ENUMS               #######################

#######################             CLASSES              #######################

#######################            FUNCTIONS             #######################
class EmulateCuC:

    def __init__(self, cu_id = 1) -> None:
        self.cu_id = cu_id
        self.mqtt = DrvMqttDriverC(error_callback=self.error_callback, cred_path='.cred.mqtt.yaml')

    def error_callback(self, data) -> None:
        log.error(f'Error in Broker Client: {data}')

    def run_heartbeat(self) -> None:
        hb_topic = f'/{self.cu_id}/heartbeat/'
        log.warning(f'Publishing heartbeat to {hb_topic}')
        hb = CommDataHeartbeatC(cu_id=self.cu_id)
        hb_dump = dumps(hb)
        while True:
            self.mqtt.publish(topic=hb_topic, data=hb_dump)
            sleep(1)


if __name__ == '__main__':
    em = EmulateCuC()
    em.run_heartbeat()
