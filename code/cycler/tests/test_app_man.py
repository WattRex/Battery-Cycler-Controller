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
main_logger = SysLogLoggerC(file_log_levels="devops/cycler/log_config.yaml")
log: Logger = sys_log_logger_get_module_logger(name="test_app_man")

#######################       THIRD PARTY IMPORTS        #######################
from sqlalchemy import delete
from wattrex_driver_db import (DrvDbSqlEngineC, DrvDbCacheStatusC, DrvDbCacheExtendedMeasureC,
                    DrvDbCacheGenericMeasureC, DrvDbCacheExperimentC, DrvDbCacheStatusC, DrvDbTypeE)
#######################          MODULE IMPORTS          #######################
sys.path.append(os.getcwd()+'/code/cycler/')
from src.wattrex_battery_cycler.app.app_man import AppManNodeC



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
        self.working_flag.clear()
        sleep(3)
        sys.exit(0)

    @fixture(scope="function", autouse=False)
    def set_environ(self, request):
        """Setup the environment variables and start the process .

        Args:
            request ([type]): [description]

        Yields:
            [type]: [description]
        """
        log.info(msg="Setup environment for test mid dabs test")
        delete_cache_data()
        self.working_flag: Event = Event()
        self.working_flag.set()
        manager: AppManNodeC = AppManNodeC(cs_id= 21, cycle_period= 350,
                                           working_flag= self.working_flag)
        try:
            sleep(1)
            manager.run()
        except KeyboardInterrupt:
            self.working_flag.clear()
            sleep(1)


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

def delete_cache_data()->None:
    """Delete all cached data from the cache database
    """
    cache_db = DrvDbSqlEngineC(config_file= 'devops/.cred.yaml',
                            db_type= DrvDbTypeE.CACHE_DB)
    stmt = delete(DrvDbCacheStatusC).where(DrvDbCacheStatusC.ExpID == 6)
    cache_db.session.execute(stmt)
    stmt = delete(DrvDbCacheExtendedMeasureC).where(DrvDbCacheExtendedMeasureC.ExpID == 6)
    cache_db.session.execute(stmt)
    stmt = delete(DrvDbCacheGenericMeasureC).where(DrvDbCacheGenericMeasureC.ExpID == 6)
    cache_db.session.execute(stmt)
    stmt = delete(DrvDbCacheExperimentC).where(DrvDbCacheExperimentC.ExpID == 6)
    cache_db.session.execute(stmt)
    cache_db.session.commit()
    cache_db.session.close()
