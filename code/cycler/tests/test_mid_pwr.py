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
main_logger = SysLogLoggerC(file_log_levels="devops/cycler/log_config.yaml",
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
        self.epc_pwr.close()
        self._meas_working_flag.clear()
        sleep(2)

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
            conf_param_epc['device_type'] = CyclerDataDeviceTypeE(conf_param_epc['device_type'])
            devices: List[CyclerDataDeviceC] = [CyclerDataDeviceC(**conf_param_epc)]
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
                                     shared_status = all_status, cycle_period = 120,
                                     working_flag = self._meas_working_flag, devices = devices,
                                     excl_tags= tags)

        ##################### PWR CONTROL #####################
        battery_info = CyclerDataPwrRangeC(volt_max=8000, volt_min=3000, curr_max=2000, curr_min=0)
        instructions = [CyclerDataInstructionC(instr_id= 1, mode= CyclerDataPwrModeE.CC_MODE,
                                ref= 1000, limit_type= CyclerDataPwrLimitE.TIME, limit_ref= 10000),
                    CyclerDataInstructionC(instr_id= 2, mode= CyclerDataPwrModeE.WAIT, ref= 10000,
                                limit_type= CyclerDataPwrLimitE.TIME, limit_ref= 10000)]
        self.epc_pwr = MidPwrControlC(devices= devices, alarm_callback= alarm_callback, #pylint: disable= attribute-defined-outside-init
                                      battery_limits= None, instruction_set= None)
        self.epc_pwr.set_new_experiment(instructions= instructions, bat_pwr_range= battery_info)
        exp_status = CyclerDataExpStatusE.QUEUED
        try:
            mid_meas_node.start()
            while mid_meas_node.status is not SysShdNodeStatusE.OK:
                sleep(1)
                log.info(f"Waiting for mid_meas_node to start. Status: {mid_meas_node.status.name}")
            while exp_status is not CyclerDataExpStatusE.FINISHED:
                tic = time()+1
                local_gen_meas = gen_meas.read()
                log.info(f"Measuring: {local_gen_meas.voltage}mV and {local_gen_meas.current}mA")
                data_ext = ext_meas.read()
                epc_ext = [f"{attr}: {data_ext.__dict__[attr]}"  for attr in data_ext.__dict__.keys()]
                log.info(f"Measuring: external measures epc=   {epc_ext}")
                data_status = all_status.read()
                log.info(f"Status epc:{data_status.pwr_dev.name}")
                log.info(f"Mode epc:{data_status.pwr_mode.name}")
                if data_status.pwr_dev.error_code != 0:
                    log.error((f"Reading error {data_status.pwr_dev.name}, "
                              f"code: {data_status.pwr_dev.error_code}"))

                ####################### SYNC WITH PWR AND EXECUTE INSTRUCTION ######################
                self.epc_pwr.update_local_data(gen_meas.read(), all_status.read())
                exp_status, inst_id =self.epc_pwr.process_iteration()
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

    @mark.parametrize("set_environ", [["EPC"]], indirect=["set_environ"])
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
