#!/usr/bin/python3
"""
This file test db sync.
COMMAND: clear && pytest db_sync/tests/test_db_sync.py -s
"""

#######################        MANDATORY IMPORTS         #######################
import os
import sys
#######################         GENERIC IMPORTS          #######################
from threading import Event
from time import sleep
from signal import signal, SIGINT
from pytest import fixture, mark
from sqlalchemy import select, text, delete

#######################      SYSTEM ABSTRACTION IMPORTS  #######################
sys.path.append(os.getcwd())
from system_logger_tool import Logger, SysLogLoggerC, sys_log_logger_get_module_logger
main_logger = SysLogLoggerC(file_log_levels="devops/db_sync/log_config.yaml",
                            output_sub_folder='tests')
log: Logger = sys_log_logger_get_module_logger(name="test_db_sync")

#######################       THIRD PARTY IMPORTS        #######################

#######################          PROJECT IMPORTS         #######################
from wattrex_driver_db import (DrvDbSqlEngineC, DrvDbTypeE, DrvDbMasterExperimentC,
                               DrvDbCacheExperimentC, DrvDbCacheExtendedMeasureC,
                               DrvDbCacheGenericMeasureC, DrvDbCacheStatusC)

#######################          MODULE IMPORTS          #######################
sys.path.append(os.getcwd()+'/code/db_sync/')
from src.wattrex_battery_cycler_db_sync import DbSyncNodeC


#######################              ENUMS               #######################

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
        self.working_flag.clear()


    def create_enviroment(self, cred_file: str) -> None:
        '''Create the enviroment'''
        log.info('Deleting data from cache...')
        cache_db = DrvDbSqlEngineC(db_type= DrvDbTypeE.CACHE_DB, config_file= cred_file)
        stmt = delete(DrvDbCacheStatusC).where(DrvDbCacheStatusC.ExpID == 4)
        cache_db.session.execute(stmt)
        stmt = delete(DrvDbCacheExtendedMeasureC).where(DrvDbCacheExtendedMeasureC.ExpID == 4)
        cache_db.session.execute(stmt)
        stmt = delete(DrvDbCacheGenericMeasureC).where(DrvDbCacheGenericMeasureC.ExpID == 4)
        cache_db.session.execute(stmt)
        stmt = delete(DrvDbCacheExperimentC).where(DrvDbCacheExperimentC.ExpID == 4)
        cache_db.session.execute(stmt)
        cache_db.session.commit()
        log.info('Adding data to cache...')
        for stmt in cache_exp_4_stmt:
            cache_db.session.execute(text(stmt))
        cache_db.session.commit()
        cache_db.close_connection()
        log.info('Removing data from master...')
        master_db = DrvDbSqlEngineC(db_type= DrvDbTypeE.MASTER_DB, config_file= cred_file)
        for stmt in master_exp_4_stmt:
            master_db.session.execute(text(stmt))
            master_db.session.commit()
        sleep(2)
        master_db.close_connection()

    def check_push_exp(self, master_con: DrvDbSqlEngineC) -> bool:
        """Check if the experiment is pushed correctly.
        """
        log.info("Check push general measures")
        result = False
        stmt = select(DrvDbMasterExperimentC).where(DrvDbMasterExperimentC.ExpID == 4)
        master_meas: DrvDbMasterExperimentC = master_con.session.execute(stmt).one()[0]
        cache_dict = {"ExpID": 4, 'Name': 'Prueba Rob Sync','Description':'Experimento prueba SYNC',
                      "DateCreation":'2023-10-18 06:57:00', "DateBegin": '2023-11-17 14:12:33',
                      "DateFinish": '2023-11-17 14:12:35', "Status": 'FINISHED', "CSID": 31,
                      "BatID": 2, "ProfID": 2}
        cache_meas: DrvDbCacheExperimentC = DrvDbCacheExperimentC(**cache_dict)
        if (cache_meas.ExpID == master_meas.ExpID and # pylint: disable=too-many-boolean-expressions
            cache_meas.Description == master_meas.Description and
            cache_meas.Name == master_meas.Name and
            cache_meas.Status == master_meas.Status and
            cache_meas.DateCreation == str(master_meas.DateCreation) and
            cache_meas.DateBegin == str(master_meas.DateBegin) and
            cache_meas.DateFinish == str(master_meas.DateFinish) and
            cache_meas.CSID == master_meas.CSID and
            cache_meas.BatID == master_meas.BatID and
            cache_meas.ProfID == master_meas.ProfID):
            result = True
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
        self.create_enviroment(request.param)
        self.working_flag: Event = Event() #pylint: disable=attribute-defined-outside-init
        self.working_flag.set()
        sync_node = DbSyncNodeC(comp_unit=1, cycle_period=1000, working_flag= self.working_flag)
        sync_node.start()
        sleep(5)
        master_db = DrvDbSqlEngineC(db_type= DrvDbTypeE.MASTER_DB, config_file= request.param)
        if not self.check_push_exp(master_con= master_db):
            raise AssertionError("The sync between master and cache is not correct")
        log.info("The sync between master and cache is correct")
        self.working_flag.clear()
        sync_node.join()


    @fixture(scope="function")
    def config(self) -> None:
        """Configure the signal handler to signal when the SIGINT is received .
        """
        signal(SIGINT, self.signal_handler)


    #Test container
    @mark.parametrize("set_environ", ['devops/.cred.yaml'], indirect=["set_environ"])

    def test_normal_op(self, set_environ, config) -> None: #pylint: disable= unused-argument
        """Test the machine status .

        Args:
            set_environ ([type]): [description]
            config ([type]): [description]
        """
        log.debug(msg="1. Test MID SYNC.")

