#!/usr/bin/python3
"""
This file test mid_dabs and show how it works.
"""

#######################        MANDATORY IMPORTS         #######################
import os
import sys
from typing import List
#######################         GENERIC IMPORTS          #######################
from threading import Event
from signal import signal, SIGINT
from time import time, sleep
from pytest import fixture, mark
#######################      SYSTEM ABSTRACTION IMPORTS  #######################
from system_logger_tool import Logger, SysLogLoggerC, sys_log_logger_get_module_logger
main_logger = SysLogLoggerC(file_log_levels="config/cycler/log_config.yaml")
log: Logger = sys_log_logger_get_module_logger(name="test_mid_dabs")
from system_shared_tool import SysShdSharedObjC, SysShdNodeStatusE
#######################       THIRD PARTY IMPORTS        #######################
# from can_sniffer import DrvCanNodeC
from wattrex_cycler_datatypes.cycler_data import (CyclerDataDeviceC, CyclerDataDeviceTypeE,
                CyclerDataLinkConfC, CyclerDataGenMeasC, CyclerDataExtMeasC, CyclerDataAllStatusC,
                CyclerDataMergeTagsC)
#######################          MODULE IMPORTS          #######################
sys.path.append(os.getcwd()+'/code/cycler/')
from src.wattrex_battery_cycler.mid.mid_meas import MidMeasNodeC

#######################              CLASS               #######################

