#!/usr/bin/python3
'''
This file contains the class that will detected the different devices connected to the cycler.
'''

#######################        MANDATORY IMPORTS         #######################
from __future__ import annotations
from typing import List, Dict, Tuple

#######################         GENERIC IMPORTS          #######################
from os import listdir
from time import time
from serial import PARITY_ODD

#######################      SYSTEM ABSTRACTION IMPORTS  #######################
from system_logger_tool import Logger, SysLogLoggerC, sys_log_logger_get_module_logger
if __name__ == '__main__':
    cycler_logger = SysLogLoggerC(file_log_levels='./devops/cu_manager/log_config.yaml',
                                  output_sub_folder='detector')
log: Logger = sys_log_logger_get_module_logger(__name__)
from bitarray.util import ba2int, int2ba
from bitarray import bitarray

#######################       THIRD PARTY IMPORTS        #######################
from can_sniffer import DrvCanCmdDataC, DrvCanFilterC, DrvCanCmdTypeE, DrvCanMessageC
from scpi_sniffer import DrvScpiCmdDataC, DrvScpiCmdTypeE, DrvScpiSerialConfC
from system_shared_tool import SysShdIpcChanC

#######################          PROJECT IMPORTS         #######################
from wattrex_cycler_datatypes.comm_data import CommDataDeviceC #pylint: disable= wrong-import-order

#######################          MODULE IMPORTS          #######################

######################             CONSTANTS              ######################
from .context import (DEFAULT_TX_CAN_NAME, DEFAULT_TX_SCPI_NAME, DEFAULT_RX_CAN_NAME,
                    DEFAULT_DETECT_TIMEOUT, DEFAULT_DEV_PATH, DEFAULT_SCPI_QUEUE_PREFIX)

#######################              CLASS               #######################
all_devices = {
    'EPC': (0x13, 0x80), # Range of can ids for the registered EPCs (0x80 excluded, max value 0x7F)
}
## The models corresponds to the bits of the serial number to know which sensor has.
comp_dev = {
    'EPC': {'Model_0': 2},
            ## Future models of EPCs
            # , 'Model_1': 4, 'Model_2': 5, 'Model_3': 6, 'Model_4': 7, 'Model_5': 8,
            # 'Model_6': 9, 'Model_7': 10, 'Model_8': 11, 'Model_9': 12, 'Model_A': 13,
            # 'Model_B': 14, 'Model_C': 15, 'Model_D': 16, 'Model_E': 17},
    'EA': {'VIRTUAL': 1, 'PS_2042-20_B': 4, 'PSB_10200-420': 6},
    'RS': {'RS-KEL103': 5},
    'BK': {},
    'BMS': 3,
    'FLOW': {},
}

