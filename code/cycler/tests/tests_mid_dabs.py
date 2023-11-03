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
main_logger = SysLogLoggerC(file_log_levels="code/cycler/log_config.yaml")
log: Logger = sys_log_logger_get_module_logger(name="test_mid_dabs")
from system_shared_tool import SysShdChanC
#######################       THIRD PARTY IMPORTS        #######################
from can_sniffer import DrvCanNodeC
# from scpi_sniffer import DrvScpiHandlerC
#######################          MODULE IMPORTS          #######################
sys.path.append(os.getcwd()+'/code/cycler/')
from src.wattrex_battery_cycler.mid.mid_dabs import MidDabsPwrDevC, MidDabsExtraMeterC
from wattrex_battery_cycler_datatypes.cycler_data import (CyclerDataDeviceC, CyclerDataDeviceTypeE,
                                    CyclerDataLinkConfC, CyclerDataGenMeasC, CyclerDataPwrLimitE,
                                        CyclerDataExtMeasC, CyclerDataAllStatusC)

dev_conf = {'epc': '0x14',
            'source': {'port': '/dev/ttyUSB1', 'baudrate': 115200, 'timeout': 0.1},
            'bms': 4}

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
        self.epc.close()
        self.bms.close()
        sleep(1)
        self.can.stop()

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
        # Instantiate can node
        _working_can = Event()
        _working_can.set()
        #Create the thread for CAN
        self.can = DrvCanNodeC(tx_buffer_size= 150, working_flag = _working_can, cycle_period= 30)
        self.can.start()

        # Instantiate MidDabsEpcDeviceC
        ######################################### EPC ##############################################
        test_dev1_info = CyclerDataDeviceC(dev_id= dev_conf['epc'], model = 'b', manufacturer= 'c',
                                        device_type= CyclerDataDeviceTypeE.EPC,
                                        iface_name= dev_conf['epc'],
                                        mapping_names= {'hs_voltage': 1})
        self.epc = MidDabsPwrDevC(device=[test_dev1_info])
        log.info("Can started and epc instantiate")
        gen_meas = CyclerDataGenMeasC()
        ext_meas = CyclerDataExtMeasC()
        status = CyclerDataAllStatusC()
        self.epc.update(gen_meas, ext_meas, status)
        self.epc.set_wait_mode(time_ref = 6000)
        # self.epc.set_cc_mode(500, 6000, CyclerDataPwrLimitE.TIME)
        next_time = time() + 5
        while time() < next_time:
            time_1 = time()
            self.epc.update(gen_meas, ext_meas, status)
            log.warning(f"Time to update: {time() - time_1}")
            log.info((f"Set wait mode and measuring: {gen_meas.voltage}mV "
                      f"and {gen_meas.current}mA"))
            log.info((f"Set wait mode and measuring: {status.pwr_mode.name}, "
                    f"{status.pwr_mode.value} "
                    f"and {ext_meas.hs_voltage_1}mV"))
            if status.pwr_mode.name != 'WAIT':
                next_time = time() + 5
            sleep(0.2)
        self.epc.close()
        ######################################### BMS ##############################################
        log.info("Starting test for bms")
        self.bms = MidDabsExtraMeterC(CyclerDataDeviceC(dev_id= dev_conf['bms'], model = 'b',
                                        manufacturer= 'c', device_type= CyclerDataDeviceTypeE.BMS,
                                        iface_name= dev_conf['bms'],
                                        mapping_names= {'vcell1': 1, 'vcell2': 2, 'vcell3': 3,
                                                        'vcell4': 4, 'vcell5': 5, 'vcell6': 6,
                                                        'vcell7': 7, 'vcell8': 8, 'vcell9': 9,
                                                        'vcell10': 10, 'vcell11': 11, 'vcell12': 12,
                                                        'vstack': 13, 'temp1': 14, 'temp2': 15,
                                                        'temp3': 16, 'temp4': 17, 'pres1': 18,
                                                        'pres2': 19}))
        for _ in range(5):
            self.bms.update(ext_meas, status)
            log.info((f"Measuring: {ext_meas.__dict__}"))
            log.info(f"Status: {getattr(status,'extra_meter_'+str(self.bms.device.dev_id)).name}")
            sleep(2)
        self.bms.close()
        log.info("Closing can")
        self.can.stop()
        sleep(1.5)
        # ######################################### SOURCE #########################################
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
