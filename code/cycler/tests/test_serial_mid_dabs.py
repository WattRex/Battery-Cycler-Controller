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
from time import sleep, time
from pytest import fixture, mark
#######################      SYSTEM ABSTRACTION IMPORTS  #######################

from system_logger_tool import Logger, SysLogLoggerC, sys_log_logger_get_module_logger
main_logger = SysLogLoggerC(file_log_levels="config/cycler/log_config.yaml",
                            output_sub_folder='tests')
log: Logger = sys_log_logger_get_module_logger(name="test_mid_dabs")
# from system_shared_tool import SysShdChanC
#######################       THIRD PARTY IMPORTS        #######################
# from can_sniffer import DrvCanNodeC
from scpi_sniffer import DrvScpiSerialConfC
#######################          MODULE IMPORTS          #######################
sys.path.append(os.getcwd()+'/code/cycler/')
from src.wattrex_battery_cycler.mid.mid_dabs import MidDabsPwrDevC
from wattrex_cycler_datatypes.cycler_data import (CyclerDataDeviceC, CyclerDataDeviceTypeE,
                                CyclerDataLinkConfC, CyclerDataGenMeasC, CyclerDataExtMeasC,
                                CyclerDataPwrModeE, CyclerDataAllStatusC)
dev_conf = {'source': {'port': '/dev/wattrex/source/EA_2963640425', 'separator':'\n',
                        'baudrate':9600, 'timeout':1, 'write_timeout':1},
            'load':{'port': '/dev/wattrex/loads/RS_79E047AE41D5', 'separator':'\n',
                        'baudrate':115200, 'timeout':1, 'write_timeout':1}
            }
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

        # Instantiate MidDabsEpcDeviceC
        ######################################### EPC ##############################################
        test_load_info = CyclerDataDeviceC(dev_db_id= 0, model = 'b',
                                    manufacturer= 'RS', device_type= CyclerDataDeviceTypeE.LOAD,
                                    iface_name= dev_conf['load']['port'],
                                    link_configuration= CyclerDataLinkConfC(**dev_conf['load']),
                                    mapping_names= {'voltage': 1, 'current': 2, 'power': 3})
        test_source_info = CyclerDataDeviceC(dev_db_id= 1, model = 'b',
                                    manufacturer= 'EA', device_type= CyclerDataDeviceTypeE.SOURCE,
                                    iface_name= dev_conf['source']['port'],
                                    link_configuration= CyclerDataLinkConfC(**dev_conf['source']),
                                    mapping_names= {'voltage': 4, 'current': 5, 'power': 6})
        test_load_info.check_power_device()
        test_source_info.check_power_device()
        self.load_source = MidDabsPwrDevC(device=[test_load_info, test_source_info])
        log.info("SCPI started and load_source instantiate")
        gen_meas = CyclerDataGenMeasC()
        ext_meas = CyclerDataExtMeasC()
        status = CyclerDataAllStatusC()
        self.load_source.update(gen_meas, ext_meas, status)
        self.load_source.set_wait_mode(time_ref = 6000)
        while gen_meas.voltage < 1000:
            self.load_source.update(gen_meas, ext_meas, status)
            log.info((f"Set wait mode and measuring: {gen_meas.voltage}mV "
                      f"and {gen_meas.current}mA"))
            log.info(f"Set wait mode and measuring: {status.pwr_mode.name}, "
                     f"{status.pwr_mode.value}")
            log.info(f"External measurements: {ext_meas.__dict__}")
            sleep(1)
        log.warning(f"Source properties: {self.load_source.source.properties.__dict__}")
        log.warning(f"Load properties: {self.load_source.load.properties.__dict__}")
        input("Press Enter to continue...")
        ######################################## CV MODE ###########################################
        #################### Battery voltage lower than control voltage ############################
        self.load_source.set_cv_mode(volt_ref= 12000, limit_ref=1000, actual_voltage= gen_meas.voltage)
        next_time = time() + 10
        while time() < next_time:
            time_1 = time()
            self.load_source.update(gen_meas, ext_meas, status)
            log.warning(f"Time to update: {time() - time_1}")
            log.info((f"Set cv mode discharge and measuring: {gen_meas.voltage}mV "
                      f"and {gen_meas.current}mA"))
            log.info(f"Set cv mode discharge and reading: {status.pwr_mode.name}, "
                     f"{status.pwr_mode.value}")
            log.info(f"External measurements: {ext_meas.__dict__}")
            if status.pwr_mode != CyclerDataPwrModeE.CV_MODE:
                next_time = time() +10
            sleep(1)
        ################### Battery voltage higher than control voltage ############################
        self.load_source.update(gen_meas, ext_meas, status)
        self.load_source.set_cv_mode(volt_ref= 12500, limit_ref= 2000, actual_voltage= gen_meas.voltage)
        next_time = time() + 10
        while time() < next_time:
            time_1 = time()
            self.load_source.update(gen_meas, ext_meas, status)
            log.warning(f"Time to update: {time() - time_1}")
            log.info((f"Set cv mode charge and measuring: {gen_meas.voltage}mV "
                      f"and {gen_meas.current}mA"))
            log.info(f"Set cv mode charge and reading: {status.pwr_mode.name}, "
                     f"{status.pwr_mode.value}")
            log.info(f"External measurements: {ext_meas.__dict__}")
            if status.pwr_mode != CyclerDataPwrModeE.CV_MODE:
                next_time = time() +10
            sleep(1)
        self.load_source.disable()
        while status.pwr_mode != CyclerDataPwrModeE.WAIT:
            self.load_source.update(gen_meas, ext_meas, status)
            log.info((f"Set wait mode and measuring: {gen_meas.voltage}mV "
                      f"and {gen_meas.current}mA"))
            log.info(f"Set wait mode and measuring: {status.pwr_mode.name}, "
                     f"{status.pwr_mode.value}")
            log.info(f"External measurements: {ext_meas.__dict__}")
            sleep(1)
        ########################################  CC MODE ##########################################
        ########################################  CHARGE  ##########################################
        self.load_source.update(gen_meas, ext_meas, status)
        self.load_source.set_cc_mode(current_ref= 1000, limit_ref=12500)
        next_time = time() + 10
        while time() < next_time:
            time_1 = time()
            self.load_source.update(gen_meas, ext_meas, status)
            log.warning(f"Time to update: {time() - time_1}")
            log.info((f"Set cc mode charge and measuring: {gen_meas.voltage}mV "
                      f"and {gen_meas.current}mA"))
            log.info(f"Set cc mode charge and reading: {status.pwr_mode.name}, "
                     f"{status.pwr_mode.value}")
            log.info(f"External measurements: {ext_meas.__dict__}")
            if status.pwr_mode != CyclerDataPwrModeE.CC_MODE:
                next_time = time() +10
            sleep(1)
        ############################ DISCHARGE ############################
        self.load_source.update(gen_meas, ext_meas, status)
        self.load_source.set_cc_mode(current_ref= -1000, limit_ref= 12500)
        next_time = time() + 10
        while time() < next_time:
            time_1 = time()
            self.load_source.update(gen_meas, ext_meas, status)
            log.warning(f"Time to update: {time() - time_1}")
            log.info((f"Set cc mode discharge and measuring: {gen_meas.voltage}mV "
                      f"and {gen_meas.current}mA"))
            log.info(f"Set cc mode discharge and reading: {status.pwr_mode.name}, "
                     f"{status.pwr_mode.value}")
            log.info(f"External measurements: {ext_meas.__dict__}")
            if status.pwr_mode != CyclerDataPwrModeE.CC_MODE:
                next_time = time() +10
            sleep(1)
        self.load_source.disable()
        next_time = time() + 10
        while time() < next_time:
            time_1 = time()
            self.load_source.update(gen_meas, ext_meas, status)
            log.warning(f"Time to update: {time() - time_1}")
            log.info((f"Set wait mode and measuring: {gen_meas.voltage}mV "
                      f"and {gen_meas.current}mA"))
            log.info(f"Set wait mode and measuring: {status.pwr_mode.name}, "
                     f"{status.pwr_mode.value}")
            log.info(f"External measurements: {ext_meas.__dict__}")
            if status.pwr_mode != CyclerDataPwrModeE.WAIT:
                next_time = time() +10
            sleep(1)
        self.load_source.close()



    @fixture(scope="function")
    def config(self) -> None:
        """Configure the signal handler to signal when the SIGINT is received .
        """
        log.critical(msg="Configuring signal handler")
        signal(SIGINT, self.signal_handler)


    #Test container
    # @mark.parametrize("set_environ", [[1, 200, 3000, 'thread'],[2, 300, 4000, 'thread'],
    #                [1, 200, 3000, 'process'],[2, 300, 4000, 'process']], indirect=["set_environ"])
    @mark.parametrize("set_environ", [['code/dev_config.yaml']], indirect=["set_environ"])
    def test_normal_op(self, config, set_environ) -> None: #pylint: disable= unused-argument
        """Test the machine status .

        Args:
            set_environ ([type]): [description]
            config ([type]): [description]
        """
        log.debug(msg="1. Test SALG machine status: check machine status normal operation")
