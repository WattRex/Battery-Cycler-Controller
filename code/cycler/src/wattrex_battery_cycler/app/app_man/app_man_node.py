#!/usr/bin/python3
"""
This modules initialize the cycler platform, check 4 new experiments and execute
them.
"""
#######################        MANDATORY IMPORTS         #######################
from __future__ import annotations

#######################         GENERIC IMPORTS          #######################
from threading import Event, current_thread
from signal import signal, SIGINT
from time import time, sleep
from typing import List, Tuple

#######################       THIRD PARTY IMPORTS        #######################
from system_logger_tool import sys_log_logger_get_module_logger, Logger
log: Logger = sys_log_logger_get_module_logger(__name__)

from system_shared_tool import SysShdChanC, SysShdSharedObjC

#######################          PROJECT IMPORTS         #######################
from wattrex_battery_cycler_datatypes.cycler_data import (CyclerDataAllStatusC, CyclerDataGenMeasC,
                                                        CyclerDataExtMeasC, CyclerDataAlarmC)
from mid.mid_str import MidStrNodeC
from mid.mid_meas import MidMeasNodeC
from .app_man_core import AppManCoreC, AppManCoreStatusE
#######################          MODULE IMPORTS          #######################

#######################              ENUMS               #######################

#######################             CLASSES              #######################
_PERIOD_CYCLE_STR: int = 250 # Period in ms of the storage node
_PERIOD_CYCLE_MEAS: int = 140 # Period in ms of the measurement node
_PERIOD_CYCLE_MAN: int = 1000 # Period in ms of the manager node

