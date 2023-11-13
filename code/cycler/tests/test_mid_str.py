#!/usr/bin/python3
"""
This file test sys shd node.
"""

#######################        MANDATORY IMPORTS         #######################
import os
import sys
from typing import Tuple
#######################         GENERIC IMPORTS          #######################
from threading import Event
from signal import signal, SIGINT
from time import sleep
from pytest import fixture, mark

#######################      SYSTEM ABSTRACTION IMPORTS  #######################
from system_logger_tool import Logger, SysLogLoggerC, sys_log_logger_get_module_logger

main_logger = SysLogLoggerC(file_log_levels="devops/log_config.yaml")
log: Logger = sys_log_logger_get_module_logger(name="test_mid_str")
from system_shared_tool import SysShdSharedObjC, SysShdChanC
#######################       THIRD PARTY IMPORTS        #######################
from wattrex_battery_cycler_datatypes.cycler_data import (CyclerDataExtMeasC, CyclerDataAllStatusC,
    CyclerDataGenMeasC, CyclerDataBatteryC, CyclerDataCyclerStationC, CyclerDataExperimentC,
    CyclerDataExpStatusE, CyclerDataProfileC, CyclerDataDeviceStatusC, CyclerDataPwrModeE)
from wattrex_driver_db import (DrvDbSqlEngineC, DrvDbTypeE, DrvDbCacheStatusC,
                DrvDbCacheExtendedMeasureC, DrvDbCacheGenericMeasureC, DrvDbCacheExperimentC)
from sqlalchemy import select, delete
#######################          MODULE IMPORTS          #######################
sys.path.append(os.getcwd()+'/code/cycler/')
from src.wattrex_battery_cycler.mid.mid_str import (MidStrNodeC, MidStrCmdDataC, MidStrReqCmdE,
                                                    MidStrDataCmdE)
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
        log.info(msg="Removing all data from cache database asociated to test")
        delete_cache_data()

        __str_flag_node = Event()
        __str_flag_node.set()
        shared_gen_meas: SysShdSharedObjC
        shared_ext_meas: SysShdSharedObjC
        str_reqs: SysShdChanC = SysShdChanC()
        str_alarms: SysShdChanC = SysShdChanC()
        str_data: SysShdChanC = SysShdChanC()
        shared_gen_meas = SysShdSharedObjC(shared_obj=CyclerDataGenMeasC())
        shared_ext_meas = SysShdSharedObjC(shared_obj=CyclerDataExtMeasC())
        shared_all_status = SysShdSharedObjC(shared_obj=CyclerDataAllStatusC())
        str_node = MidStrNodeC(name= 'dummyNode', cycle_period=request.param[0],
                        working_flag= __str_flag_node, shared_gen_meas= shared_gen_meas,
                        shared_ext_meas= shared_ext_meas, shared_status= shared_all_status,
                        str_reqs= str_reqs, str_alarms= str_alarms, str_data= str_data,
                        cycler_station= 2, cred_file= 'devops/.cred.yaml')
        str_node.start()
        log.info("Mid Storage Node started")
        log.info(f"Cycler station info retrieved {get_cs_info(str_reqs, str_data).__dict__}")
        experiment, battery, profile = fetch_new_exp(str_reqs, str_data)
        log.info(f"New experiment retrieved {experiment.__dict__}")
        log.info(f"New battery retrieved {battery.__dict__}")
        log.info(f"New profile retrieved {profile.__dict__}")
        log.info("Uploading random measures to shared objects to test the node")
        all_status = CyclerDataAllStatusC()
        all_status.pwr_mode= CyclerDataPwrModeE.WAIT
        all_status.pwr_dev= CyclerDataDeviceStatusC(0,2)
        gen_meas = CyclerDataGenMeasC(voltage= 1000, current= 34, power= 0, instr_id = 1)
        ext_meas = CyclerDataExtMeasC()
        ext_meas.hs_voltage_1 = 3000
        ext_meas.temp_body_2 = 211
        ext_meas.temp_amb_3 = -115
        shared_gen_meas.write(new_obj= gen_meas)
        shared_ext_meas.write(new_obj= ext_meas)
        shared_all_status.write(new_obj= all_status)
        log.info("Waiting for the node to finish for 10s")
        sleep(10)
        write_exp_status(str_reqs, CyclerDataExpStatusE.ERROR)
        sleep(1)
        __str_flag_node.clear()
        str_node.join()

    @fixture(scope="function")
    def config(self) -> None:
        """Configure the signal handler to signal when the SIGINT is received .
        """
        signal(SIGINT, self.signal_handler)


    #Test container
    @mark.parametrize("set_environ", [[500]], indirect=["set_environ"])
    def test_normal_op(self, set_environ, config) -> None: #pylint: disable= unused-argument
        """Test the machine status .

        Args:
            set_environ ([type]): [description]
            config ([type]): [description]
        """
        log.debug(msg="1. Test SALG machine status: check machine status normal operation")

