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
main_logger = SysLogLoggerC(file_log_levels="config/cycler/log_config.yaml",
                            output_sub_folder='tests')
log: Logger = sys_log_logger_get_module_logger(name="test_mid_pwr")
from system_shared_tool import SysShdSharedObjC, SysShdNodeStatusE
#######################       THIRD PARTY IMPORTS        #######################
from wattrex_cycler_datatypes.cycler_data import (CyclerDataDeviceC, CyclerDataDeviceTypeE,
                CyclerDataLinkConfC, CyclerDataGenMeasC, CyclerDataExtMeasC, CyclerDataAllStatusC,
                CyclerDataMergeTagsC, CyclerDataPwrRangeC, CyclerDataInstructionC,
                CyclerDataPwrModeE, CyclerDataPwrLimitE, CyclerDataAlarmC, CyclerDataExpStatusE)
#######################          MODULE IMPORTS          #######################
sys.path.append(os.getcwd()+'/code/cycler/')
from src.wattrex_battery_cycler.mid.mid_pwr import MidPwrControlC #pylint: disable= import-error
from src.wattrex_battery_cycler.mid.mid_meas import MidMeasNodeC #pylint: disable= import-error

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
        self.serial_pwr.close()
        self._meas_working_flag.clear()
        sleep(2)
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
            'source': {'port': '/dev/wattrex/source/EA_2963640425', 'separator':'\n',
                        'baudrate':9600, 'timeout':1, 'write_timeout':1},
            'load':{'port': '/dev/wattrex/loads/RS_79E047AE41D5', 'separator':'\n',
                        'baudrate':115200, 'timeout':1, 'write_timeout':1}
        }
        devices: List[CyclerDataDeviceC] = []
        if set(['SOURCE_LOAD']).issubset(request.param):
            test_load_info = CyclerDataDeviceC(dev_db_id= 0, model = 'b',
                                    manufacturer= 'RS', device_type= CyclerDataDeviceTypeE.LOAD,
                                    iface_name= conf_param['load']['port'],
                                    link_configuration= CyclerDataLinkConfC(**conf_param['load']),
                                    mapping_names= {'voltage': 21, 'current': 22, 'power': 23})
            test_load_info.check_power_device()
            test_source_info = CyclerDataDeviceC(dev_db_id= 1, model = 'b',
                                    manufacturer= 'EA', device_type= CyclerDataDeviceTypeE.SOURCE,
                                    iface_name= conf_param['source']['port'],
                                    link_configuration= CyclerDataLinkConfC(**conf_param['source']),
                                    mapping_names= {'voltage': 24, 'current': 25, 'power': 26})
            test_source_info.check_power_device()
            devices: List[CyclerDataDeviceC] = [test_load_info, test_source_info]
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

        ##################### PWR CONTROL #####################
        battery_info = CyclerDataPwrRangeC(volt_max=13000, volt_min=10000,
                                           curr_max=10000, curr_min=-10000)
        instructions = [
                    CyclerDataInstructionC(instr_id= 6, mode= CyclerDataPwrModeE.CC_MODE, ref= -250,
                            limit_type= CyclerDataPwrLimitE.VOLTAGE, limit_ref= 12000),
                    CyclerDataInstructionC(instr_id= 7, mode= CyclerDataPwrModeE.CV_MODE, ref= 12000,
                            limit_type= CyclerDataPwrLimitE.CURRENT, limit_ref= 50),
                    CyclerDataInstructionC(instr_id= 8, mode= CyclerDataPwrModeE.WAIT, ref= 10000,
                            limit_type= CyclerDataPwrLimitE.TIME, limit_ref= 10000),]
        # instructions = [CyclerDataInstructionC(instr_id= 1, mode= CyclerDataPwrModeE.CC_MODE,
        #                     ref= 2000, limit_type= CyclerDataPwrLimitE.VOLTAGE, limit_ref= 12500),
        #             CyclerDataInstructionC(instr_id= 2, mode= CyclerDataPwrModeE.CV_MODE, ref= 12500,
        #                     limit_type= CyclerDataPwrLimitE.CURRENT, limit_ref= 400),
        #             CyclerDataInstructionC(instr_id= 3, mode= CyclerDataPwrModeE.WAIT, ref= 10000,
        #                     limit_type= CyclerDataPwrLimitE.TIME, limit_ref= 10000),
        #             CyclerDataInstructionC(instr_id= 4, mode= CyclerDataPwrModeE.CC_MODE, ref= -1000,
        #                     limit_type= CyclerDataPwrLimitE.VOLTAGE, limit_ref= 12000),
        #             CyclerDataInstructionC(instr_id= 5, mode= CyclerDataPwrModeE.CC_MODE, ref= -500,
        #                     limit_type= CyclerDataPwrLimitE.VOLTAGE, limit_ref= 12000),
        #             CyclerDataInstructionC(instr_id= 6, mode= CyclerDataPwrModeE.CC_MODE, ref= -250,
        #                     limit_type= CyclerDataPwrLimitE.VOLTAGE, limit_ref= 12000),
        #             CyclerDataInstructionC(instr_id= 7, mode= CyclerDataPwrModeE.CV_MODE, ref= 12000,
        #                     limit_type= CyclerDataPwrLimitE.CURRENT, limit_ref= 50),
        #             CyclerDataInstructionC(instr_id= 8, mode= CyclerDataPwrModeE.WAIT, ref= 10000,
        #                     limit_type= CyclerDataPwrLimitE.TIME, limit_ref= 10000),]
        self.serial_pwr = MidPwrControlC(devices= devices, alarm_callback= alarm_callback, #pylint: disable= attribute-defined-outside-init
                                      battery_limits= None, instruction_set= None)
        self.serial_pwr.set_new_experiment(instructions= instructions, bat_pwr_range= battery_info)
        exp_status = CyclerDataExpStatusE.QUEUED
        try:
            mid_meas_node.start()
            while mid_meas_node.status is not SysShdNodeStatusE.OK:
                sleep(1)
                log.info(f"Waiting for mid_meas_node to start. Status: {mid_meas_node.status.name}")
            log.warning(f"Status devices: {all_status.read().__dict__}")
            while exp_status is not CyclerDataExpStatusE.FINISHED:
                tic = time()+1
                local_gen_meas = gen_meas.read()
                log.info(f"Measuring: {local_gen_meas.voltage}mV and {local_gen_meas.current}mA")
                data_ext = ext_meas.read()
                epc_ext = [f"{attr}:{data_ext.__dict__[attr]}" for attr in data_ext.__dict__.keys()]
                log.info(f"Measuring: external measures epc=   {epc_ext}")
                data_status = all_status.read()
                log.info(f"Status dev:{data_status.pwr_dev.name}")
                log.info(f"Mode dev:{data_status.pwr_mode.name}")
                if data_status.pwr_dev.error_code != 0:
                    log.error((f"Reading error {data_status.pwr_dev.name}, "
                              f"code: {data_status.pwr_dev.error_code}"))

                ####################### SYNC WITH PWR AND EXECUTE INSTRUCTION ######################
                self.serial_pwr.update_local_data(gen_meas.read(), all_status.read())
                exp_status, inst_id =self.serial_pwr.process_iteration()
                log.info(f"Status: {exp_status.name}, instruction: {inst_id}")

                while time()-tic < 0:
                    sleep(0.01)

        except Exception as err:
            log.error(msg=f"Exception: {err}")

        self._meas_working_flag.clear()
        sleep(2)

    @fixture(scope="function")
    def config(self) -> None:
        """Configure the signal handler to signal when the SIGINT is received .
        """
        signal(SIGINT, self.signal_handler)

    @mark.parametrize("set_environ", [["SOURCE_LOAD"]], indirect=["set_environ"])
    def test_normal_op(self, config, set_environ) -> None: #pylint: disable= unused-argument
        """Test the machine status .

        Args:
            set_environ ([type]): [description]
            config ([type]): [description]
        """
        log.debug(msg="1. Test mid power")

def alarm_callback(alarm: CyclerDataAlarmC) -> None:
    '''Callback for alarm'''
    log.error("This is a test for alarm callback")
    log.error(f"Received {alarm.__dict__}")
