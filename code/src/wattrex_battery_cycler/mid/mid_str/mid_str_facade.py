#!/usr/bin/python3
'''
Definition of MID STR Facade where database connection methods are defined.
'''
#######################        MANDATORY IMPORTS         #######################
from __future__ import annotations

#######################         GENERIC IMPORTS          #######################
from datetime import datetime
from typing import List

#######################       THIRD PARTY IMPORTS        #######################
from sqlalchemy import select, update, insert

#######################      SYSTEM ABSTRACTION IMPORTS  #######################
from system_logger_tool import sys_log_logger_get_module_logger
log = sys_log_logger_get_module_logger(__name__)

#######################          PROJECT IMPORTS         #######################
from wattrex_driver_db import DrvDbSqlEngineC, DrvDbExperimentC, DrvDbBatteryC, DrvDbProfileC, \
                        DrvDbCycleStationC, DrvDbInstructionC, DrvDbExpStatusE, DrvDbAlarmC, \
                        DrvDbExtendedMeasureC, DrvDbGenericMeasureC, DrvDbStatusC

#######################          MODULE IMPORTS          #######################
from ..mid_data import MidDataAlarmC, MidDataGenMeasC, MidDataExtMeasC, MidDataAllStatusC,\
                MidDataExpStatusE, MidDataProfileC, MidDataBatteryC,\
                MidDataExperimentC, MidDataCyclerStationC\

#######################              ENUMS               #######################
#
#
# getExpStatus
# getExpProfileData
# getExpBatteryData
# modifyCurrentExp
# writeNewAlarms
# writeGenericMeasures
# writeExtendedMeasures

#######################             CLASSES              #######################

class MidStrDbElementNotFoundErrorC(Exception):
    """Exception raised for errors when an input not found in the database.

    Attributes:
        message -- explanation of the error
    """
    def __init__(self, message):
        super().__init__(message)

