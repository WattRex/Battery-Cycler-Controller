#!/usr/bin/python3
'''
Definition of MID STR Node.
'''
#######################        MANDATORY IMPORTS         #######################
from __future__ import annotations

#######################         GENERIC IMPORTS          #######################
import threading
import time
from typing import Callable, Iterable, Mapping, Any, List

#######################       THIRD PARTY IMPORTS        #######################
from func_timeout import func_timeout, FunctionTimedOut

#######################      SYSTEM ABSTRACTION IMPORTS  #######################
from system_logger_tool import sys_log_logger_get_module_logger
log = sys_log_logger_get_module_logger(__name__)

#######################          PROJECT IMPORTS         #######################
from system_config_tool import sys_conf_read_config_params

#######################          MODULE IMPORTS          #######################
from .mid_str_facade import MidStrFacadeC


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

### THREAD ###
class MidStrNodeC(threading.Thread):

    def __init__(self, cycle_period : int, working_flag : threading.Event, name : str = 'MID_STR', \
        target: Callable[..., object] | None = ..., args: Iterable[Any] = ..., \
        kwargs: Mapping[str, Any] | None = ..., *, daemon: bool | None = ...) -> None:
        '''
        Initialize the MID_STR thread used as database proxy.

        Args:
            cycle_period (int): Period of the thread cycle in seconds.
            working_flag (threading.Event): Flag used to stop the thread.
            name (str, optional): Name of the thread. Defaults to 'MID_STR'.
        '''        
        super().__init__(None, target, name, args, kwargs, daemon=daemon)
        log.info(f"Initializing {name} node...")
        self.cycle_period = cycle_period
        self.working_flag = working_flag
        self.cycler_station = sys_conf_read_config_params('./config.yaml', 'cycler_station')
        self.db = MidStrFacadeC(self.cycler_station['id'])


###################################### REMOVE FOLLOWING LINES ######################################
        self.is_recording_meas = False
        self.shared_meas = shared_measures
        self.shared_status = shared_status
        self.chan_APP_STR = chan_APP_STR

        # Create the conector used for database comunication
        local_status : MID_DABS_Status_c = self.shared_status.read()
        local_meas : MID_DABS_Measures_c = self.shared_meas.read()
        local_meas.elect.OperatingHours = self.db.getOperatingHours(local_meas.bat_id)
        local_meas : MID_DABS_Measures_c = self.shared_meas.mergeIncludedTags(local_meas, ['elect.OperatingHours'])

    def __receiveAlarms(self) -> List[MID_DABS_Alarm_c]:
        alarms = []
        # log.warning(f"chan_APP_STR queue size BEFORE receive: {self.chan_APP_STR.qsize()}")
        al = self.chan_APP_STR.receiveDataUnblocking()
        while al is not None:
            alarms.append(al)
            # log.info(f"Alarm received in MID_STR node: {al.__repr__()}")
            al = self.chan_APP_STR.receiveDataUnblocking()
        # log.warning(f"chan_APP_STR queue size AFTER receive: {self.chan_APP_STR.qsize()}")
        return alarms

    def stop(self) -> None:
        self.db.closeConnection()
        log.critical(f"Stopping {threading.currentThread().getName()} node")

    def run(self) -> None:
        log.info(f"Running {threading.currentThread().getName()} thread")
        fstInsert = True
        try:
            # timeout = gevent.Timeout(TIMEOUT_CONNECTION)
            while self.working_flag.isSet():
                try:
                    # timeout.start()
                    # log.critical(f"Is database connection closed? - {self.db.session.connection().closed}")
                    log.info(f"----- {threading.currentThread().getName()} new iteration -----")
                    nextTime = time.time() + 1

                    # Receive and write alarms
                    alarms = self.__receiveAlarms()
                    self.db.writeAlarms(alarms)
                    log.info(f"+++++ After write alarams in db object +++++")
                    local_meas : MID_DABS_Measures_c = self.shared_meas.read()
                    local_status : MID_DABS_Status_c = self.shared_status.read()

                    if local_meas.is_recording_meas:
                        if fstInsert:
                            fstInsert = False
                        ### Write measures and status changes
                        self.db.incMeasID()
                        self.db.writeMeasures(local_meas)
                        self.db.writeStatusChanges(local_status, fstInsert)
                    
                    log.info(f"+++++ Before commit changes in db +++++")
                    func_timeout(TIMEOUT_CONNECTION, self.db.commitChanges) # TIMEOUT added to detect if database connection was ended.
                    
                    sleep_time = nextTime-time.time()
                    if sleep_time < 0.1:
                        log.critical(f"Real time error, cycle time exhausted: {sleep_time}")
                    else:
                        time.sleep(sleep_time)
                except FunctionTimedOut as exc:
                    log.warning("Timeout during commit changes to local database. Database connection will be restarted.")
                    self.db.reset()
            func_timeout(TIMEOUT_CONNECTION, self.stop) # TIMEOUT added to detect if database connection was ended.
        except ConnectionError as exc:
            log.critical(exc)
        except Exception as exc:
            log.critical(f"Unexpected error in MID_STR_Node_c thread.\n{exc}")
            self.stop()

#######################            FUNCTIONS             #######################
