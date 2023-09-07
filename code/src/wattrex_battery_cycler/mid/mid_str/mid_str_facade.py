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
from sqlalchemy import BigInteger, false, null, select, update, insert

#######################      SYSTEM ABSTRACTION IMPORTS  #######################
from system_logger_tool import sys_log_logger_get_module_logger
log = sys_log_logger_get_module_logger(__name__)

#######################          PROJECT IMPORTS         #######################
from wattrex_driver_db.drv_db_engine import DrvDbSqlEngineC
from wattrex_driver_db.drv_db_dao import DrvDbExperimentC, DrvDbBatteryC, DrvDbProfileC, \
                                        DrvDbCycleStationC, DrvDbInstructionC
from wattrex_driver_db.drv_db_types import DrvDbExpStatusE

#######################          MODULE IMPORTS          #######################



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

class MidStrExperimentC(DrvDbExperimentC):
    
    def __init__(self, exp : DrvDbExperimentC, filePath: str, cs : DrvDbCycleStationC = None, \
                    bat : DrvDbBatteryC = None, prof : DrvDbProfileC = None, \
                    instr : List[DrvDbInstructionC] = None):
        for key, value in exp.__dict__.items():
            setattr(self, key, value)
        if cs is not None:
            self.CS = cs
        else:
            self.CS = select(DrvDbCycleStationC)\
                            .where(DrvDbCycleStationC.CSID == exp.CSID).first()[0]
        if bat is not None:
            self.Bat = bat
        else:
            self.Bat = select(DrvDbBatteryC)\
                            .where(DrvDbBatteryC.BatID == exp.BatID).first()[0]
        if prof is not None:
            self.Prof = prof
        else:
            self.Prof = select(DrvDbProfileC)\
                            .where(DrvDbProfileC.ProfID == exp.ProfID).first()[0]
        if instr is not None:
            self.Instr = instr
        else:
            self.Instr = select(DrvDbInstructionC)\
                            .where(DrvDbInstructionC.ExpID == exp.ExpID)\
                            .order_by(DrvDbExperimentC.DateCreation.asc()).all()
        
        print(self.__dict__.items())
    



class MidStrFacadeC(DrvDbSqlEngineC):
    '''
    This class is used to interface with the database.
    '''
    def __init__(self, cycler_station_id : int, config_file : str = ".cred.yaml"):
        log.info("Initializing DB Connection...")
        super().__init__(config_file = config_file)
        self.cycler_station_id = cycler_station_id

    def getAndStartQueuedExp(self) -> MidStrExperimentC:
        '''
        Get the oldest queued experiment, assigned to the cycler station where this 
        cycler would be running, and change its status to RUNNING in database.
        '''
        try:
            stmt =  select(DrvDbExperimentC)\
                        .where(DrvDbExperimentC.Status == DrvDbExpStatusE.QUEUED)\
                        .where(DrvDbExperimentC.CSID == self.cycler_station_id)\
                        .order_by(DrvDbExperimentC.DateCreation.asc())
            result = self.session.execute(stmt).first()
            if result is None:
                raise MidStrDbElementNotFoundErrorC(f"No experiment \
                    found for cycler station with ID: {self.cycler_station_id}")
            exp : DrvDbExperimentC = result[0]

            # Change experiment status to running and update begin datetime
            stmt = update(DrvDbExperimentC)\
                        .where(DrvDbExperimentC.ExpID == exp.ExpID)\
                        .values(Status=DrvDbExpStatusE.RUNNING, DateBegin=datetime.utcnow())
            self.session.execute(stmt)

            
            # # Get File Path
            # stmt = select(DRV_DB_Profile_c).where(DRV_DB_Profile_c.ProfID == exp.Profile)
            # result = self.session.execute(stmt).first()
            # if result is None:
            #     raise MID_COMM_DB_Element_Not_Found_Error_c(f"Any profile found for that experiment. Profile ID: {exp.Profile}")
            # prof = result[0] 
            # MID_exp = MID_COMM_Experiment_c(exp, prof.CMDFilePath)
            # #print(expVO.ExpID)
            
            # # Get Battery info
            # stmt = select(DRV_DB_Battery_c).where(DRV_DB_Battery_c.BatID == exp.Battery)
            # result = self.session.execute(stmt).first()
            # if result is None:
            #     raise MID_COMM_DB_Element_Not_Found_Error_c(f"Any battery found for that experiment. Battery ID: {exp.Battery}")
            # MID_bat = MID_COMM_Battery_c(result[0])
            self.session.commit()
                
        except Exception as err:
            # TODO: not catch own raised exceptions 
            # print(err)
            # print("Error on GetQueuedExperimentById. Performing rollback...")
            self.session.rollback()
        finally:
            return MidStrExperimentC(exp)





#######################            FUNCTIONS             #######################
if __name__ == '__main__':
    MidStrFacadeC()