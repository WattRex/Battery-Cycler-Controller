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
from system_config_tool import sys_conf_read_config_params
main_logger = SysLogLoggerC(file_log_levels="code/log_config.yaml")
log: Logger = sys_log_logger_get_module_logger(name="test_mid_dabs")
from system_shared_tool import SysShdSharedObjC
#######################       THIRD PARTY IMPORTS        #######################
from can_sniffer import DrvCanNodeC
#######################          MODULE IMPORTS          #######################
sys.path.append(os.getcwd()+'/code/')
from src.wattrex_battery_cycler.mid.mid_meas import MidMeasNodeC
from src.wattrex_battery_cycler.mid.mid_data import MidDataDeviceC, MidDataDeviceTypeE, \
                                                    MidDataLinkConfSerialC, \
                                                    MidDataLinkConfCanC, MidDataGenMeasC, \
                                                    MidDataExtMeasC, MidDataAllStatusC

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
        conf_param = sys_conf_read_config_params('code/tests/'+request.param[0])
        devices: List[MidDataDeviceC] = []
        if {'SOURCE','LOAD'} <= conf_param.keys():
            conf_param_dev1, conf_param_dev2 = conf_param.values()
            for conf in [conf_param_dev1, conf_param_dev2]:
                if conf['device_type'].lower() is ('source','load'):
                    conf['device_type'] = MidDataDeviceTypeE(conf['device_type'])
                    conf['link_configuration'] = MidDataLinkConfSerialC(
                        **conf['link_configuration'])
            devices: List[MidDataDeviceC] = [MidDataDeviceC(**conf_param_dev1),
                                    MidDataDeviceC(**conf_param_dev2)]
        else:
            conf_param = conf_param[next(iter(conf_param))]
            if conf_param['device_type'].lower() == 'epc':
                _can_working_flag = Event()
                _can_working_flag.set()
                can = DrvCanNodeC(tx_buffer_size= 100, working_flag = _can_working_flag)
                can.start()
                sleep(2)
                conf_param['device_type'] = MidDataDeviceTypeE(conf_param['device_type'])
                conf_param['link_configuration'] = MidDataLinkConfCanC(
                    **conf_param['link_configuration'])
            else:
                conf_param['device_type'] = MidDataDeviceTypeE(conf_param['device_type'])
                conf_param['link_configuration'] = MidDataLinkConfSerialC(
                    **conf_param['link_configuration'])
            devices: List[MidDataDeviceC] = [MidDataDeviceC(**conf_param)]
        _meas_working_flag = Event()
        _meas_working_flag.set()
        gen_meas: SysShdSharedObjC = SysShdSharedObjC(
                        MidDataGenMeasC(current=0, voltage=0, power=0))
        ext_meas: SysShdSharedObjC = SysShdSharedObjC(MidDataExtMeasC())
        all_status: SysShdSharedObjC = SysShdSharedObjC(MidDataAllStatusC())
        mid_meas_node = MidMeasNodeC(shared_gen_meas = gen_meas, shared_ext_meas = ext_meas,
                                     shared_status = all_status, cycle_period = 0.5,
                                     working_flag = _meas_working_flag, devices = devices)
        try:
            mid_meas_node.start()
            i=0
            while i<30:
                tic = time()
                log.info(f"Measuring: {gen_meas.read().voltage}mV and {gen_meas.read().current}mA")
                log.info(f"Measuring: hs_voltage =  {ext_meas.read().hs_voltage}mV")
                if all_status.read().epc_status.error_code != 0:
                    log.error((f"Reading error {all_status.read().epc_status.name}, "
                              f"code: {all_status.read().epc_status.error_code}"))
                # log.error(f"Reading error")
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
    @mark.parametrize("set_environ", [['test_meas_epc.json']],
                      indirect=["set_environ"])
    def test_normal_op(self, set_environ, config) -> None: #pylint: disable= unused-argument
        """Test the machine status .

        Args:
            set_environ ([type]): [description]
            config ([type]): [description]
        """
        log.debug(msg="1. Test mid meas")
