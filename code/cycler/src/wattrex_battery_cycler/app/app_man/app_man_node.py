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
from time import sleep
from typing import List

#######################       THIRD PARTY IMPORTS        #######################
from system_logger_tool import sys_log_logger_get_module_logger, Logger
log: Logger = sys_log_logger_get_module_logger(__name__)
from system_shared_tool import SysShdChanC, SysShdSharedObjC, SysShdNodeC, SysShdNodeStatusE

#######################          PROJECT IMPORTS         #######################
from wattrex_battery_cycler_datatypes.cycler_data import (CyclerDataAllStatusC, CyclerDataGenMeasC,
                                        CyclerDataExtMeasC, CyclerDataAlarmC, CyclerDataMergeTagsC,
                                        CyclerDataCyclerStationC)
#######################          MODULE IMPORTS          #######################
from .context import *
from mid.mid_str import MidStrNodeC, MidStrReqCmdE, MidStrCmdDataC
from mid.mid_meas import MidMeasNodeC
from .app_man_core import AppManCoreC, AppManCoreStatusE

#######################              ENUMS               #######################

#######################             CLASSES              #######################
_PERIOD_CYCLE_STR: int = 500#250 # Period in ms of the storage node
_PERIOD_CYCLE_MEAS: int = 400#140 # Period in ms of the measurement node
_PERIOD_CYCLE_MAN: int = 1000 # Period in ms of the manager node

class AppManNodeC(SysShdNodeC):
    """Generate a classman node for the application .
    """

    def __init__(self, cs_id: int, working_flag: Event,
                cycle_period: int= _PERIOD_CYCLE_MAN) -> None:
        super().__init__(name= "App_Manager", cycle_period= cycle_period,
                         working_flag=working_flag)
        # Initialize attributes
        self.cs_id: int = cs_id

        # Initialize system structure except meas node
        self.init_system()

        signal(SIGINT, self.signal_handler)

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

        ### Shared objects and channels ###
        self.__shd_gen_meas = SysShdSharedObjC(CyclerDataGenMeasC())
        self.__shd_ext_meas = SysShdSharedObjC(CyclerDataExtMeasC())
        self.__shd_all_status  = SysShdSharedObjC(CyclerDataAllStatusC())
        __chan_alarms = SysShdChanC()
        __chan_str_reqs = SysShdChanC()
        __chan_str_data = SysShdChanC()
        self.__shared_tags: CyclerDataMergeTagsC = CyclerDataMergeTagsC(status_attrs= [],
                                                                 gen_meas_attrs= ['instr_id'],
                                                                 ext_meas_attrs= [])

        ### 1.1 Store thread ###
        self._th_str = MidStrNodeC(name= 'MID_STR', working_flag= self.working_str,
                shared_gen_meas= self.__shd_gen_meas, shared_ext_meas= self.__shd_ext_meas,
                shared_status= self.__shd_all_status, str_reqs= __chan_str_reqs,
                str_data= __chan_str_data, str_alarms= __chan_alarms,
                cycle_period= _PERIOD_CYCLE_STR, cycler_station= self.cs_id,
                cred_file= 'devops/.cred.yaml')
        self._th_str.start()
        # Get info from the cycler station to know which devices are compatible
        cs_info = self.configure_cs(reqs_chan= __chan_str_reqs, data_chan= __chan_str_data)
        for dev in cs_info.devices:
            log.info(f"Device {dev.device_type.name} with iface {dev.iface_name}")
        ### 1.2 Manager thread ###
        self.man_core: AppManCoreC= AppManCoreC(devices=cs_info.devices, str_reqs= __chan_str_reqs,
                                str_data= __chan_str_data, str_alarms= __chan_alarms)
        # launch the meas node if cs is not deprecated
        if not cs_info.deprecated:
            ### 1.3 Meas thread ###
            self._th_meas = MidMeasNodeC(working_flag= self.working_meas,
                    shared_gen_meas= self.__shd_gen_meas, shared_ext_meas= self.__shd_ext_meas,
                    shared_status= self.__shd_all_status, devices= cs_info.devices,
                    cycle_period= _PERIOD_CYCLE_MEAS, excl_tags= self.__shared_tags)
            self._th_meas.start()
        else:
            log.critical(("Cycler station is deprecated. Meas node will not be launched, "
                        "cycler station will be stop"))
            self.stop()
        sleep(2)
        self.__prepare_node()

    def configure_cs(self, reqs_chan: SysShdChanC,
                     data_chan: SysShdChanC) -> CyclerDataCyclerStationC:
        """Get the cycler station info from the database

        Returns:
            CyclerDataCyclerStationC: Cycler station info
        """
        request: MidStrCmdDataC = MidStrCmdDataC(cmd_type= MidStrReqCmdE.GET_CS)
        reqs_chan.send_data(request)
        response: MidStrCmdDataC = data_chan.receive_data()
        if response.error_flag:
            raise ValueError(("Error in response from MID STR"))
        return response.station

    def __prepare_node(self):
        log.info(f"Running {self.th_name} thread")
        self.iter = -1
        self.sync_shd_data()
        while self.man_core.local_gen_meas.voltage is None:
            sleep(1)
        self.status = SysShdNodeStatusE.OK


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
        self.status = SysShdNodeStatusE.STOP
        log.critical("Stopping Cycler manager node")
        self.working_app.clear()
        self.working_meas.clear()
        ## If the manager is stoping, first turn all experiments queued or running to error
        self.man_core.deprecated_cs()
        sleep(2)
        self.working_str.clear()
        # TODO: improve stop process
        # self._th_str.join(timeout=timeout)
        # self._th_meas.join(timeout=timeout)

    def sync_shd_data(self) -> None:
        self.man_core.local_gen_meas : CyclerDataGenMeasC = self.__shd_gen_meas.\
            update_including_tags(self.man_core.local_gen_meas, self.__shared_tags.gen_meas_attrs)
        self.man_core.local_ext_meas : CyclerDataExtMeasC = self.__shd_ext_meas.\
            update_including_tags(self.man_core.local_ext_meas, self.__shared_tags.ext_meas_attrs)
        self.man_core.local_all_status : CyclerDataAllStatusC = self.__shd_all_status.\
            update_including_tags(self.man_core.local_all_status, self.__shared_tags.status_attrs)

    def process_iteration(self) -> None:
        """Run the app .
        """
        try:
            self.iter += 1
            log.debug(f"----- {self.th_name} start iteration: [{self.iter}] -----")
            log.debug(f"----- start iteration: {self.iter} mode: {self.man_core.state} -----")
            raised_alarms = []
            # 1.0 Check system healthy and recover if possible
            raised_alarms = self.check_system_health_and_recover()
            # 2.0 HeartBeat
            self.heartbeat()
            # 3.0 Sync shared data
            self.sync_shd_data()
            # 4.0 Process reqs to str node
            self.man_core.process_request()

            # 5.0 Execute status machine
            self.man_core.execute_machine_status()

            # 6.0 Check if man_core is in error to stop node
            if self.man_core.state == AppManCoreStatusE.ERROR:
                self.stop()
            log.debug(f"----- {self.th_name} end iteration: [{self.iter}] -----")
            log.debug(f"----- end iteration: {self.iter} mode: {self.man_core.state} -----")
        except Exception as exc:
            log.critical(f"Unexpected error during main execution in APP_SALG_Node thread.\n{exc}")
            log.exception(exc)
            self.stop()
