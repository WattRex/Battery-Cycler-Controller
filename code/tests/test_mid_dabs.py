#!/usr/bin/python3
"""
This file test mid_dabs and show how it works.
"""

#######################        MANDATORY IMPORTS         #######################
import os
import sys

#######################         GENERIC IMPORTS          #######################
from threading import Event
from signal import signal, SIGINT
from time import sleep
from pytest import fixture, mark

#######################      SYSTEM ABSTRACTION IMPORTS  #######################
from system_logger_tool import Logger, SysLogLoggerC, sys_log_logger_get_module_logger
from system_config_tool import sys_conf_read_config_params
main_logger = SysLogLoggerC(file_log_levels="code/log_config.yaml")
log: Logger = sys_log_logger_get_module_logger(name="test_mid_dabs")
from system_shared_tool import SysShdChanC
#######################       THIRD PARTY IMPORTS        #######################
from can_sniffer import DrvCanNodeC
#######################          MODULE IMPORTS          #######################
sys.path.append(os.getcwd()+'/code/')
from src.wattrex_battery_cycler.mid.mid_dabs import MidDabsEpcDevC
from src.wattrex_battery_cycler.mid.mid_data import MidDataDeviceC, MidDataDeviceTypeE, MidDataPwrLimitE

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
        dev_file = request.param[0]
        dev_conf = sys_conf_read_config_params(dev_file)
        # Instantiate can node
        tx_queue = SysShdChanC(10000)
        _working_can = Event()
        _working_can.set()
        #Create the thread for CAN
        can = DrvCanNodeC(tx_queue, _working_can)
        can.start()
        # Instantiate MidDabsEpcDeviceC
        dev_info = MidDataDeviceC('a', 'b', 'c', MidDataDeviceTypeE.EPC, 'd', {'e': 0})
        epc = MidDabsEpcDevC(dev_info,dev_conf,tx_queue)
        log.info("Can started and epc instantiate")

        try:
            epc.set_wait_mode(MidDataPwrLimitE.TIME, 30000)
        except Exception as exc:
            raise AssertionError("Error while trying to set wait mode for 30s") from exc
        for i in range(0,5):
            if epc.__epc.get_mode().mode.value == 0 and i != 1:
                log.info("Correctly set wait mode")
                break
            sleep(1)



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
