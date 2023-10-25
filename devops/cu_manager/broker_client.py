#!/usr/bin/python3
"""
Wrapper for the MQTT client
"""
#######################        MANDATORY IMPORTS         #######################

#######################         GENERIC IMPORTS          #######################
from typing import Callable, List
from pickle import dumps, loads

#######################       THIRD PARTY IMPORTS        #######################

#######################    SYSTEM ABSTRACTION IMPORTS    #######################
from system_logger_tool import sys_log_logger_get_module_logger, SysLogLoggerC, Logger

#######################       LOGGER CONFIGURATION       #######################
if __name__ == '__main__':
    cycler_logger = SysLogLoggerC(file_log_levels='../log_config.yaml')
log: Logger = sys_log_logger_get_module_logger(__name__)

#######################          PROJECT IMPORTS         #######################
from wattrex_battery_cycler_datatypes.comm_data  import CommDataCuC,\
    CommDataDeviceC,CommDataHeartbeatC

from wattrex_driver_mqtt import DrvMqttDriverC

#######################          MODULE IMPORTS          #######################
from detect import detect_devices

#######################              ENUMS               #######################

#######################             CLASSES              #######################

class BrokerClientC():
    """
    Broker Client Class to instanciate a Broker Client object
    """
    def __init__(self, error_callback : Callable, inform_reg_cb : Callable,
                 launch_callback : Callable, detect_callback : Callable,
                 cu_id_msg_callback : Callable) -> None:
        self.mqtt : DrvMqttDriverC = DrvMqttDriverC(error_callback=error_callback,
                                                    cred_path='.cred.yaml')
        self.__inform_reg_cb : Callable = inform_reg_cb
        self.__launch_cb : Callable = launch_callback
        self.__detect_cb : Callable = detect_callback
        self.cu_id = None
        self.mqtt.subscribe(topic='/inform_reg', callback=cu_id_msg_callback)


    def process_inform_reg(self, raw_data) -> None:
        if isinstance(raw_data, CommDataCuC):
            data : CommDataCuC = loads(raw_data)
            if data.msg_type is CommDataRegisterTypeE.DISCOVER:
                log.debug(f"Receiving {data.msg_type} from {data.hostname}")
                data.msg_type = CommDataRegisterTypeE.REQUEST
                new_raw_data = dumps(data)
                # TODO: answer only if the recieved mac is the same as the sent one
                self.publish_cu_info(new_raw_data)
            elif data.msg_type is CommDataRegisterTypeE.ACK:
                log.info(f"Device registered. CU_ID: {data.cu_id}")
                self.cu_id = data.cu_id
                self.__inform_reg_cb(data)
                # self.mqtt.unsubscribe(topic='/inform_reg') # TODO: add it on drv_mqtt
                self.mqtt.subscribe(topic=f'/{data.cu_id}/req_detect', callback=self.process_detect)
                self.mqtt.subscribe(topic=f'/{data.cu_id}/launch', callback=self.process_launch)
        else:
            log.error(f"Receiving {type(data)} instead of CommDataC")

    def process_launch(self, raw_data) -> None:
        cs_id : int = loads(raw_data)
        self.__launch_cb(cs_id)

    def process_detect(self) -> None:
        self.__detect_cb()

    def publish_devices(self, detected_devices : List[CommDataDeviceC]) -> None:
        raw_devs = dumps(detected_devices)
        self.mqtt.publish(topic=f'/{self.cu_id}/detected_dev', data=raw_devs)

    def publish_cu_info(self, cu_info : CommDataCuC) -> None:
        self.mqtt.publish(topic='/register', data=cu_info.to_json())

    def publish_heartbeat(self, hb : CommDataHeartbeatC) -> None:
        raw_data = dumps(hb)
        self.mqtt.publish(topic=f'/{self.cu_id}/heartbeat', data=raw_data)

    def process_iteration(self) -> None:
        self.mqtt.process_data()

#######################            FUNCTIONS             #######################