class MidStrFacadeC:
    '''
    This class is used to interface with the database.
    '''
    def __init__(self, master_file : str = ".cred.yaml", cache_file : str = ".cred.yaml") -> None:
        log.info("Initializing DB Connection...")
        self.__master_db: DrvDbSqlEngineC = DrvDbSqlEngineC(master_file)
        self.__cache_db: DrvDbSqlEngineC = DrvDbSqlEngineC(cache_file)
        self.meas_id: int = 0

    def get_start_queued_exp(self, cycler_station_id) -> MidDataExperimentC:
        '''
        Get the oldest queued experiment, assigned to the cycler station where this 
        cycler would be running, and change its status to RUNNING in database.
        '''
        self.meas_id = 0
        exp = {}
        battery = {}
        profile = {}
        try:
            stmt =  select(DrvDbExperimentC)\
                        .where(DrvDbExperimentC.Status == DrvDbExpStatusE.QUEUED)\
                        .where(DrvDbExperimentC.CSID == cycler_station_id)\
                        .order_by(DrvDbExperimentC.DateCreation.asc())
            result = self.__master_db.execute(stmt).first()
            if result is None:
                raise MidStrDbElementNotFoundErrorC(("No experiment found for cycler station "
                                                    f"with ID: {cycler_station_id}"))
            exp : DrvDbExperimentC = result[0]
            # Get battery info
            stmt =  select(DrvDbBatteryC)\
                        .where(DrvDbBatteryC.BatID == exp.BatID)
            result = self.__master_db.execute(stmt).first()
            if result is None:
                raise MidStrDbElementNotFoundErrorC(("No battery found with ID: {exp.BatID}"))
            battery = result[0]
            # Get profile info
            stmt =  select(DrvDbProfileC)\
                        .where(DrvDbProfileC.ProfID == exp.ProfID)
            result = self.__master_db.execute(stmt).first()
            if result is None:
                raise MidStrDbElementNotFoundErrorC(("No profile found with ID: {exp.ProfID}"))
            profile = result[0]

            # Change experiment status to running and update begin datetime
            stmt = update(DrvDbExperimentC).where(DrvDbExperimentC.ExpID == exp.ExpID)\
                        .values(Status=DrvDbExpStatusE.RUNNING, DateBegin=datetime.utcnow())
            self.__cache_db.execute(stmt)
        except Exception as err: #pylint: disable=broad-except
            # TODO: not catch own raised exceptions
            # print(err)
            # print("Error on GetQueuedExperimentById. Performing rollback...")
            # self.session.rollback()
            pass
        finally:
            return MidDataExperimentC(**exp.__dict__), MidDataBatteryC(**battery.__dict__),\
                        MidDataProfileC(**profile.__dict__)

    ## All methods that get information will gather the info from the master db
    def get_exp_status(self, exp_id: int) -> MidDataExpStatusE:
        """Returns the experiment status .
        Args:
            exp_id (int): [description]
        Returns:
            MidDataExpStatusE: [description]
        """
        stmt = select(DrvDbExperimentC).where(DrvDbExperimentC.ExpID == exp_id)
        result = self.__master_db.execute(stmt).fetchone()
        if result is None:
            raise MidStrDbElementNotFoundErrorC(f'Experiment with id {exp_id} not found')
        return MidDataExpStatusE(result.get("Status"))

    def get_exp_profile_data(self,exp_id: int) -> MidDataProfileC:
        """AI is creating summary for get_exp_profile_data
        Args:
            exp_id (int): [description]
        Returns:
            MidDataProfileC: [description]
        """
        stmt = select(DrvDbExperimentC).where(DrvDbExperimentC.ExpID == exp_id)
        result = self.__master_db.execute(stmt).fetchone()
        if result is None:
            raise MidStrDbElementNotFoundErrorC(f'Experiment with id {exp_id} not found')
        return MidDataProfileC(**result.get("Profile"))

    def get_exp_battery_data(self, exp_id: int) -> MidDataBatteryC:
        """Get the mid - data of an experiment .
        Args:
            exp_id (int): [description]
        Returns:
            MidDataBatteryC: [description]
        """
        stmt = select(DrvDbExperimentC).where(DrvDbExperimentC.ExpID == exp_id)
        result = self.__master_db.execute(stmt).fetchone()
        if result is None:
            raise MidStrDbElementNotFoundErrorC(f'Experiment with id {exp_id} not found')
        return MidDataBatteryC(**result.get("Battery"))

    def get_cycler_station_info(self, exp_id: int) -> MidDataCyclerStationC:
        """Returns the name and name of the cycle station for the experiment .
        Returns:
            [type]: [description]
        """
        stmt = select(DrvDbExperimentC).where(DrvDbExperimentC.ExpID == exp_id)
        result = self.__master_db.execute(stmt).fetchone()
        if result is None:
            raise MidStrDbElementNotFoundErrorC(f'Experiment with id {exp_id} not found')
        result = result.get("CyclerStation")
        ## TODO: Check what is going to return exactly this function (ask Marius and Javi)
        return MidDataCyclerStationC(**result.__dict__)

    ## All methods that write information will write the info into the cache db
    def modify_current_exp(self, exp_status: MidDataExperimentC) -> None:
        """Modify the current experiment status .
        Args:
            exp_status (MidDataExpStatusE): [description]
        """
        stmt = update(DrvDbExperimentC).where(DrvDbExperimentC.ExpID == exp_status.exp_id).\
            values(Timestamp= datetime.now(), Status = exp_status.status)
        self.__cache_db.execute(stmt)

    def write_status_changes(self, all_status: MidDataAllStatusC) -> None:
        """Write the status changes into the cache db .
        Args:
            new_status (MidDataAllStatusC): [description]
        """
        stmt = update(DrvDbStatusC).where(DrvDbStatusC.ExpID == all_status.exp_id).\
            values(Timestamp= datetime.now(), **all_status.__dict__)
        self.__cache_db.execute(stmt)

    def write_new_alarm(self, alarms: List[MidDataAlarmC]) -> None:
        """Write an alarm into the cache db .
        Args:
            alarm (List[MidDataAlarmC]): [description]
        """
        for alarm in alarms:
            stmt = insert(DrvDbAlarmC).values(Timestamp= datetime.now(), **alarm.__dict__)
            self.__cache_db.execute(stmt)

    def write_generic_measures(self, gen_meas: MidDataGenMeasC) -> None:
        """Write the generic measures into the cache db .
        Args:
            gen_meas (MidDataGenMeasC): [description]
        """
        stmt = insert(DrvDbGenericMeasureC).values(Timestamp= datetime.now(), MeasID= self.meas_id,
                                                   **gen_meas.__dict__)
        self.__cache_db.execute(stmt)
        self.meas_id += 1

    def write_extended_measures(self, ext_meas: MidDataExtMeasC) -> None:
        """Write the extended measures into the cache db .
        Args:
            ext_meas (MidDataExtMeasC): [description]
        """
        stmt = insert(DrvDbExtendedMeasureC).values(Timestamp= datetime.now(), MeasID= self.meas_id,
                                                     **ext_meas.__dict__)
        self.__cache_db.execute(stmt)

    def commit_changes(self):
        """Commit changes made to the cache database.
        """
        self.__cache_db.commit_changes()

    def reset_db_connection(self):
        """Reset the connection to the both database.
        """
        # Closing connection to databases
        self.__cache_db.reset()
        self.__master_db.reset()

    def close_db_connection(self):
        """Close the connection to the both databases.
        """
        # Closing connection to databases
        self.__cache_db.closeConnection()
        self.__master_db.closeConnection()