#######################            FUNCTIONS             #######################

cache_exp_4_stmt= [("INSERT INTO `Experiment` (`ExpID`, `Name`, `Description`, `DateCreation`, "
                    "`DateBegin`, `DateFinish`, `Status`, `CSID`, `BatID`, `ProfID`) VALUES "
                    "(4, 'Prueba Rob Sync', 'Experimento prueba SYNC', '2023-10-18 06:57:00', "
                    "'2023-11-17 14:12:33', '2023-11-17 14:12:35', 'FINISHED', 31, 2, 2);"),
("INSERT INTO `GenericMeasures` (`ExpID`, `MeasID`, `Timestamp`, `InstrID`, `Voltage`, `Current`, "
            "`Power`, `PowerMode`) VALUES (4, 10, '2023-11-17 12:40:08', 1, 1000, 34, 0, 'WAIT');"),
("INSERT INTO `GenericMeasures` (`ExpID`, `MeasID`, `Timestamp`, `InstrID`, `Voltage`, `Current`, "
            "`Power`, `PowerMode`) VALUES (4, 9, '2023-11-17 12:40:07', 1, 1000, 34, 0, 'WAIT');"),
("INSERT INTO `GenericMeasures` (`ExpID`, `MeasID`, `Timestamp`, `InstrID`, `Voltage`, `Current`, "
            "`Power`, `PowerMode`) VALUES (4, 8, '2023-11-17 12:40:07', 1, 1000, 34, 0, 'WAIT');"),
("INSERT INTO `GenericMeasures` (`ExpID`, `MeasID`, `Timestamp`, `InstrID`, `Voltage`, `Current`, "
            "`Power`, `PowerMode`) VALUES (4, 7, '2023-11-17 12:40:06', 1, 1000, 34, 0, 'WAIT');"),
("INSERT INTO `GenericMeasures` (`ExpID`, `MeasID`, `Timestamp`, `InstrID`, `Voltage`, `Current`, "
            "`Power`, `PowerMode`) VALUES (4, 6, '2023-11-17 12:40:06', 1, 1000, 34, 0, 'WAIT');"),
("INSERT INTO `GenericMeasures` (`ExpID`, `MeasID`, `Timestamp`, `InstrID`, `Voltage`, `Current`, "
            "`Power`, `PowerMode`) VALUES (4, 5, '2023-11-17 12:40:05', 1, 1000, 34, 0, 'WAIT');"),
("INSERT INTO `GenericMeasures` (`ExpID`, `MeasID`, `Timestamp`, `InstrID`, `Voltage`, `Current`, "
            "`Power`, `PowerMode`) VALUES (4, 4, '2023-11-17 12:40:05', 1, 1000, 34, 0, 'WAIT');"),
("INSERT INTO `GenericMeasures` (`ExpID`, `MeasID`, `Timestamp`, `InstrID`, `Voltage`, `Current`, "
            "`Power`, `PowerMode`) VALUES (4, 3, '2023-11-17 12:40:04', 1, 1000, 34, 0, 'WAIT');"),
("INSERT INTO `GenericMeasures` (`ExpID`, `MeasID`, `Timestamp`, `InstrID`, `Voltage`, `Current`, "
            "`Power`, `PowerMode`) VALUES (4, 2, '2023-11-17 12:40:04', 1, 1000, 34, 0, 'WAIT');"),
("INSERT INTO `GenericMeasures` (`ExpID`, `MeasID`, `Timestamp`, `InstrID`, `Voltage`, `Current`, "
            "`Power`, `PowerMode`) VALUES (4, 1, '2023-11-17 12:40:03', 1, 1000, 34, 0, 'WAIT');"),
("INSERT INTO `GenericMeasures` (`ExpID`, `MeasID`, `Timestamp`, `InstrID`, `Voltage`, `Current`, "
            "`Power`, `PowerMode`) VALUES (4, 0, '2023-11-17 12:40:03', 1, 1000, 34, 0, 'WAIT');"),
("INSERT INTO `ExtendedMeasures` (`MeasID`, `ExpID`, `UsedMeasID`, `Value`) "
                                                                    "VALUES (0, 4, 1, 5000);"),
("INSERT INTO `ExtendedMeasures` (`MeasID`, `ExpID`, `UsedMeasID`, `Value`) "
                                                                    "VALUES (1, 4, 1, 3000);"),
("INSERT INTO `ExtendedMeasures` (`MeasID`, `ExpID`, `UsedMeasID`, `Value`) "
                                                                    "VALUES (2, 4, 1, 3000);"),
("INSERT INTO `ExtendedMeasures` (`MeasID`, `ExpID`, `UsedMeasID`, `Value`) "
                                                                    "VALUES (3, 4, 1, 3000);"),
("INSERT INTO `ExtendedMeasures` (`MeasID`, `ExpID`, `UsedMeasID`, `Value`) "
                                                                    "VALUES (4, 4, 1, 3000);"),
("INSERT INTO `ExtendedMeasures` (`MeasID`, `ExpID`, `UsedMeasID`, `Value`) "
                                                                    "VALUES (5, 4, 1, 3000);"),
("INSERT INTO `ExtendedMeasures` (`MeasID`, `ExpID`, `UsedMeasID`, `Value`) "
                                                                    "VALUES (6, 4, 1, 3000);"),
("INSERT INTO `ExtendedMeasures` (`MeasID`, `ExpID`, `UsedMeasID`, `Value`) "
                                                                    "VALUES (7, 4, 1, 3000);"),
("INSERT INTO `ExtendedMeasures` (`MeasID`, `ExpID`, `UsedMeasID`, `Value`) "
                                                                    "VALUES (8, 4, 1, 3000);"),
("INSERT INTO `ExtendedMeasures` (`MeasID`, `ExpID`, `UsedMeasID`, `Value`) "
                                                                    "VALUES (9, 4, 1, 3000);"),
("INSERT INTO `ExtendedMeasures` (`MeasID`, `ExpID`, `UsedMeasID`, `Value`) "
                                                                    "VALUES (10, 4, 1, 3000);"),
("INSERT INTO `ExtendedMeasures` (`MeasID`, `ExpID`, `UsedMeasID`, `Value`) "
                                                                    "VALUES (0, 4, 2, 211);"),
("INSERT INTO `ExtendedMeasures` (`MeasID`, `ExpID`, `UsedMeasID`, `Value`) "
                                                                    "VALUES (1, 4, 2, 211);"),
("INSERT INTO `ExtendedMeasures` (`MeasID`, `ExpID`, `UsedMeasID`, `Value`) "
                                                                    "VALUES (2, 4, 2, 211);"),
("INSERT INTO `ExtendedMeasures` (`MeasID`, `ExpID`, `UsedMeasID`, `Value`) "
                                                                    "VALUES (3, 4, 2, 211);"),
("INSERT INTO `ExtendedMeasures` (`MeasID`, `ExpID`, `UsedMeasID`, `Value`) "
                                                                    "VALUES (4, 4, 2, 211);"),
("INSERT INTO `ExtendedMeasures` (`MeasID`, `ExpID`, `UsedMeasID`, `Value`) "
                                                                    "VALUES (5, 4, 2, 211);"),
("INSERT INTO `ExtendedMeasures` (`MeasID`, `ExpID`, `UsedMeasID`, `Value`) "
                                                                    "VALUES (6, 4, 2, 211);"),
("INSERT INTO `ExtendedMeasures` (`MeasID`, `ExpID`, `UsedMeasID`, `Value`) "
                                                                    "VALUES (7, 4, 2, 211);"),
("INSERT INTO `ExtendedMeasures` (`MeasID`, `ExpID`, `UsedMeasID`, `Value`) "
                                                                    "VALUES (8, 4, 2, 211);"),
("INSERT INTO `ExtendedMeasures` (`MeasID`, `ExpID`, `UsedMeasID`, `Value`) "
                                                                    "VALUES (9, 4, 2, 211);"),
("INSERT INTO `ExtendedMeasures` (`MeasID`, `ExpID`, `UsedMeasID`, `Value`) "
                                                                    "VALUES (10, 4, 2, 211);"),
("INSERT INTO `ExtendedMeasures` (`MeasID`, `ExpID`, `UsedMeasID`, `Value`) "
                                                                    "VALUES (0, 4, 3, -115);"),
("INSERT INTO `ExtendedMeasures` (`MeasID`, `ExpID`, `UsedMeasID`, `Value`) "
                                                                    "VALUES (1, 4, 3, -115);"),
("INSERT INTO `ExtendedMeasures` (`MeasID`, `ExpID`, `UsedMeasID`, `Value`) "
                                                                    "VALUES (2, 4, 3, -115);"),
("INSERT INTO `ExtendedMeasures` (`MeasID`, `ExpID`, `UsedMeasID`, `Value`) "
                                                                    "VALUES (3, 4, 3, -115);"),
("INSERT INTO `ExtendedMeasures` (`MeasID`, `ExpID`, `UsedMeasID`, `Value`) "
                                                                    "VALUES (4, 4, 3, -115);"),
("INSERT INTO `ExtendedMeasures` (`MeasID`, `ExpID`, `UsedMeasID`, `Value`) "
                                                                    "VALUES (5, 4, 3, -115);"),
("INSERT INTO `ExtendedMeasures` (`MeasID`, `ExpID`, `UsedMeasID`, `Value`) "
                                                                    "VALUES (6, 4, 3, -115);"),
("INSERT INTO `ExtendedMeasures` (`MeasID`, `ExpID`, `UsedMeasID`, `Value`) "
                                                                    "VALUES (7, 4, 3, -115);"),
("INSERT INTO `ExtendedMeasures` (`MeasID`, `ExpID`, `UsedMeasID`, `Value`) "
                                                                    "VALUES (8, 4, 3, -115);"),
("INSERT INTO `ExtendedMeasures` (`MeasID`, `ExpID`, `UsedMeasID`, `Value`) "
                                                                    "VALUES (9, 4, 3, -115);"),
("INSERT INTO `ExtendedMeasures` (`MeasID`, `ExpID`, `UsedMeasID`, `Value`) "
                                                                    "VALUES (10, 4, 3, -115);"),
("INSERT INTO `Status` (`StatusID`, `ExpID`, `DevID`, `Timestamp`, `Status`, `ErrorCode`) "
"VALUES (0, 4, 2, '2023-11-17 12:40:03', 'OK', 0);"),
("INSERT INTO `Status` (`StatusID`, `ExpID`, `DevID`, `Timestamp`, `Status`, `ErrorCode`) "
"VALUES (10, 4, 2, '2023-11-17 12:40:08', 'OK', 0)"),
("INSERT INTO `Status` (`StatusID`, `ExpID`, `DevID`, `Timestamp`, `Status`, `ErrorCode`) "
"VALUES (8, 4, 2, '2023-11-17 12:40:07', 'OK', 0);"),
("INSERT INTO `Status` (`StatusID`, `ExpID`, `DevID`, `Timestamp`, `Status`, `ErrorCode`) "
"VALUES (7, 4, 2, '2023-11-17 12:40:06', 'OK', 0);"),
("INSERT INTO `Status` (`StatusID`, `ExpID`, `DevID`, `Timestamp`, `Status`, `ErrorCode`) "
"VALUES (6, 4, 2, '2023-11-17 12:40:06', 'OK', 0);"),
("INSERT INTO `Status` (`StatusID`, `ExpID`, `DevID`, `Timestamp`, `Status`, `ErrorCode`) "
"VALUES (5, 4, 2, '2023-11-17 12:40:05', 'OK', 0);"),
("INSERT INTO `Status` (`StatusID`, `ExpID`, `DevID`, `Timestamp`, `Status`, `ErrorCode`) "
"VALUES (9, 4, 2, '2023-11-17 12:40:07', 'OK', 0);"),
("INSERT INTO `Status` (`StatusID`, `ExpID`, `DevID`, `Timestamp`, `Status`, `ErrorCode`) "
"VALUES (4, 4, 2, '2023-11-17 12:40:05', 'OK', 0);"),
("INSERT INTO `Status` (`StatusID`, `ExpID`, `DevID`, `Timestamp`, `Status`, `ErrorCode`) "
"VALUES (3, 4, 2, '2023-11-17 12:40:04', 'OK', 0);"),
("INSERT INTO `Status` (`StatusID`, `ExpID`, `DevID`, `Timestamp`, `Status`, `ErrorCode`) "
 "VALUES (1, 4, 2, '2023-11-17 12:40:03', 'OK', 0);"),
("INSERT INTO `Status` (`StatusID`, `ExpID`, `DevID`, `Timestamp`, `Status`, `ErrorCode`) "
 "VALUES (2, 4, 2, '2023-11-17 12:40:04', 'OK', 0);")]
master_exp_4_stmt = [
    "DELETE FROM `ExtendedMeasures` WHERE  `ExpID`= 4;",
    "DELETE FROM `Status` WHERE  `ExpID`=4;",
    "DELETE FROM `Alarm` WHERE  `ExpID`=4;",
    "DELETE FROM `GenericMeasures` WHERE  `ExpID`= 4;",
    ("REPLACE INTO `Experiment` (`ExpID`, `Name`, `Description`, `DateCreation`, "
                "`DateBegin`, `DateFinish`, `Status`, `CSID`, `BatID`, `ProfID`) VALUES "
                "(4, 'Prueba Rob Sync', 'Experimento prueba SYNC', '2023-10-18 06:57:00', "
                "NULL, NULL, 'QUEUED', 31, 2, 2);")]
