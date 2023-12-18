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
from wattrex_cycler_datatypes.comm_data  import CommDataCuC,\
    CommDataDeviceC,CommDataHeartbeatC, CommDataRegisterTypeE

from wattrex_driver_mqtt import DrvMqttDriverC

#######################          MODULE IMPORTS          #######################

#######################              ENUMS               #######################
_REGISTER_TOPIC = '/register'
_INFORM_TOPIC = '/inform_reg'
_SUFFIX_TX_DET_DEV = '/detected_dev'
_SUFFIX_TX_HB = '/heartbeat'
_SUFFIX_RX_DET = '/req_detect'
_SUFFIX_RX_LAUNCH = '/launch'



#######################             CLASSES              #######################

class BrokerClientC():
    """
    Broker Client Class to instanciate a Broker Client object
    """
    def __init__(self, error_callback : Callable, launch_callback : Callable,\
                detect_callback : Callable, store_cu_info_cb : Callable) -> None:
        self.mqtt : DrvMqttDriverC = DrvMqttDriverC(error_callback=error_callback,
                                                    cred_path='./devops/.cred.yaml')
        self.__launch_cb : Callable = launch_callback
        self.__detect_cb : Callable = detect_callback
        self.__store_cu_info_cb : Callable = store_cu_info_cb
        self.cu_id = None
        self.mac : int = None


    def __store_mac(self, mac : int) -> None:
        '''
        Store the MAC address of the CU

        Args:
            mac (int): MAC address
        '''
        if self.mac is None:
            self.mac = mac


    def subscribe_cu(self, cu_id : int, mac : int) -> None:
        '''
        Subscribe to the topics of the CU

        Args:
            cu_id (int): CU ID
        '''
        self.__store_mac(mac)
        self.cu_id = cu_id
        self.mqtt.subscribe(topic=f'/{cu_id}{_SUFFIX_RX_DET}', callback=self.process_det_dev)
        self.mqtt.subscribe(topic=f'/{cu_id}{_SUFFIX_RX_LAUNCH}', callback=self.process_launch)


    def process_inform_reg(self, raw_data : bytearray) -> None:
        '''
        Process the registration answer from MQTT Broker

        Args:
            raw_data (bytearray): Raw data received
        '''
        data : CommDataCuC = loads(raw_data)
        if isinstance(data, CommDataCuC):
            if data.msg_type is CommDataRegisterTypeE.OFFER:
                log.info(f"Receiving {data.msg_type.name} for "
                         + f"[host: {data.hostname}, mac: {data.mac}], cu_id: {data.cu_id}")
                if data.mac == self.mac:
                    data.msg_type = CommDataRegisterTypeE.REQUEST
                    self.publish_cu_info(data)
            elif data.msg_type is CommDataRegisterTypeE.ACK and data.mac == self.mac:
                log.info(f"Received {data.msg_type.name}. Device registered. CU_ID: {data.cu_id}")
                self.subscribe_cu(data.cu_id, self.mac)
                self.__store_cu_info_cb(data)
                self.mqtt.unsubscribe(topic='/inform_reg')
        else:
            log.error(f"Receiving {type(data)} instead of CommDataC")


    def publish_cu_info(self, cu_info : CommDataCuC) -> None:
        '''
        Publish the CU info to the MQTT Broker
        '''
        if self.mac is None:
            self.mac = cu_info.mac
            self.mqtt.subscribe(topic=_INFORM_TOPIC, callback=self.process_inform_reg)
        log.info(f"Send {cu_info.msg_type.name} msg with mac: {cu_info.mac}")
        raw_data = dumps(cu_info)
        self.mqtt.publish(topic=_REGISTER_TOPIC, data=raw_data)


    def process_launch(self, raw_data : bytearray) -> None:
        '''
        Process the launch request from MQTT Broker

        Args:
            raw_data (bytearray): Raw data received
        '''
        log.info(f"Received launch request from {raw_data}")
        cs_id : int = int(raw_data)
        self.__launch_cb(cs_id)


    def process_det_dev(self, raw_data : bytearray) -> None:
        '''
        Process the device detection request from MQTT Broker

        Args:
            raw_data (bytearray): Raw data received (Not used)
        '''
        log.info("Received device detection request")
        log.debug(f"Raw data received from device detection request : {raw_data}")
        self.__detect_cb()


    def publish_dev(self, devices : List[CommDataDeviceC]) -> None:
        '''
        Publish the detected devices to the MQTT Broker

        Args:
            devices (List[CommDataDeviceC]): List of detected devices
        '''
        raw_devs = dumps(devices)
        log.critical(f"Publishing detected devices: {raw_devs} on CU: {self.cu_id}")
        self.mqtt.publish(topic=f'/{self.cu_id}{_SUFFIX_TX_DET_DEV}', data=raw_devs)


    def publish_heartbeat(self, heartbeat : CommDataHeartbeatC) -> None:
        '''
        Publish the heartbeat to the MQTT Broker

        Args:
            hb (CommDataHeartbeatC): Heartbeat to publish
        '''
        raw_data = dumps(heartbeat)
        self.mqtt.publish(topic=f'/{self.cu_id}{_SUFFIX_TX_HB}', data=raw_data)


    def process_iteration(self) -> None:
        '''
        Process the MQTT Broker data
        '''
        self.mqtt.process_data()


    def close(self) -> None:
        '''
        Close the broker client.
        '''
        self.mqtt.close()

#######################            FUNCTIONS             #######################