class DetectorC: #pylint: disable= too-many-instance-attributes
    '''
    Classmethod to handle DetectorCectorC .
    '''
    def __init__(self, cu_id : int):
        self.__cu_id = cu_id
        self.det_bms: List[CommDataDeviceC] = []
        self.det_epc: List[CommDataDeviceC] = []
        self.det_source: List[CommDataDeviceC] = []
        self.det_bisource: List[CommDataDeviceC] = []
        self.det_load: List[CommDataDeviceC] = []
        self.det_flow: List[CommDataDeviceC] = []
        self.det_bk: List[CommDataDeviceC] = []
        self.found_scpi_devs: Dict[str, Dict[str, bool]] = {
            ## The bool indicates if the device has responded
            ## Example: 'source': {'EA_1': False, 'EA_2': False},
            'bisource': {},
            'source': {},
            'loads': {},
            'bk': {},
            'flow': {},
        }
        self.__reqs_flow: bool = False
        self.__reqs_sources: bool = False
        self.__reqs_bisources: bool = False
        self.__reqs_loads: bool = False
        self.__reqs_epc: bool = False
        self.__reqs_bk: bool = False


        ## Create the queues for CAN messages
        self.__tx_can: SysShdIpcChanC
        self.__rx_can: SysShdIpcChanC
        ## Create the queues for SCPI messages
        self.__tx_scpi: SysShdIpcChanC
        self.__rx_scpi : Dict[str, SysShdIpcChanC] = {}

    def process_detection(self) -> List[CommDataDeviceC]:
        '''
        Process detection of connected devices using CAN and SCPI.
        '''
        ## Reset detected devices lists
        self.__reset_detected()
        self.__find_scpi_devs()
        ## Add filter to the can bus to receive all messages
        self.__tx_can.send_data(DrvCanCmdDataC(data_type= DrvCanCmdTypeE.ADD_FILTER,
                                        payload= DrvCanFilterC(addr= 0x000, mask= 0x000,
                                                                chan_name=DEFAULT_RX_CAN_NAME)))
        # ## Request detections
        self.detect_epc()
        self.detect_sources()
        self.detect_bisources()
        self.detect_flow()
        self.detect_loads()
        self.detect_bk()
        log.info("START DETECT DEVICES LOOP")
        initial_time = time()
        while (initial_time + DEFAULT_DETECT_TIMEOUT) > time():
            msg_can : DrvCanMessageC = self.__rx_can.receive_data_unblocking()
            if msg_can is not None:
                if 0x100 <= msg_can.addr <= 0x120:
                    log.warning("BMS detected")
                    self.detect_bms(msg_can)
                elif 0x130 <= msg_can.addr <= 0x7FF:
                    log.warning("EPC detected")
                    self.detect_epc(msg_can)
                else:
                    log.error(f"Unknown device with can id {msg_can.addr}")
            ## Process detection of scpi devices
            self.detect_sources()
            self.detect_bisources()
            self.detect_flow()
            self.detect_loads()
            self.detect_bk()

        self.__tx_can.send_data(DrvCanCmdDataC(data_type= DrvCanCmdTypeE.REMOVE_FILTER,
                                        payload= DrvCanFilterC(addr= 0x000, mask= 0x000,
                                                chan_name=DEFAULT_RX_CAN_NAME)))

        ## Close the channels
        self.close()
        all_devices_detected  = self.det_bms + self.det_epc + self.det_source + self.det_load +\
                                self.det_flow + self.det_bisource
        return all_devices_detected

    def __reset_detected(self) -> None:
        '''
        Reset the detection of connected devices.
        '''
        ## Create the queues for CAN messages
        self.__tx_can: SysShdIpcChanC = SysShdIpcChanC(name= DEFAULT_TX_CAN_NAME)
        self.__rx_can: SysShdIpcChanC = SysShdIpcChanC(name= DEFAULT_RX_CAN_NAME,
                                                        max_message_size= 400)
        ## Create the queues for SCPI messages
        self.__tx_scpi: SysShdIpcChanC = SysShdIpcChanC(name= DEFAULT_TX_SCPI_NAME)

        self.det_bms.clear()
        self.det_bisource.clear()
        self.det_epc.clear()
        self.det_source.clear()
        self.det_load.clear()
        self.det_flow.clear()
        self.det_bk.clear()
        for dev_dict,_ in self.found_scpi_devs.items():
            self.found_scpi_devs[dev_dict].clear() #pylint: disable= unnecessary-dict-index-lookup
        self.__reqs_flow = False #pylint: disable= unused-private-member
        self.__reqs_sources = False
        self.__reqs_bisources = False
        self.__reqs_loads = False #pylint: disable= unused-private-member
        self.__reqs_epc = False
        self.__reqs_bk = False

    def __find_scpi_devs(self) -> None:
        '''
        Find the scpi devices connected to the computational unit.
        '''
        for dev_dir,_ in self.found_scpi_devs.items():
            listdir_result: List[str] = []
            try:
                listdir_result = listdir(DEFAULT_DEV_PATH+dev_dir)
            except FileNotFoundError:
                log.info(f"Path {DEFAULT_DEV_PATH+dev_dir} not found")
                continue
            for element in listdir_result:
                self.found_scpi_devs[dev_dir][element] = False #pylint: disable= unnecessary-dict-index-lookup

    def detect_bms(self, msg: DrvCanMessageC):
        '''
        Detect the bms connected to the cycler.
        '''
        if int(msg.addr) not in [dev.serial_number for dev in self.det_bms]:
            dev_data = CommDataDeviceC(cu_id=self.__cu_id, comp_dev_id= comp_dev['BMS'],
                                    serial_number= msg.addr,
                                    link_name= str(msg.addr - 0x100))
            self.det_bms.append(dev_data)

    def detect_epc(self, msg: DrvCanMessageC|None = None) -> None:
        '''
        Detect the bms connected to the cycler.

        Returns:
            List[CyclerDataDeviceC]: List of bms devices.
        '''
        if not self.__reqs_epc:
            ## Request info for all the epcs listed
            for can_id in range(all_devices['EPC'][0], all_devices['EPC'][1]):
                ## The id send is the union of the device can id and type of the message to send
                id_msg = can_id<<4 | 1
                data_msg = 0x0
                msg = DrvCanMessageC(addr= id_msg, size= 1, payload = data_msg)
                self.__tx_can.send_data(DrvCanCmdDataC(data_type=DrvCanCmdTypeE.MESSAGE,
                                                         payload=msg))
            self.__reqs_epc = True
        elif msg is not None and (msg.addr & 0x00F) == 0xA:
            can_id, serial_number, hw_ver = self.__parse_epc_msg(msg)
            hw_ver = ba2int(hw_ver[7:])
            if can_id not in [int(dev.link_name) for dev in self.det_epc]:
                dev_data = CommDataDeviceC(cu_id=self.__cu_id,
                                           comp_dev_id= comp_dev['EPC'][f"Model_{hex(hw_ver)[0]}"],
                                           serial_number=serial_number,
                                           link_name= can_id)
                self.det_epc.append(dev_data)

    def detect_loads(self):
        '''
        Detect the sources connected to the cycler.
        '''
        if not self.__reqs_loads: #pylint: disable= too-many-nested-blocks
            ## Create a queue for each SCPI connected device
            for load_name in self.found_scpi_devs['loads']:
                try:
                    self.__rx_scpi[load_name] = SysShdIpcChanC(
                                                name= DEFAULT_SCPI_QUEUE_PREFIX+load_name,
                                                max_message_size=400)
                except Exception as exc:
                    log.error(f"Error creating queue for load: {exc}")
                    self.close()
                    raise exc
                self.__tx_scpi.send_data(DrvScpiCmdDataC(
                                            data_type=DrvScpiCmdTypeE.ADD_DEV,
                                            port=DEFAULT_DEV_PATH+'loads/'+load_name,
                                            rx_chan_name=DEFAULT_SCPI_QUEUE_PREFIX+load_name,
                                            payload=DrvScpiSerialConfC(
                                                port=DEFAULT_DEV_PATH+'loads/'+load_name,
                                                separator='\n', timeout = 0.8,
                                                write_timeout = 0.8, parity = PARITY_ODD,
                                                baudrate = 115200)
                                            )
                                        )
                ## Request info for the source
                if load_name.startswith('RS'):
                    self.__tx_scpi.send_data(DrvScpiCmdDataC(data_type=DrvScpiCmdTypeE.WRITE_READ,
                                                port=DEFAULT_DEV_PATH+'loads/'+load_name,
                                                payload="*IDN?"))
            self.__reqs_loads = True
        else:
            for load_name in self.found_scpi_devs['loads']:
                if not self.found_scpi_devs['loads'][load_name]:
                    ## Try to read its queue for response
                    msg_load: DrvScpiCmdDataC|None = \
                                            self.__rx_scpi[load_name].receive_data_unblocking()
                    if msg_load is not None:
                        if load_name.startswith('RS'):
                            try:
                                load_serial_number = msg_load.payload[0].split(':')[-1]
                                load_model = msg_load.payload[0].split(' ')[0]
                            except Exception as exc:
                                log.error((f"Error parsing loads response: {exc} | "
                                        f"Response received (__dict__): {msg_load.__dict__}"))
                            else:
                                log.critical(f"Load found: {msg_load.__dict__}")
                                self.det_load.append(CommDataDeviceC(cu_id=self.__cu_id,
                                                            comp_dev_id= comp_dev['RS'][load_model],
                                                            serial_number=load_serial_number,
                                                            link_name=load_name))

                        self.found_scpi_devs['loads'][load_name] = True
                        self.__tx_scpi.send_data(DrvScpiCmdDataC(
                                                data_type=DrvScpiCmdTypeE.DEL_DEV,
                                                port=DEFAULT_DEV_PATH+'loads/'+load_name,
                                                rx_chan_name=DEFAULT_SCPI_QUEUE_PREFIX+load_name)
                                        )
                        self.__rx_scpi.pop(load_name).terminate()

    def detect_sources(self):
        '''
        Detect the sources connected to the cycler.
        '''
        if not self.__reqs_sources: #pylint: disable= too-many-nested-blocks
            ## Create a queue for each SCPI connected device
            for source_name in self.found_scpi_devs['source']:
                try:
                    self.__rx_scpi[source_name] = SysShdIpcChanC(
                                                name= DEFAULT_SCPI_QUEUE_PREFIX+source_name,
                                                max_message_size=500)
                except Exception as exc:
                    log.error(f"Error creating queue for source: {exc}")
                    self.close()
                    raise exc
                self.__tx_scpi.send_data(DrvScpiCmdDataC(
                                data_type=DrvScpiCmdTypeE.ADD_DEV,
                                port=DEFAULT_DEV_PATH+'source/'+source_name,
                                rx_chan_name=DEFAULT_SCPI_QUEUE_PREFIX+source_name,
                                payload=DrvScpiSerialConfC(
                                        port=DEFAULT_DEV_PATH+'source/'+source_name,
                                        separator='\n', timeout = 0.8,
                                        write_timeout = 0.8, parity = PARITY_ODD,
                                        baudrate = 9600)))
                ## Request info for the source
                if source_name.startswith('EA'):
                    self.__tx_scpi.send_data(DrvScpiCmdDataC(data_type=DrvScpiCmdTypeE.WRITE_READ,
                                                        port=DEFAULT_DEV_PATH+'source/'+source_name,
                                                        payload=":*IDN?"))
            self.__reqs_sources = True
        else:
            for source_name in self.found_scpi_devs['source']:
                if not self.found_scpi_devs['source'][source_name]:
                    ## Try to read its queue for response
                    msg_source: DrvScpiCmdDataC|None = \
                                            self.__rx_scpi[source_name].receive_data_unblocking()
                    if msg_source is not None:
                        if source_name.startswith('EA'):
                            try:
                                ea_serial_number = msg_source.payload[0].split(', ')[2]
                                ea_model = msg_source.payload[0].split(', ')[1].replace(' ', '_')
                            except Exception as exc:
                                log.error((f"Error parsing EA response: {exc} | "
                                           f"Response received (__dict__): {msg_source.__dict__}"))
                            else:
                                log.critical(f"EA found: {msg_source.__dict__}")
                                self.det_source.append(CommDataDeviceC(cu_id=self.__cu_id,
                                                            comp_dev_id= comp_dev['EA'][ea_model],
                                                            serial_number=ea_serial_number,
                                                            link_name=source_name))

                        self.found_scpi_devs['source'][source_name] = True
                        self.__tx_scpi.send_data(DrvScpiCmdDataC(
                                                data_type=DrvScpiCmdTypeE.DEL_DEV,
                                                port=DEFAULT_DEV_PATH+'source/'+source_name,
                                                rx_chan_name=DEFAULT_SCPI_QUEUE_PREFIX+source_name)
                                        )
                        self.__rx_scpi.pop(source_name).terminate()

    def detect_bisources(self):
        '''
        Detect the sources connected to the cycler.
        '''
        if not self.__reqs_bisources: #pylint: disable= too-many-nested-blocks
            ## Create a queue for each SCPI connected device
            for bisource_name in self.found_scpi_devs['bisource']:
                try:
                    self.__rx_scpi[bisource_name] = SysShdIpcChanC(
                                                name= DEFAULT_SCPI_QUEUE_PREFIX+bisource_name,
                                                max_message_size=400)
                except Exception as exc:
                    log.error(f"Error creating queue for bisource: {exc}")
                    self.close()
                    raise exc
                self.__tx_scpi.send_data(DrvScpiCmdDataC(
                                            data_type=DrvScpiCmdTypeE.ADD_DEV,
                                            port=DEFAULT_DEV_PATH+'bisource/'+bisource_name,
                                            rx_chan_name=DEFAULT_SCPI_QUEUE_PREFIX+bisource_name,
                                            payload=DrvScpiSerialConfC(
                                                port=DEFAULT_DEV_PATH+'bisource/'+bisource_name,
                                                separator='\n', timeout = 0.8,
                                                write_timeout = 0.8, parity = PARITY_ODD,
                                                baudrate = 9600)
                                            )
                                        )
                ## Request info for the source
                if bisource_name.startswith('EPS'):
                    self.__tx_scpi.send_data(DrvScpiCmdDataC(data_type=DrvScpiCmdTypeE.WRITE_READ,
                                                port=DEFAULT_DEV_PATH+'bisource/'+bisource_name,
                                                payload=":*IDN?"))
            self.__reqs_bisources = True
        else:
            for bisource_name in self.found_scpi_devs['bisource']:
                if not self.found_scpi_devs['bisource'][bisource_name]:
                    ## Try to read its queue for response
                    msg_bisource: DrvScpiCmdDataC|None = \
                                            self.__rx_scpi[bisource_name].receive_data_unblocking()
                    if msg_bisource is not None:
                        if bisource_name.startswith('EPS'):
                            try:
                                bi_serial_number = msg_bisource.payload[0].split(', ')[2]
                                bi_model = msg_bisource.payload[0].split(', ')[1].replace(' ', '_')
                            except Exception as exc:
                                log.error((f"Error parsing Bisource response: {exc} | "
                                        f"Response received (__dict__): {msg_bisource.__dict__}"))
                            else:
                                log.critical(f"BiSource found: {msg_bisource.__dict__}")
                                self.det_bisource.append(CommDataDeviceC(cu_id=self.__cu_id,
                                                            comp_dev_id= comp_dev['EA'][bi_model],
                                                            serial_number=bi_serial_number,
                                                            link_name=bisource_name))

                        self.found_scpi_devs['bisource'][bisource_name] = True
                        self.__tx_scpi.send_data(DrvScpiCmdDataC(
                                            data_type=DrvScpiCmdTypeE.DEL_DEV,
                                            port=DEFAULT_DEV_PATH+'bisource/'+bisource_name,
                                            rx_chan_name=DEFAULT_SCPI_QUEUE_PREFIX+bisource_name)
                                        )
                        self.__rx_scpi.pop(bisource_name).terminate()

    def detect_flow(self):
        '''
        Detect the flow connected to the cycler.
        '''
        if not self.__reqs_flow:
            self.__reqs_flow = True
        else:
            pass

    def detect_bk(self):
        '''
        Detect the bk connected to the cycler.
        '''
        if not self.__reqs_bk:
            self.__reqs_bk = True
        else:
            pass

    def __parse_epc_msg(self, msg: DrvCanMessageC) -> Tuple[int, str, bitarray]:
        msg_bits = int2ba(int.from_bytes(msg.payload,'little'),length=64, endian='little')
        # The first 6 bits correspond to the can id
        can_id = ba2int(msg_bits[:6])
        log.debug(f"Device ID: {can_id}")
        # The next 5 bits correspond to the fw version
        fw_ver = ba2int(msg_bits[6:11])
        log.debug(f"Device fw version: {fw_ver}")
        # The next 13 bits correspond to the hw version
        hw_ver = msg_bits[11:24]
        log.debug(f"Device hw version: {ba2int(hw_ver)}")
        # The last bits correspond to the serial number
        serial_number = str(ba2int(msg_bits[24:32]))
        return can_id, serial_number, hw_ver

    def close(self) -> None:
        '''
        Close used ipc channels
        '''
        ## Closing conections with queues
        if isinstance(self.__rx_can, SysShdIpcChanC):
            self.__rx_can.terminate()
        if isinstance(self.__tx_can, SysShdIpcChanC):
            self.__tx_can.close()
        if isinstance(self.__tx_scpi, SysShdIpcChanC):
            self.__tx_scpi.close()
        log.critical("Closing channels used by detector")
