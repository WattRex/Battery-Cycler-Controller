#!/usr/bin/python3
"""
This file test sys shd node.
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

main_logger = SysLogLoggerC(file_log_levels="config/cycler/log_config.yaml")
log: Logger = sys_log_logger_get_module_logger(name="test_mid_str")
from system_shared_tool import SysShdSharedObjC, SysShdChanC
#######################       THIRD PARTY IMPORTS        #######################

#######################          MODULE IMPORTS          #######################
sys.path.append(os.getcwd()+'/code/')
from src.wattrex_battery_cycler.mid.mid_str import MidStrFacadeC, MidStrNodeC
from src.wattrex_battery_cycler.mid.mid_data import MidDataExtMeasC, MidDataAllStatusC,\
    MidDataGenMeasC, MidDataDeviceStatusC
from src.wattrex_battery_cycler.mid.mid_meas import MidMeasNodeC
#######################          PROJECT IMPORTS         #######################

#######################              ENUMS               #######################

#######################             CLASSES              #######################

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
        log.info(msg="Setting up the environment Node testing mid storage")
        __str_flag_node = Event()
        __str_flag_node.set()
        shared_gen_meas = SysShdSharedObjC(shared_obj=MidDataGenMeasC)
        shared_ext_meas = SysShdSharedObjC(shared_obj=MidDataExtMeasC)
        shared_all_status = SysShdSharedObjC(shared_obj=MidDataAllStatusC)
        str_node = MidStrNodeC(name= 'dummyNode', cycle_period=request.param[0],
                        working_flag= __str_flag_node, shared_gen_meas= shared_gen_meas,
                        shared_ext_meas= shared_ext_meas, shared_status= shared_all_status,
                        str_reqs= SysShdChanC(), str_alarms= SysShdChanC(), str_data= SysShdChanC(),
                        cycler_station= 1, master_file= 'code/tests/.cred_master.yaml',
                        cache_file= 'code/tests/.cred_cache.yaml')
        str_node.start()
        log.info("Mid Storage Node started")
        log.info("Uploading random measures to shared objects to test the node")
        gen_meas = MidDataGenMeasC(pwr_mode= 0, voltage= 1000, current= 34, power= 0)
        ext_meas = MidDataExtMeasC(temp= 25, humidity= 50, pressure= 1000)
        all_status = MidDataAllStatusC()
        all_status.epc= MidDataDeviveStatusC(0)
        shared_gen_meas.write(new_obj= gen_meas)
        shared_ext_meas.write(new_obj= ext_meas)
        shared_all_status.write(new_obj= all_status)
        log.info("Waiting for the node to finish 10 cycles")
        sleep(10)
        __str_flag_node.clear()
        str_node.join()

    @fixture(scope="function")
    def config(self) -> None:
        """Configure the signal handler to signal when the SIGINT is received .
        """
        signal(SIGINT, self.signal_handler)


    #Test container
    @mark.parametrize("set_environ", [[750],
                                      [500]],\
                indirect=["set_environ"])
    def test_normal_op(self, set_environ, config) -> None: #pylint: disable= unused-argument
        """Test the machine status .

        Args:
            set_environ ([type]): [description]
            config ([type]): [description]
        """
        log.debug(msg="1. Test SALG machine status: check machine status normal operation")

#######################            FUNCTIONS             #######################