class TestChannels:
    """A test that tests the channels in pytest.
    """
    MAX_PERIOD = 120


    def signal_handler(self, sig, frame) -> None: #pylint: disable= unused-argument
        """Called when the user presses Ctrl + C to stop test.

        Args:
            sig ([type]): [description]
            frame ([type]): [description]
        """
        log.critical(msg='You pressed Ctrl+C! Stopping test...')
        self._meas_working_flag.clear()
        sleep(2)
        # self._can_working_flag.clear()
        # sleep(2)
        sys.exit(0)

    @fixture(scope="function", autouse=False)
    def set_environ(self, request): #pylint: disable= too-many-locals, too-many-statements
        """Setup the environment variables and start the process .

        Args:
            request ([type]): [description]

        Yields:
            [type]: [description]
        """
        log.info(msg=f"Setting up the environment for {request.param}")
        conf_param = {
            "EPC": {
                "dev_db_id": 20,
                "device_type": "Epc",
                "iface_name": 20,
                "manufacturer": "abc",
                "model" : "123",
                "serial_number" : "12311",
                "mapping_names" : {
                    "hs_voltage": 1,
                    "temp_body": 2,
                    "temp_anod": 3,
                    "temp_amb": 4
                },
            },
            "BMS": {
                "dev_db_id": 3, ## For local test use 2
                "device_type": "Bms",
                "iface_name": 3, ## For local test use 2
                "manufacturer": "abc",
                "model" : "123",
                "serial_number" : "12311",
                "mapping_names" : {'vcell1': 1, 'vcell2': 2, 'vcell3': 3,
                        'vcell4': 4, 'vcell5': 5, 'vcell6': 6,
                        'vcell7': 7, 'vcell8': 8, 'vcell9': 9,
                        'vcell10': 10, 'vcell11': 11, 'vcell12': 12,
                        'vstack': 13, 'temp1': 14, 'temp2': 15,
                        'temp3': 16, 'temp4': 17, 'pres1': 18,
                        'pres2': 19},
            },
            "SOURCE": {
                "dev_db_id": 18,
                "device_type": "Source",
                "iface_name": '/dev/ttyUSB0',
                "manufacturer": "abc",
                "model" : "123",
                "serial_number" : "12311",
                "mapping_names" : {
                    "voltage": "voltage_Source",
                    "current": "current_Source",
                },
            },
            "LOAD": {
                "dev_db_id": 19,
                "device_type": "Load",
                "iface_name": '/dev/ttyUSB1',
                "manufacturer": "abc",
                "model" : "123",
                "serial_number" : "12311",
                "mapping_names" : {
                    "voltage": "voltage_Load",
                    "current": "current_Load",
                },
            }
        }
        devices: List[CyclerDataDeviceC] = []
        # request = ['EPC']
        if set(['SOURCE','LOAD']).issubset(request.param):
            conf_param_dev1 = conf_param['SOURCE']
            conf_param_dev2 = conf_param['LOAD']
            for conf in [conf_param_dev1, conf_param_dev2]:
                if conf['device_type'].lower() is ('source','load'):
                    conf['device_type'] = CyclerDataDeviceTypeE(conf['device_type'])
                    conf['link_configuration'] = CyclerDataLinkConfC(
                        **conf['link_configuration'])
            devices: List[CyclerDataDeviceC] = [CyclerDataDeviceC(**conf_param_dev1),
                                    CyclerDataDeviceC(**conf_param_dev2)]
        elif {'EPC'} <= conf_param.keys():
            conf_param_epc = conf_param[next(iter(conf_param))]
            # self._can_working_flag = Event() #pylint: disable= attribute-defined-outside-init
            # self._can_working_flag.set()
            # can = DrvCanNodeC(tx_buffer_size= 100, working_flag = self._can_working_flag,
            #                     cycle_period= 50)
            # can.start()
            # sleep(2)
            conf_param_epc['device_type'] = CyclerDataDeviceTypeE(conf_param_epc['device_type'])
            devices: List[CyclerDataDeviceC] = [CyclerDataDeviceC(**conf_param_epc)]
        ### ADD EXTRA METERS
        if {'BMS'} <= conf_param.keys():
            conf_param = conf_param['BMS']
            conf_param['device_type'] = CyclerDataDeviceTypeE(conf_param['device_type'])
            devices.append(CyclerDataDeviceC(**conf_param))
        log.info(msg=f"Devices: {devices}")
        tags = CyclerDataMergeTagsC(status_attrs= [],
                                    gen_meas_attrs= ['instr_id'],
                                    ext_meas_attrs= [])
        self._meas_working_flag = Event() #pylint: disable= attribute-defined-outside-init
        self._meas_working_flag.set()
        gen_meas: SysShdSharedObjC = SysShdSharedObjC(CyclerDataGenMeasC())
        ext_meas: SysShdSharedObjC = SysShdSharedObjC(CyclerDataExtMeasC())
        all_status: SysShdSharedObjC = SysShdSharedObjC(CyclerDataAllStatusC())
        mid_meas_node = MidMeasNodeC(shared_gen_meas = gen_meas, shared_ext_meas = ext_meas,
                                     shared_status = all_status,
                                     working_flag = self._meas_working_flag, devices = devices,
                                     excl_tags= tags)
        ext_meas_list= ['hs_voltage_1', 'temp_body_2', 'temp_anod_3', 'temp_amb_4', 'vcell1_1',
                'vcell2_2', 'vcell3_3', 'vcell4_4', 'vcell5_5', 'vcell6_6', 'vcell7_7', 'vcell8_8',
                'vcell9_9', 'vcell10_10', 'vcell11_11', 'vcell12_12', 'vstack_13', 'temp1_14',
                'temp2_15', 'temp3_16', 'temp4_17', 'pres1_18', 'pres2_19']
        try:
            mid_meas_node.start()
            i=0
            while mid_meas_node.status is not SysShdNodeStatusE.OK:
                sleep(1)
            while i<10:
                tic = time()
                log.info(f"Measuring: {gen_meas.read().voltage}mV and {gen_meas.read().current}mA")
                # log.info(f"Measuring: hs_voltage =  {ext_meas.read().hs_voltage_1} mV")
                data_ext = ext_meas.read()
                epc_ext = [f"{attr}: {data_ext.__dict__[attr]}"  for attr in ext_meas_list[0:4]]
                log.info(f"Measuring: external measures epc=   {epc_ext}")
                bms_ext = [f"{attr}: {data_ext.__dict__[attr]}"  for attr in ext_meas_list[4:]]
                log.info(f"Measuring: external measures bms=   {bms_ext}")
                data_status = all_status.read()
                log.info(f"Status epc:{data_status.pwr_dev.name}")
                att_name = [attr for attr in data_status.__dict__.keys() if 'extra_meter' in attr]
                if len(att_name)>0:
                    log.info(f"Status bms:{getattr(data_status, att_name[0]).name}")
                if data_status.pwr_dev.error_code != 0:
                    log.error((f"Reading error {data_status.pwr_dev.name}, "
                              f"code: {data_status.pwr_dev.error_code}"))
                while time()-tic <= 1:
                    pass
                i+=1
        except Exception as err:
            log.error(msg=f"Exception: {err}")

        self._meas_working_flag.clear()
        sleep(2)
        # self._can_working_flag.clear()
        # sleep(1)

    @fixture(scope="function")
    def config(self) -> None:
        """Configure the signal handler to signal when the SIGINT is received .
        """
        signal(SIGINT, self.signal_handler)

    @mark.parametrize("set_environ", [["EPC"]], indirect=["set_environ"])
    def test_normal_op(self, config, set_environ) -> None: #pylint: disable= unused-argument
        """Test the machine status .

        Args:
            set_environ ([type]): [description]
            config ([type]): [description]
        """
        log.debug(msg="1. Test mid meas")
