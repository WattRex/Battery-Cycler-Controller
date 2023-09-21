#!/usr/bin/python3
"""
This file test mid sync.
COMMAND: clear && pytest mid_sync/test/test_mid_sync.py -s
"""

#######################        MANDATORY IMPORTS         #######################
import os
from sys import path
from copy import deepcopy
#######################         GENERIC IMPORTS          #######################
# from threading import Event
from signal import signal, SIGINT
import time
from datetime import datetime
from pytest import fixture, mark
from sqlalchemy import select, text, Column, DateTime, func, Enum

#######################      SYSTEM ABSTRACTION IMPORTS  #######################
path.append(os.getcwd())
from system_logger_tool import Logger, SysLogLoggerC, sys_log_logger_get_module_logger

main_logger = SysLogLoggerC(file_log_levels="./log_config.yaml")
log: Logger = sys_log_logger_get_module_logger(name="test_mid_sync")
from system_shared_tool import SysShdSharedObjC, SysShdChanC

#######################       THIRD PARTY IMPORTS        #######################

#######################          MODULE IMPORTS          #######################
from mid_sync import *

#######################          PROJECT IMPORTS         #######################
from wattrex_driver_db import *

#######################              ENUMS               #######################
file_data_cache = "./mid_sync/test/data_cache_mid_sync.sql"
MASTER_DB = DrvDbSqlEngineC(db_type = DrvDbTypeE.MASTER_DB,\
                                    config_file='./mid_sync/.server_cred.yaml')

CACHE_DB = DrvDbSqlEngineC(db_type = DrvDbTypeE.CACHE_DB,\
                            config_file='./mid_sync/.cache_cred.yaml')
EXP_ID = 2
MEAS_ID = 22
DATE_NOW = datetime.now()
CACHE_EXP = DrvDbCacheExperimentC()
CACHE_GEN_MEAS = DrvDbCacheGenericMeasureC(ExpID = EXP_ID, MeasID = MEAS_ID, Timestamp = DATE_NOW,
                                           Voltage = 20,   Current = 5,      Power = 100,
                                           PwrMode = DrvDbCyclingModeE.CV.value)
CACHE_EXT_MEAS = DrvDbCacheExtendedMeasureC(ExpID = EXP_ID, MeasID = MEAS_ID, Value = 1)
CACHE_ALARMS = DrvDbAlarmC(ExpID = EXP_ID, AlarmID = 20, Timestamp = DATE_NOW, Code = 87, Value = 19)
CACHE_STS = DrvDbCacheStatusC(ExpID = EXP_ID, Timestamp = DATE_NOW, Status = DrvDbEquipStatusE.OK.value, ErrorCode = 510)

#######################             CLASSES              #######################

