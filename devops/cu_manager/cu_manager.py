#!/usr/bin/python3
"""
Cu Manager
"""
#######################        MANDATORY IMPORTS         #######################

#######################         GENERIC IMPORTS          #######################
from datetime import datetime
import json
from os import path
import subprocess
from time import sleep
import threading
from typing import List, Dict

#######################       THIRD PARTY IMPORTS        #######################

#######################    SYSTEM ABSTRACTION IMPORTS    #######################
from system_logger_tool import sys_log_logger_get_module_logger, SysLogLoggerC, Logger

#######################       LOGGER CONFIGURATION       #######################
if __name__ == '__main__':
    cycler_logger = SysLogLoggerC(file_log_levels='./log_config.yaml')
log: Logger = sys_log_logger_get_module_logger(__name__)

#######################          MODULE IMPORTS          #######################
import context
from broker_client import BrokerClientC
from register import get_cu_info

#######################          PROJECT IMPORTS         #######################
from comm_data import CommDataCuC
from system_shared_tool import SysShdIpcChanC, SysShdNodeC

#######################              ENUMS               #######################

#######################             CLASSES              #######################

class CuManagerNodeC(SysShdNodeC):
    """
    Cu Manager Class to instanciate a CU Manager Node
    """
    def __init__(self, working_flag : threading.Event, cycle_period : int) -> None:
        ''' Initialize the node.
        '''
        super().__init__(name='cu_manager_node', cycle_period=cycle_period, working_flag=working_flag)
        self.heartbeat_queue : SysShdIpcChanC = SysShdIpcChanC(name='heartbeat_queue')
        self.active_cs : Dict[int, datetime] = {} # {cs_id : last_connection}
        self.client_mqtt : BrokerClientC = BrokerClientC(error_callback=self.on_mqtt_error,
                                                         inform_reg_cb=self.inform_reg_cb
                                                         launch_callback=self.launch_cs,
                                                         detect_callback=self.detect_devices,
                                                         cu_id_msg_callback=self.on_register_answer)
        # self.sync_node : MidSyncNoceC = MidSyncNoceC()
        self.working_flag_sync : threading.Event = threading.Event()
        self.working_flag_sync.set()

        self.working_flag = working_flag
        self.cycle_period : int = cycle_period

        self.cu_id = None
        if path.exists('./devops/cu_manager/.cu_id'):
            with open('./devops/cu_manager/.cu_id', 'r', encoding='utf-8') as cu_id_file:
                self.cu_id = int(cu_id_file.read())
        else:
            self.registered = threading.Event()
            self.registered.clear()
            self.register_cu()

    def on_mqtt_error(self) -> None:
        '''
        Callback function executed from the Broker Client when an error is detected
        '''
        log.critical('MQTT Error')
        # TODO: implement error handling

    def process_heartbeat(self) -> None:
        pass

    def __gather_heartbeat(self) -> None:
        pass

    def register_cu(self) -> None:
        '''
        Register the CU in the broker to get from it an id.
        '''
        cu_info = get_cu_info()
        self.client_mqtt.publish_cu_info(cu_info())

        while not self.registered.is_set():
            self.client_mqtt.process_iteration()
            sleep(0.1)


    def inform_reg_cb(self, data) -> None:
        if isinstance(data, CommDataCuC):
            self.cu_id = data.cu_id
            log.info(f'CU_ID assigned: {self.cu_id}')
            with open('./devops/cu_manager/.cu_id', 'w', encoding='utf-8') as cu_id_file:
                cu_id_file.write(str(self.cu_id))
            self.registered.set()
            log.info(f"Device registered with CU_ID: {data.cu_id}")
        else:
            log.error("Error receiving CU_ID from broker")


    def launch_cs(self, mqtt_msg) -> None:
        '''Callback function executed from the Broker Client when a message is received from the
        broker in the CU_ID/launch/ topic.

        Args:
            mqtt_msg ([type]): [description]
        '''
        if mqtt_msg.payload == 'launch':
            result = subprocess.run(['./devops/deploy.sh', '', 'cs', '1'],
                                    stdout=subprocess.PIPE,
                                    universal_newlines=True,
                                    check=False)
            log.info(result.stdout) # TODO: sure? Is can be the all the output of cycler


    def process_iteration(self) -> None:
        self.client_mqtt.process_iteration()
        log.error("a")


#######################            FUNCTIONS             #######################

if __name__ == '__main__':
    working_flag_event : threading.Event = threading.Event()
    working_flag_event.set()
    cu_manager_node = CuManagerNodeC(working_flag=working_flag_event, cycle_period=1000)
    cu_manager_node.run()
