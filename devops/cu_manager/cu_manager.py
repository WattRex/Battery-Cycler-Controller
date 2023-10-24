#!/usr/bin/python3
"""
Cu Manager
"""
#######################        MANDATORY IMPORTS         #######################

#######################         GENERIC IMPORTS          #######################
import subprocess
import threading
from os import path
from typing import List
from time import sleep
import json

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

#######################          PROJECT IMPORTS         #######################
from system_shared_tool import SysShdIpcChanC, SysShdNodeC
from mid.mid_data import MidDataCuC, MidDataDeviceC, MidDataDeviceTypeE, MidDataLinkConfC

#######################              ENUMS               #######################
SECONDS_TO_WAIT_FOR_CU_ID = 60
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
        self.active_cs : dict = {} #{cs_id : last_connection}
        self.client_mqtt : BrokerClientC = BrokerClientC(error_callback=self.on_mqtt_error,
                                                         launch_callback=self.launch_cs,
                                                         detect_callback=self.detect_devices,
                                                         cu_id_msg_callback=self.on_register_answer)
        # self.sync_node : MidSyncNoceC = MidSyncNoceC()
        self.working_flag_sync : threading.Event = working_flag
        self.cycle_period : int = cycle_period

        self.cu_id = None
        if path.exists('./devops/cu_manager/.cu_id'):
            with open('./devops/cu_manager/.cu_id', 'r', encoding='utf-8') as cu_id_file:
                self.cu_id = int(cu_id_file.read())
        else:
            self.register_cu()


    def process_heartbeat(self) -> None:
        pass

    def __gather_heartbeat(self) -> None:
        pass

    def register_cu(self) -> None:
        '''
        Register the CU in the broker to get from it an id.
        '''
        self.client_mqtt.publish_cu_info(MidDataCuC())
        for _ in range(SECONDS_TO_WAIT_FOR_CU_ID*10):
            if self.cu_id is not None:
                break
            self.client_mqtt.mqtt.process_data()
            sleep(0.1)

        if self.cu_id is None:
            log.critical('No CU_ID assigned')
            raise RuntimeError('No CU_ID assigned')

        log.info('CU_ID assigned: %s', self.cu_id)
        with open('./devops/cu_manager/.cu_id', 'w', encoding='utf-8') as cu_id_file:
            cu_id_file.write(str(self.cu_id))


    def detect_devices(self) -> List[MidDataDeviceC]:
        '''Detect the devices that are currently connected to the device.

        Returns:
            List[MidDataDeviceC]: List of devices connected to the device that are detected and 
            which type has been previously defined.
        '''

        test_detected_device = MidDataDeviceC(dev_id=1,
                                                            manufacturer='test',
                                                            model='test',
                                                            serial_number='test',
                                                            device_type=MidDataDeviceTypeE.EPC,
                                                            iface_name='test',
                                                            mapping_names={'test':'test'},
                                                            link_configuration=MidDataLinkConfC(
                                                                baudrate=9600,
                                                                parity='N',
                                                                stopbits=1,
                                                                bytesize=8,
                                                                timeout=0.1,
                                                                write_timeout=0.1,
                                                                inter_byte_timeout=0.1,
                                                                separator='\n'))
        return [test_detected_device]

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
            log.info(result.stdout)

    def on_mqtt_error(self) -> None:
        ''' Callback function executed from the Broker Client when an error is detected
        '''
        log.critical('MQTT Error')

    def on_register_answer(self, msg_data) -> None:
        '''
        Callback function executed from the Broker Client when 
        a message is received from the mqtt broker

        Args:
            msg_data (MidDataCuC): Message data
        '''
        msg_data = json.loads(msg_data)
        if 'type' in msg_data:
            log.critical(msg_data)
            log.critical(json.loads(msg_data))
            if msg_data['mac'] == MidDataCuC().mac:
                self.cu_id = msg_data['cu_id']
                log.info('Cu_id received from mqtt: %s', self.cu_id)
            else:
                log.info('Cu_id received from mqtt but is not for this CU: %s', msg_data['cu_id'])
        else:
            raise RuntimeWarning("No type defined in msg received from '/inform_reg' suscribed topic")


    def sync_shd_data(self) -> None:
        pass

    def process_iteration(self) -> None:
        log.error("a")
        sleep(0.8)

    def stop(self) -> None:
        pass


#######################            FUNCTIONS             #######################

if __name__ == '__main__':
    working_flag_event : threading.Event = threading.Event()
    working_flag_event.set()
    cu_manager_node = CuManagerNodeC(working_flag=working_flag_event, cycle_period=1000)
    cu_manager_node.run()
