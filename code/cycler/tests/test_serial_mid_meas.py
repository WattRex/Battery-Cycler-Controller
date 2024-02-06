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
from src.wattrex_battery_cycler.mid.mid_dabs import MidDabsPwrDevC

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
        self.load_source.close()
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
            'source': {'port': '/dev/wattrex/source/EA_2963640425', 'separator':'\n',
                        'baudrate':9600, 'timeout':1, 'write_timeout':1},
            'load':{'port': '/dev/wattrex/loads/RS_79E047AE41D5', 'separator':'\n',
                        'baudrate':115200, 'timeout':1, 'write_timeout':1}
            }
        devices: List[CyclerDataDeviceC] = []
        test_load_info = CyclerDataDeviceC(dev_db_id= 0, model = 'b',
                                manufacturer= 'RS', device_type= CyclerDataDeviceTypeE.LOAD,
                                iface_name= conf_param['load']['port'],
                                link_configuration= CyclerDataLinkConfC(**conf_param['load']),
                                mapping_names= {'voltage': 1, 'current': 2, 'power': 3})
        test_load_info.check_power_device()
        test_source_info = CyclerDataDeviceC(dev_db_id= 1, model = 'b',
                                manufacturer= 'EA', device_type= CyclerDataDeviceTypeE.SOURCE,
                                iface_name= conf_param['source']['port'],
                                link_configuration= CyclerDataLinkConfC(**conf_param['source']),
                                mapping_names= {'voltage': 4, 'current': 5, 'power': 6})
        test_source_info.check_power_device()
        devices: List[CyclerDataDeviceC] = [test_source_info, test_load_info]
        self.load_source = MidDabsPwrDevC(device=[test_load_info, test_source_info])
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
        try:
            mid_meas_node.start()
            i=0
            while mid_meas_node.status is not SysShdNodeStatusE.OK:
                sleep(1)
            self.load_source.set_cc_mode(-100)
            while i<10:
                tic = time()
                log.info(f"Measuring: {gen_meas.read().voltage}mV and {gen_meas.read().current}mA")
                # log.info(f"Measuring: hs_voltage =  {ext_meas.read().hs_voltage_1} mV")
                data_ext = ext_meas.read()
                log.info(f"Measuring: external measures =   {data_ext.__dict__}")
                data_status = all_status.read()
                log.info(f"Status epc:{data_status.pwr_dev.name}")
                while time()-tic <= 1:
                    pass
                i+=1
            self.load_source.disable()
        except Exception as err:
            log.error(msg=f"Exception: {err}")
        self.load_source.close()
        self._meas_working_flag.clear()
        sleep(2)
        # self._can_working_flag.clear()
        # sleep(1)

    @fixture(scope="function")
    def config(self) -> None:
        """Configure the signal handler to signal when the SIGINT is received .
        """
        signal(SIGINT, self.signal_handler)

    @mark.parametrize("set_environ", [["SERIAL"]], indirect=["set_environ"])
    def test_normal_op(self, config, set_environ) -> None: #pylint: disable= unused-argument
        """Test the machine status .

        Args:
            set_environ ([type]): [description]
            config ([type]): [description]
        """
        log.debug(msg="1. Test mid meas")
