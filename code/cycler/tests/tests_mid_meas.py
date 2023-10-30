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
main_logger = SysLogLoggerC(file_log_levels="code/cycler/log_config.yaml")
log: Logger = sys_log_logger_get_module_logger(name="test_mid_dabs")
from system_shared_tool import SysShdSharedObjC
#######################       THIRD PARTY IMPORTS        #######################
from can_sniffer import DrvCanNodeC
from wattrex_battery_cycler_datatypes.cycler_data import (CyclerDataDeviceC, CyclerDataDeviceTypeE,
                CyclerDataLinkConfC, CyclerDataGenMeasC, CyclerDataExtMeasC, CyclerDataAllStatusC)
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

    @fixture(scope="function", autouse=False)
    def set_environ(self, request): #pylint: disable= too-many-locals
        """Setup the environment variables and start the process .

        Args:
            request ([type]): [description]

        Yields:
            [type]: [description]
        """
        log.info(msg=f"Setting up the environment for {request}")
        conf_param = {
            "EPC": {
                "dev_id": 17,
                "device_type": "Epc",
                "iface_name": 17,
                "manufacturer": "abc",
                "model" : "123",
                "serial_number" : "12311",
                "mapping_names" : {
                    "hs_voltage": "hs_voltage",
                    "temp_body": "temperatura_1",
                    "temp_anod": "temperatura_2",
                    "temp_amb": "temperatura_ambiente"
                },
            },
            "SOURCE": {
                "dev_id": 18,
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
                "dev_id": 19,
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
        if set(['SOURCE','LOAD']).issubset(request):
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
            conf_param = conf_param[next(iter(conf_param))]
            if conf_param['device_type'].lower() == 'epc':
                _can_working_flag = Event()
                _can_working_flag.set()
                can = DrvCanNodeC(tx_buffer_size= 100, working_flag = _can_working_flag)
                can.start()
                sleep(2)
                conf_param['device_type'] = CyclerDataDeviceTypeE(conf_param['device_type'])
            else:
                conf_param['device_type'] = CyclerDataDeviceTypeE(conf_param['device_type'])
                conf_param['link_configuration'] = CyclerDataLinkConfC(
                    **conf_param['link_configuration'])
            devices: List[CyclerDataDeviceC] = [CyclerDataDeviceC(**conf_param)]
        _meas_working_flag = Event()
        _meas_working_flag.set()
        gen_meas: SysShdSharedObjC = SysShdSharedObjC(CyclerDataGenMeasC())
        ext_meas: SysShdSharedObjC = SysShdSharedObjC(CyclerDataExtMeasC())
        all_status: SysShdSharedObjC = SysShdSharedObjC(CyclerDataAllStatusC())
        mid_meas_node = MidMeasNodeC(shared_gen_meas = gen_meas, shared_ext_meas = ext_meas,
                                     shared_status = all_status, cycle_period = 500,
                                     working_flag = _meas_working_flag, devices = devices)
        try:
            mid_meas_node.start()
            i=0
            while i<30:
                tic = time()
                log.info(f"Measuring: {gen_meas.read().voltage}mV and {gen_meas.read().current}mA")
                log.info(f"Measuring: hs_voltage =  {ext_meas.read().hs_voltage}mV")
                log.info(f"Measuring: external measures =  {ext_meas.read().__dict__}")
                if all_status.read().pwr_dev.error_code != 0:
                    log.error((f"Reading error {all_status.read().pwr_dev.name}, "
                              f"code: {all_status.read().pwr_dev.error_code}"))
                while time()-tic <= 1:
                    pass
                i+=1
        except Exception as err:
            log.error(msg=f"Exception: {err}")

        _can_working_flag.clear()
        _meas_working_flag.clear()
        sleep(2)

    @fixture(scope="function")
    def config(self) -> None:
        """Configure the signal handler to signal when the SIGINT is received .
        """
        signal(SIGINT, self.signal_handler)


    #Test container
    @mark.parametrize("set_environ", [['EPC']],
                      indirect=["set_environ"])
    def test_normal_op(self, set_environ, config) -> None: #pylint: disable= unused-argument
        """Test the machine status .

        Args:
            set_environ ([type]): [description]
            config ([type]): [description]
        """
        log.debug(msg="1. Test mid meas")
