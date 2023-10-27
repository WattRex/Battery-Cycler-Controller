#!/usr/bin/python3
"""
This file test mid_dabs and show how it works.
"""

#######################        MANDATORY IMPORTS         #######################
import os
import sys
from subprocess import run, PIPE

#######################         GENERIC IMPORTS          #######################
from threading import Event
from signal import signal, SIGINT
from time import sleep
from pytest import fixture, mark
from datetime import datetime as dt
#######################      SYSTEM ABSTRACTION IMPORTS  #######################
from system_logger_tool import Logger, SysLogLoggerC, sys_log_logger_get_module_logger
# from system_config_tool import sys_conf_read_config_params
main_logger = SysLogLoggerC(file_log_levels="code/cycler/log_config.yaml")
log: Logger = sys_log_logger_get_module_logger(name="test_mid_dabs")
from system_shared_tool import SysShdChanC
#######################       THIRD PARTY IMPORTS        #######################
from can_sniffer import DrvCanNodeC
from scpi_sniffer import DrvScpiHandlerC
#######################          MODULE IMPORTS          #######################
sys.path.append(os.getcwd()+'/code/cycler/')
from src.wattrex_battery_cycler.mid.mid_dabs import MidDabsPwrDevC
from wattrex_battery_cycler_datatypes.cycler_data import (CyclerDataDeviceC, CyclerDataDeviceTypeE,
                                    CyclerDataLinkConfC, CyclerDataGenMeasC,
                                        CyclerDataExtMeasC, CyclerDataAllStatusC)

dev_conf = {'epc': '0x11',
            'source': {'port': '/dev/ttyUSB1', 'baudrate': 115200, 'timeout': 0.1}}

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
    def set_environ(self, request):
        """Setup the environment variables and start the process .

        Args:
            request ([type]): [description]

        Yields:
            [type]: [description]
        """
        log.info(msg="Setup environment for test mid dabs test")
        # run(['sudo', 'ip', 'link', 'set', 'down', 'can0'], stdout=PIPE, stderr=PIPE)
        # run(['sudo', 'ip', 'link', 'set', 'up', 'txqueuelen', '10000', 'can0', 'type', 'can',
        #     'bitrate', '125000'], stdout=PIPE, stderr=PIPE)
        dev_file = request.param[0]
        # dev_conf = sys_conf_read_config_params(dev_file)
        # Instantiate can node
        tx_queue = SysShdChanC(10000)
        _working_can = Event()
        _working_can.set()
        #Create the thread for CAN
        can = DrvCanNodeC(tx_buffer_size= 150, working_flag = _working_can)
        can.start()
        # Instantiate MidDabsEpcDeviceC
        test_dev1_info = CyclerDataDeviceC(dev_id= dev_conf['epc'], model = 'b', manufacturer= 'c',
                                        device_type= CyclerDataDeviceTypeE.EPC,
                                        iface_name= dev_conf['epc'],
                                        mapping_names= {'hs_voltage': 'hs_voltage'})
        epc = MidDabsPwrDevC(device=[test_dev1_info])
        log.info("Can started and epc instantiate")
        gen_meas = CyclerDataGenMeasC()
        ext_meas = CyclerDataExtMeasC()
        status = CyclerDataAllStatusC()

        try:
            epc.set_wait_mode(time_ref = 30000)
        except Exception as exc:
            raise AssertionError("Error while trying to set wait mode for 30s") from exc
        for i in range(0,5):
            epc.update(gen_meas, ext_meas, status)
            log.info((f"Set wait mode and measuring: {gen_meas.voltage}mV "
                      f"and {gen_meas.current}mA"))
            log.info((f"Set wait mode and measuring: {status.pwr_mode.name} "
                     f"and {ext_meas.hs_voltage}mV"))
            if status.pwr_mode.value == 0 and i != 1:
                log.info("Correctly set wait mode")
                break
            sleep(1)
        epc.disable()
        epc.close()
        # run(['sudo', 'ip', 'link', 'set', 'down', 'can0'], stdout=PIPE, stderr=PIPE)
        # log.info("Starting test for ea source")
        # test_dev2_info = CyclerDataDeviceC(iface_name = dev_conf['source']['port'] , model = 'b',
        #                             manufacturer = 'c', device_type= CyclerDataDeviceTypeE.SOURCE,
        #                             link_configuration= CyclerDataLinkConfC(**dev_conf['source']))
        # ea_source = MidDabsPwrDevC(test_dev2_info, tx_queue)

        # ea_source.set_cv_mode(5000, 500)
        # for i in range(0,5):
        #     ea_meas = ea_source.update()
        #     log.info((f"Set {ea_meas.mode} with 5V 0.5A and measuring: {ea_meas.voltage}V "
        #              f"and {ea_meas.current}A"))
        #     sleep(1)
        # ea_source.disable()
        # ea_source.close()



    @fixture(scope="function")
    def config(self) -> None:
        """Configure the signal handler to signal when the SIGINT is received .
        """
        signal(SIGINT, self.signal_handler)


    #Test container
    # @mark.parametrize("set_environ", [[1, 200, 3000, 'thread'],[2, 300, 4000, 'thread'],
    #                [1, 200, 3000, 'process'],[2, 300, 4000, 'process']], indirect=["set_environ"])
    @mark.parametrize("set_environ", [['code/dev_config.yaml']], indirect=["set_environ"])
    def test_normal_op(self, set_environ, config) -> None: #pylint: disable= unused-argument
        """Test the machine status .

        Args:
            set_environ ([type]): [description]
            config ([type]): [description]
        """
        log.debug(msg="1. Test SALG machine status: check machine status normal operation")