class TestChannels:
    '''A test that tests the channels in pytest.'''

    def signal_handler(self, sig, frame) -> None: #pylint: disable= unused-argument
        """Called when the user presses Ctrl + C to stop test.

        Args:
            sig ([type]): [description]
            frame ([type]): [description]
        """
        log.critical(msg='You pressed Ctrl+C! Nothing...')


    def create_enviroment(self) -> None:
        '''Create the enviroment'''
        log.info('Adding dates to cache...')
        global CACHE_GEN_MEAS, CACHE_EXT_MEAS, CACHE_ALARMS, CACHE_STS

        #PULL EXPERIMENT OF SERVER
        stmt = select(DrvDbMasterExperimentC).where(DrvDbMasterExperimentC.ExpID == EXP_ID)
        master_exp: DrvDbMasterExperimentC = MASTER_DB.session.execute(stmt).all()[0][0]
        CACHE_EXP.ExpID          = master_exp.ExpID
        CACHE_EXP.Name           = master_exp.Name
        CACHE_EXP.Description    = master_exp.Description
        CACHE_EXP.DateCreation   = master_exp.DateCreation
        CACHE_EXP.Status         = master_exp.Status
        CACHE_EXP.CSID           = master_exp.CSID
        CACHE_EXP.BatID          = master_exp.BatID
        CACHE_EXP.ProfID         = master_exp.ProfID

        #PULL INSTRUCTIONS OF SERVER
        stmt = select(DrvDbInstructionC)
        master_inst: DrvDbInstructionC = MASTER_DB.session.execute(stmt).all()[0][0]
        CACHE_GEN_MEAS.InstrID = master_inst.InstrID

        #PULL MEASURES_DECLARATION OF SERVER
        stmt = select(DrvDbMeasuresDeclarationC)
        master_meas_declarat: DrvDbMeasuresDeclarationC = MASTER_DB.session.execute(stmt).all()[0][0]
        CACHE_EXT_MEAS.MeasType = master_meas_declarat.MeasType

        #PULL USED_DEVICES OF SERVER
        stmt = select(DrvDbUsedDeviceC)
        master_meas_used_dev: DrvDbUsedDeviceC = MASTER_DB.session.execute(stmt).all()[0][0]
        CACHE_STS.DevID = master_meas_used_dev.DevID

        #DELETE THE DATES WITH ExpID IN MASTER
        for cl in [DrvDbMasterStatusC, DrvDbMasterExtendedMeasureC, DrvDbAlarmC, DrvDbMasterGenericMeasureC]:
            stmt = select(cl).where(cl.ExpID == EXP_ID)
            meas_master = MASTER_DB.session.execute(stmt).all()
            for meas in meas_master:
                MASTER_DB.session.delete(meas[0])
                MASTER_DB.commit_changes()

        #DELETE THE DATES WITH ExpID IN CACHE
        for cl in [DrvDbCacheStatusC, DrvDbCacheExtendedMeasureC, DrvDbCacheGenericMeasureC, DrvDbAlarmC, DrvDbCacheExperimentC]:
            stmt = select(cl).where(cl.ExpID == EXP_ID)
            meas_cache = CACHE_DB.session.execute(stmt).all()
            for meas in meas_cache:
                CACHE_DB.session.delete(meas[0])
                CACHE_DB.commit_changes()

        #ADD DATES IN CACHE
        for c in [CACHE_EXP, CACHE_GEN_MEAS, CACHE_EXT_MEAS, CACHE_STS, CACHE_ALARMS]:
            CACHE_DB.session.add(deepcopy(c))
            CACHE_DB.commit_changes()

    def check_push_gen_meas(self) -> bool:
        # global CACHE_GEN_MEAS
        # CACHE_GEN_MEAS = CACHE_GEN_MEAS
        log.info("Check push general measures")
        result = False
        stmt = select(DrvDbMasterGenericMeasureC).where(DrvDbMasterGenericMeasureC.ExpID == EXP_ID)
        meas_master: DrvDbMasterGenericMeasureC = MASTER_DB.session.execute(stmt).all()[0][0]
        print(meas_master.__dict__)
        print(CACHE_GEN_MEAS.__dict__)
        if CACHE_GEN_MEAS.ExpID == meas_master.ExpID and CACHE_GEN_MEAS.MeasID == meas_master.MeasID and \
           CACHE_GEN_MEAS.Timestamp == meas_master.Timestamp and CACHE_GEN_MEAS.InstrID == meas_master.InstrID and \
           CACHE_GEN_MEAS.Voltage == meas_master.Voltage and CACHE_GEN_MEAS.Current == meas_master.Current and \
           CACHE_GEN_MEAS.Power == meas_master.Power and CACHE_GEN_MEAS.PwrMode == meas_master.PwrMode:
            result = True
        print(result)
        return result


    @fixture(scope="function", autouse=False)
    def set_environ(self, request):
        """Setup the environment variables and start the process .

        Args:
            request ([type]): [description]

        Yields:
            [type]: [description]
        """
        log.info(msg="Setting up the environment testing mid sync")
        self.create_enviroment()
        sync_node = MidSyncNodeC(comp_unit=1, cycle_period=1)
        sync_node.process_iterarion()
        self.check_push_gen_meas()
        # a = self.check_push_correct_meas(class_name = DrvDbMasterExtendedMeasureC(),  meas_cache = CACHE_EXT_MEAS)
        # b = self.check_push_correct_meas(type_class = DrvDbMasterGenericMeasureC(),   meas_cache = CACHE_GEN_MEAS )
        # c = self.check_push_correct_meas(type_class = DrvDbMasterStatusC(),           meas_cache = CACHE_STS)
        # log.critical(f"A: {a}   b: {b}  c:{c}")
        # log.critical(f"A: {a}")


    @fixture(scope="function")
    def config(self) -> None:
        """Configure the signal handler to signal when the SIGINT is received .
        """
        signal(SIGINT, self.signal_handler)


    #Test container
    @mark.parametrize("set_environ", [750], indirect=["set_environ"])

    def test_normal_op(self, set_environ, config) -> None: #pylint: disable= unused-argument
        """Test the machine status .

        Args:
            set_environ ([type]): [description]
            config ([type]): [description]
        """
        log.debug(msg="1. Test MID SYNC.")

#######################            FUNCTIONS             #######################