class AppManNodeC:
    """Generate a classman node for the application .
    """

    def __init__(self, cs_id: int, cycle_period: int= _PERIOD_CYCLE_MAN ) -> None:

        # Initialize attributes
        self.cs_id: int = cs_id
        self.cycle_period: int = cycle_period

        # Initialize system structure except meas node
        self.init_system()

        signal(SIGINT, self.signal_handler)

        # Config system
        self.config_system()

        log.info(f"{self.th_name} node initiliazed")

    def signal_handler(self, sig, frame):
        """Stop the keyboard .
        """
        log.critical('You pressed Ctrl+C! Stopping all threads...')
        self.stop()
        # TODO: raise alarm if stops node


    def init_system(self) -> None:
        """Initialize the system for this system
        """
        ### 1.0 Threads initialization ###
        self.th_name = current_thread().name
        ### 2.1 Manager thread ###
        log.info(f"Starting {self.th_name} node ...")
        self.working_app = Event()
        self.working_app.set()

        self.working_str = Event()
        self.working_str.set()

        self.working_meas = Event()
        self.working_meas.set()

        __shd_gen_meas = SysShdSharedObjC(CyclerDataGenMeasC())
        __shd_ext_meas = SysShdSharedObjC(CyclerDataExtMeasC())
        __shd_all_status  = SysShdSharedObjC(CyclerDataAllStatusC())
        __chan_alarms = SysShdChanC()
        __chan_str_reqs = SysShdChanC()
        __chan_str_data = SysShdChanC()

        ### 1.1 Store thread ###
        self._th_str = MidStrNodeC(name= 'MID_STR', working_flag= self.working_str,
                shared_gen_meas= __shd_gen_meas, shared_ext_meas= __shd_ext_meas,
                shared_status= __shd_all_status, str_reqs= __chan_str_reqs,
                str_data= __chan_str_data, str_alarms= __chan_alarms,
                cycle_period= _PERIOD_CYCLE_STR, cycler_station= self.cs_id,
                cred_file= 'devops/.cred.yaml')
        self._th_str.start()

        ### 1.2 Manager thread ###
        self.man_core: AppManCoreC= AppManCoreC(shared_gen_meas= __shd_gen_meas,
                    shared_ext_meas= __shd_ext_meas, shared_all_status= __shd_all_status,
                    str_reqs= __chan_str_reqs, str_data= __chan_str_data, str_alarms= __chan_alarms)
        # Get info from the cycler station to know which devices are compatible to
        # launch the meas node if cs is not deprecated
        cs_station_info = self.man_core.get_cs_info()

        if not cs_station_info.deprecated:
            ### 1.3 Meas thread ###
            self._th_meas = MidMeasNodeC(working_flag= self.working_meas,
                    shared_gen_meas= __shd_gen_meas, shared_ext_meas= __shd_ext_meas,
                    shared_status= __shd_all_status, devices= cs_station_info.devices,
                    cycle_period= _PERIOD_CYCLE_MEAS, excl_tags= )
            self._th_meas.start()

    def config_system(self) -> None:
        """Configure the manager
        """
        ### 1.0 Get cycler station info ###
        ### 2.0 Check if CAN sniffer is used and working ###
        ### 3.0 Check if SCPI sniffer is used and working ###
        ### 4.0 Check if all devices has been initialized properly ###


        # TODO: manage errors on system configuration
        pass

    def check_system_health_and_recover(self) -> List[CyclerDataAlarmC]:
        '''
        Checks if the device is running.

        Returns:
            bool: True if all threads works correctly. Otherwise return False
        '''
        log.debug("Checking system health")
        # Check threads status
        alarms = []
        # if not self._th_meas.is_alive():
            # log.critical("Thread MID_DABS has died.")
            # al = APP_DIAG_Alarm_c(code=APP_DIAG_Alarm_Type_e.INTERNAL_PLC_ERR.value, status=0)
            # alarms.append(al)
            # self.__stopDABS_CAN()
            # stop = True


        # if not self._th_str.is_alive():
        #     log.critical("Thread MID_STR has died.")
        #     al = APP_DIAG_Alarm_c(code=APP_DIAG_Alarm_Type_e.INTERNAL_PLC_ERR.value, status=2)
        #     alarms.append(al)
        #     self._th_str.stop()
        #     self._th_str.join()
        #     stop = True

        # if hasattr(self._th_dabs, "can_drv_node"):
        #     if not self._th_dabs.can_drv_node.is_alive():
        #         log.critical("Thread CAN_DRV, used on MID_DABS, has died.")
        #         al = APP_DIAG_Alarm_c(code=APP_DIAG_Alarm_Type_e.INTERNAL_PLC_ERR.value, status=3)
        #         alarms.append(al)
        #         self.__stopDABS_CAN()
        #         stop = True

        # TODO: improve shutdown
        return alarms

        
    def heartbeat(self) -> None:
        """Perform a heartbeat .
        """
        pass

    def stop(self, timeout=1.0):
        """ Stop the thread. """
        log.critical("Stopping BFR application")
        self.working_app.clear()
        self.working_str.clear()
        self.working_meas.clear()
        # TODO: improve stop process
        # self._th_str.join(timeout=timeout)
        # self._th_meas.join(timeout=timeout)


    def run(self) -> None:
        """Run the app .
        """
        log.info(f"Running {self.th_name} thread")
        next_time = time()
        self.iter = -1
        try:
            while self.working_app.is_set():
                log.debug(f"----- {self.th_name} iteration: [{self.iter}] -----")
                raised_alarms = []
                next_time = time() + self.cycle_period/1000.0
                self.iter += 1

                # 1.0 Check system healthy and recover if possible
                raised_alarms = self.check_system_health_and_recover()

                # 2.0 Execute status machine
                self.man_core.execute_machine_status()

                # 3.0 Check if man_core is in error to stop node
                if self.man_core.state == AppManCoreStatusE.ERROR:
                    self.stop()
                # 3.0 Sleep the remaining time
                sleep_time: float = next_time-time()
                if sleep_time < 0.0:
                    log.warning(msg=f"Real time error, cycle time exhausted: {sleep_time}")
                    sleep_time = 0.0
                sleep(sleep_time)

        except Exception as exc:
            log.critical(f"Unexpected error during main execution in APP_SALG_Node thread.\n{exc}")
            log.exception(exc)
            self.stop()