#######################            FUNCTIONS             #######################

def get_cs_info(chan_str_reqs: SysShdChanC, chan_str_data: SysShdChanC) -> CyclerDataCyclerStationC:
    """Get the cycler station info from the database

    Returns:
        CyclerDataCyclerStationC: Cycler station info
    """
    request: MidStrCmdDataC = MidStrCmdDataC(cmd_type= MidStrReqCmdE.GET_CS)
    chan_str_reqs.send_data(request)
    response: MidStrCmdDataC = chan_str_data.receive_data()
    if response.cmd_type != MidStrDataCmdE.CS_DATA:
        raise ValueError(("Unexpected response from MID_STR, expected CS_DATA "
                            f"and got {response.cmd_type}"))
    return response.station

def fetch_new_exp(chan_str_reqs: SysShdChanC, chan_str_data: SysShdChanC) -> \
            Tuple[CyclerDataExperimentC, CyclerDataBatteryC, CyclerDataProfileC]:
    """AI is creating summary for fetch_new_exp

    Raises:
        ValueError: [description]

    Returns:
        Tuple[CyclerDataExperimentC, CyclerDataBatteryC, CyclerDataProfileC]: [description]
    """
    log.debug("Checking for new experiments")
    request: MidStrCmdDataC = MidStrCmdDataC(cmd_type= MidStrReqCmdE.GET_NEW_EXP)
    chan_str_reqs.send_data(request)
    response: MidStrCmdDataC = chan_str_data.receive_data()
    while response.cmd_type != MidStrDataCmdE.EXP_DATA:
        response: MidStrCmdDataC = chan_str_data.receive_data()
        # raise ValueError(("Unexpected response from MID_STR, expected EXP_DATA "
        #                   f"and got {response.cmd_type}"))
    return response.experiment, response.battery, response.profile

def write_exp_status(chan_str_reqs: SysShdChanC,
                        exp_status: CyclerDataExpStatusE) -> None:
    """Write the experiment status in the shared memory

    Args:
        exp_status (CyclerDataExpStatusE): Experiment status
    """
    request: MidStrCmdDataC = MidStrCmdDataC(cmd_type= MidStrReqCmdE.SET_EXP_STATUS,
                    exp_status= exp_status)
    chan_str_reqs.send_data(request)

def delete_cache_data()->None:
    """Delete all cached data from the cache database
    """
    cache_db = DrvDbSqlEngineC(config_file= 'devops/.cred.yaml',
                            db_type= DrvDbTypeE.CACHE_DB, section= 'cache_db')
    stmt = delete(DrvDbCacheStatusC).where(DrvDbCacheStatusC.ExpID == 1)
    cache_db.session.execute(stmt)
    stmt = delete(DrvDbCacheExtendedMeasureC).where(DrvDbCacheExtendedMeasureC.ExpID == 1)
    cache_db.session.execute(stmt)
    stmt = delete(DrvDbCacheGenericMeasureC).where(DrvDbCacheGenericMeasureC.ExpID == 1)
    cache_db.session.execute(stmt)
    stmt = delete(DrvDbCacheExperimentC).where(DrvDbCacheExperimentC.ExpID == 1)
    cache_db.session.execute(stmt)
    cache_db.session.commit()
    cache_db.session.close()
