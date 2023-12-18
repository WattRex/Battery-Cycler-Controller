#!/usr/bin/python3
"""
Cu Manager
"""
#######################        MANDATORY IMPORTS         #######################

#######################         GENERIC IMPORTS          #######################
from datetime import datetime
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

#######################          PROJECT IMPORTS         #######################
from wattrex_cycler_datatypes.comm_data import CommDataCuC, CommDataHeartbeatC,\
    CommDataDeviceC, CommDataRegisterTypeE
from system_shared_tool import SysShdIpcChanC, SysShdNodeC, SysShdNodeStatusE

#######################          MODULE IMPORTS          #######################
from .cu_broker_client import BrokerClientC
from .register import get_cu_info
from .detect import DetectorC

#######################              ENUMS               #######################

#######################             CLASSES              #######################
class CuManagerNodeC(SysShdNodeC):  # pylint: disable=too-many-instance-attributes
    '''
    Cu Manager Class to instanciate a CU Manager Node
    '''

    def __init__(self, working_flag : threading.Event, cycle_period : int,
                 cu_id_file_path : str = './devops/cu_manager/.cu_id') -> None:
        '''
        Initialize the CU manager node.
        '''
        super().__init__(name='cu_manager_node', cycle_period=cycle_period,
                         working_flag=working_flag)
        self.cu_info: CommDataCuC = get_cu_info()
        self.heartbeat_queue : SysShdIpcChanC = SysShdIpcChanC(name='heartbeat_queue')
        self.active_cs : Dict[int, datetime] = {} # {cs_id : last_connection}
        self.client_mqtt : BrokerClientC = BrokerClientC(error_callback=self.broker_error_cb,
                                                         launch_callback=self.launch_cs,
                                                         detect_callback=self.process_detect,
                                                         store_cu_info_cb=self.store_cu_info_cb)
        # self.sync_node : MidSyncNoceC = MidSyncNoceC()
        self.working_flag_sync : threading.Event = threading.Event()
        self.working_flag_sync.set()

        self.working_flag = working_flag
        self.cycle_period : int = cycle_period

        self.__cu_id_file_path : str = cu_id_file_path

        self._cu_id = None
        if path.exists(self.__cu_id_file_path):
            with open(self.__cu_id_file_path, 'r', encoding='utf-8') as cu_id_file:
                self.cu_id = int(cu_id_file.read())
                self.client_mqtt.subscribe_cu(cu_id=self.cu_id, mac=self.cu_info.mac)
                log.info(f"Device previously registered with id: {self.cu_id}")
        else:
            self.registered = threading.Event()
            self.registered.clear()
            self.register_cu()
            log.info(f"Device registered with id: {self.cu_id}")
        self.detector = DetectorC(self.cu_id)

    @property
    def cu_id(self) -> int:
        '''
        Get the cu_id

        Returns:
            int: cu_id
        '''
        return self._cu_id


    @cu_id.setter
    def cu_id(self, new_cu_id) -> None:
        '''
        Set the cu_id

        Args:
            new_cu_id (int): new cu_id
        '''
        self.client_mqtt.cu_id = new_cu_id
        self._cu_id = new_cu_id


    def broker_error_cb(self) -> None:
        '''
        Callback function executed from the Broker Client when an error is detected
        '''
        log.critical('MQTT Error')
        self.status = SysShdNodeStatusE.COMM_ERROR


    def register_cu(self) -> None:
        '''
        Register the CU in the broker to get from it an id.
        '''
        cu_info : CommDataCuC = get_cu_info()
        cu_info.msg_type = CommDataRegisterTypeE.DISCOVER
        self.client_mqtt.publish_cu_info(cu_info)

        while not self.registered.is_set():
            self.client_mqtt.process_iteration()
            sleep(0.1)


    def store_cu_info_cb(self, data : CommDataCuC) -> None:
        '''
        Callback function executed from the Broker Client when a message is received from the
        broker in the CU_ID/register/ topic.

        Args:
            data (CommDataCuC): data received from the broker
        '''
        if isinstance(data, CommDataCuC):
            self.cu_id = data.cu_id
            log.info(f'CU_ID assigned: {self.cu_id}')
            with open(self.__cu_id_file_path, 'w', encoding='utf-8') as cu_id_file:
                cu_id_file.write(str(self.cu_id))
            self.registered.set()
            log.info(f"Device registered with CU_ID: {data.cu_id}")
        else:
            log.error("Error receiving CU_ID from broker")


    def process_detect(self) -> None:
        '''
        Process the detection
        '''
        log.info("Processing detection")
        detected_devices : List[CommDataDeviceC] = self.detector.process_detection()
        self.client_mqtt.publish_dev(detected_devices)


    def process_heartbeat(self) -> None:
        '''
        Process the heartbeat
        '''
        log.debug("Processing heartbeat")
        if self.__gather_heartbeat():
            hb = CommDataHeartbeatC(cu_id=self.cu_id)
            self.client_mqtt.publish_heartbeat(hb)


    def __gather_heartbeat(self) -> bool:
        # TODO: implement this @roberto # pylint: disable=fixme
        return True


    def launch_cs(self, cs_id : int) -> None:
        '''Callback function executed from the Broker Client when a message is received from the
        broker in the CU_ID/launch/ topic.

        Args:
            cs_id (int): cycler station id to launch
        '''
        log.info(f"Launching CS: {cs_id}")
        self.active_cs[cs_id] = datetime.now()
        # TODO: fix it, raise an error due to bad credential configuration # pylint: disable=fixme
        result = subprocess.run(['./devops/deploy.sh', 'cycler', f'{cs_id}'],
                    stdout=subprocess.PIPE,
                    universal_newlines=True,
                    check=False)
        log.critical(result.stdout)


    def process_iteration(self) -> None:
        '''
        Process an iteration of the CU Manager Node.
        '''
        self.client_mqtt.process_iteration()
        self.process_heartbeat()


    def sync_shd_data(self) -> None:
        '''Sync shared data with the sync node.
        '''


    def stop(self) -> None:
        '''Stop the stream .
        '''
        self.client_mqtt.close()

#######################            FUNCTIONS             #######################
