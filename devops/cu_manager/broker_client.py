#!/usr/bin/python3
"""
Wrapper for the MQTT client
"""
#######################        MANDATORY IMPORTS         #######################

#######################         GENERIC IMPORTS          #######################
from typing import Callable, List
import json

#######################       THIRD PARTY IMPORTS        #######################

#######################    SYSTEM ABSTRACTION IMPORTS    #######################
from system_logger_tool import sys_log_logger_get_module_logger, SysLogLoggerC, Logger

#######################       LOGGER CONFIGURATION       #######################
if __name__ == '__main__':
    cycler_logger = SysLogLoggerC(file_log_levels='../log_config.yaml')
log: Logger = sys_log_logger_get_module_logger(__name__)

#######################          MODULE IMPORTS          #######################

#######################          PROJECT IMPORTS         #######################
import context
from mid.mid_data import MidDataDeviceC, MidDataCuC
from wattrex_driver_mqtt import DrvMqttDriverC

#######################              ENUMS               #######################

#######################             CLASSES              #######################

class BrokerClientC():
    """
    Broker Client Class to instanciate a Broker Client object
    """
    def __init__(self, error_callback : Callable,
                 launch_callback : Callable,
                 detect_callback : Callable,
                 cu_id_msg_callback : Callable) -> None:
        self.mqtt : DrvMqttDriverC = DrvMqttDriverC(error_callback=error_callback,
                                                    cred_path='.cred.yaml')
        self.__detect_cb : Callable = detect_callback
        self.__launch_cb : Callable = launch_callback
        self.mqtt.subscribe(topic='/cu_id_assigned', callback=cu_id_msg_callback)

    def process_launch(self) -> None:
        pass

    def precess_detect(self) -> None:
        pass

    def publish_devices(self, detected_devices : List[MidDataDeviceC]) -> None:
        pass

    def publish_cu_info(self, cu_info : MidDataCuC) -> None:
        self.mqtt.publish(topic='/register', data=cu_info.to_json())

    def publish_heartbeat(self) -> None:
        pass

    def process_iteration(self) -> None:
        pass
    

#######################            FUNCTIONS             #######################
