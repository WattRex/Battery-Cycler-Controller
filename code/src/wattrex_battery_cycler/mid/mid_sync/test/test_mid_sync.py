#!/usr/bin/python3
"""
This file test mid sync.
COMMAND: clear && pytest mid_sync/test/test_mid_sync.py -s
"""

#######################        MANDATORY IMPORTS         #######################
import os
from sys import path

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

#######################          PROJECT IMPORTS         #######################
from wattrex_driver_db import *

#######################              ENUMS               #######################
file_data_cache = "./mid_sync/test/data_cache_mid_sync.sql"
EXP_ID = 2
MEAS_ID = 22
DATE_NOW = datetime.now()
CACHE_EXP = DrvDbCacheExperimentC(ExpID          = EXP_ID,
                                  Name           = "MID_SYNC",
                                  Description    = "MID_SYNC",
                                  DateCreation   = DATE_NOW,
                                  Status         = DrvDbExpStatusE.QUEUED.value,
                                  CSID           = 2,
                                  BatID          = 2,
                                  ProfID         = 2)

CACHE_GEN_MEAS = DrvDbCacheGenericMeasureC(ExpID = EXP_ID,
                                           MeasID = MEAS_ID,
                                           Timestamp = DATE_NOW,
                                           InstrID = 35,
                                           Voltage = 20,
                                           Current = 5,
                                           Power = 100,
                                           PwrMode = DrvDbCyclingModeE.CV.value)

CACHE_EXT_MEAS = DrvDbCacheExtendedMeasureC(ExpID = EXP_ID,
                                            MeasType = 38,
                                            MeasID = MEAS_ID,
                                            Value = 1)

CACHE_STS = DrvDbCacheStatusC(ExpID = EXP_ID,
                              DevID = 780,
                              Timestamp = DATE_NOW,
                              Status = DrvDbEquipStatusE.OK.value,
                              ErrorCode = 510)


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


    def create_enviroment(self, cache_db: DrvDbSqlEngineC):
        log.info('Adding dates to cache...')
        
        #DELETE THE DATES WITH ExpID
        for cl in [DrvDbCacheStatusC, DrvDbCacheExtendedMeasureC, DrvDbCacheGenericMeasureC, DrvDbCacheExperimentC]:
            stmt = select(cl).where(cl.ExpID == EXP_ID)
            # cache_meas.extend(cache_db.session.execute(stmt).all())
            meas = cache_db.session.execute(stmt).all()
            for m in meas:
                cache_db.session.delete(m[0])
                cache_db.commit_changes()

        #ADD DATES
        for c in [CACHE_EXP, CACHE_GEN_MEAS, CACHE_EXT_MEAS, CACHE_STS]:
            cache_db.session.add(c)
            cache_db.commit_changes()


    @fixture(scope="function", autouse=False)
    def set_environ(self, request):
        """Setup the environment variables and start the process .

        Args:
            request ([type]): [description]

        Yields:
            [type]: [description]
        """
        log.info(msg="Setting up the environment testing mid sync")
        master_db = DrvDbSqlEngineC(db_type = DrvDbTypeE.MASTER_DB,\
                                    config_file='./mid_sync/.server_cred.yaml')

        cache_db = DrvDbSqlEngineC(db_type = DrvDbTypeE.CACHE_DB,\
                                    config_file='./mid_sync/.cache_cred.yaml')
        self.create_enviroment(cache_db)

        #TODO: Inicializar sync_node y subir los datos al server.



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