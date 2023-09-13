#!/usr/bin/python3
'''
Definition of MID STR Node.
'''
#######################        MANDATORY IMPORTS         #######################
from __future__ import annotations

#######################         GENERIC IMPORTS          #######################
from threading import Event, current_thread
from typing import List

#######################       THIRD PARTY IMPORTS        #######################
from func_timeout import func_timeout, FunctionTimedOut

#######################      SYSTEM ABSTRACTION IMPORTS  #######################
from system_logger_tool import sys_log_logger_get_module_logger
log = sys_log_logger_get_module_logger(__name__)

#######################          PROJECT IMPORTS         #######################
from system_config_tool import sys_conf_read_config_params
from system_shared_tool import SysShdSharedObjC, SysShdNodeC, SysShdNodeParamsC, SysShdChanC
#######################          MODULE IMPORTS          #######################
from .mid_str_facade import MidStrFacadeC
from .mid_str_cmd import MidStrCmdDataC, MidStrDataCmdE, MidStrReqCmdE
from ..mid_data import MidDataAlarmC, MidDataGenMeasC, MidDataExtMeasC, MidDataAllStatusC #pylint: disable= relative-beyond-top-level

#######################              ENUMS               #######################
# getExpStatus
# getExpProfileData
# getExpBatteryData
# modifyCurrentExp
# writeNewAlarms
# writeGenericMeasures
# writeExtendedMeasures

#######################             CLASSES              #######################
TIMEOUT_CONNECTION = 10
### THREAD ###
class MidStrNodeC(SysShdNodeC): #pylint: disable= too-many-instance-attributes
    """This class will create a node that communicates with the databases reading and writing data.
    """
    def __init__(self, name: str, working_flag : Event, shared_gen_meas: SysShdSharedObjC, #pylint: disable= too-many-arguments
                 shared_ext_meas: SysShdSharedObjC, shared_status: SysShdSharedObjC,
                 str_reqs: SysShdChanC, str_data: SysShdChanC, str_alarms: SysShdChanC,
                 cycle_period: int, cycler_station: int,
                 str_params: SysShdNodeParamsC= SysShdNodeParamsC()) -> None:
        '''
        Initialize the MID_STR thread used as database proxy.

        Args:
            cycle_period (int): Period of the thread cycle in seconds.
            working_flag (threading.Event): Flag used to stop the thread.
            name (str, optional): Name of the thread. Defaults to 'MID_STR'.
        '''
        super().__init__(name, cycle_period, working_flag, str_params)
        log.info(f"Initializing {name} node...")
        self.cycle_period = cycle_period
        self.working_flag = working_flag
        self.cycler_station = cycler_station
        self.db_iface = MidStrFacadeC(master_file= './config.yaml', cache_file= './cache.yaml')
        self.str_reqs: SysShdChanC = str_reqs
        self.str_data: SysShdChanC = str_data
        self.str_alarms: SysShdChanC = str_alarms
        self.globlal_gen_meas: SysShdSharedObjC = shared_gen_meas
        self.globlal_ext_meas: SysShdSharedObjC = shared_ext_meas
        self.globlal_all_status: SysShdSharedObjC = shared_status
        self.__all_status: MidDataAllStatusC = MidDataAllStatusC()
        self.__gen_meas: MidDataGenMeasC = MidDataGenMeasC(0,0,0,0)
        self.__ext_meas: MidDataExtMeasC = MidDataExtMeasC()
        self.__actual_exp_id: int = -1

        ## Once it has been initilizated all atributes ask for the cycler station info
        cycler_info = self.db_iface.get_cycler_station_info(self.cycler_station)
        self.str_data.send_data(MidStrCmdDataC(cmd_type= MidStrDataCmdE.CS_DATA,
                                               station= cycler_info))


###################################### REMOVE FOLLOWING LINES ######################################
        # self.is_recording_meas = False
        # self.shared_meas = shared_measures
        # self.shared_status = shared_status
        # self.chan_APP_STR = chan_APP_STR

        # # Create the conector used for database comunication
        # local_status : MID_DABS_Status_c = self.shared_status.read()
        # local_meas : MID_DABS_Measures_c = self.shared_meas.read()
        # local_meas.elect.OperatingHours = self.db_iface.getOperatingHours(local_meas.bat_id)
        # local_meas : MID_DABS_Measures_c = self.shared_meas.mergeIncludedTags(local_meas,
        #                                       ['elect.OperatingHours'])

    def __receive_alarms(self) -> List[MidDataAlarmC]:
        alarms = []
        alarm = self.str_alarms.receive_data_unblocking()
        while alarm is not None:
            alarms.append(alarm)
            alarm = self.str_alarms.receive_data_unblocking()
        return alarms

    def __apply_command(self, command : MidStrCmdDataC) -> None:
        '''Apply a command to the Storage node.

        Args:
            command (DrvCanCmdDataC): Data to process, does not know if its for the channel or
            a message to a device

        Raises:
            err (CanOperationError): Raised when error with CAN connection occurred
        '''
        #Check which type of command has been received and matchs the payload type
        if command.cmd_type == MidStrReqCmdE.GET_NEW_EXP:
            log.info('Getting new experiment info from database')
            exp_info, battery_info, profile_info = self.db_iface.get_start_queued_exp(
                                                                self.cycler_station)
            self.__actual_exp_id = exp_info.exp_id
            log.debug("Sending new experiment to APP_MANAGER")
            self.str_data.send_data(MidStrCmdDataC(cmd_type= MidStrDataCmdE.EXP_DATA, exp= exp_info,
                                battery= battery_info, profile= profile_info))
        elif command.cmd_type == MidStrReqCmdE.GET_EXP_STATUS:
            exp_status = self.db_iface.get_exp_status(self.__actual_exp_id)
            self.str_data.send_data(MidStrCmdDataC(cmd_type= MidStrDataCmdE.EXP_STATUS,
                                                   exp_status= exp_status))
        elif command.cmd_type == MidStrReqCmdE.GET_CS:
            cycler_info = self.db_iface.get_cycler_station_info(self.cycler_station)
            self.str_data.send_data(MidStrCmdDataC(cmd_type= MidStrDataCmdE.CS_DATA,
                                                   station= cycler_info))
        elif command.cmd_type == MidStrReqCmdE.SET_EXP_STATUS and command.exp_status is not None:
            self.db_iface.modify_current_exp(command.exp_status)
        else:
            log.error(("Can`t apply command. Error in command format, "
                       "check command type and payload type"))

    def sync_shd_data(self) -> None:
        '''Update local data
        '''
        self.__all_status: MidDataAllStatusC = self.globlal_all_status.read()
        self.__gen_meas: MidDataGenMeasC     = self.globlal_gen_meas.read()
        self.__ext_meas: MidDataExtMeasC     = self.globlal_ext_meas.read()

    def stop(self) -> None:
        """Stop the node if it is not already closed .
        """
        self.db_iface.close_db_connection()
        log.critical(f"Stopping {current_thread().getName()} node")

    def process_iteration(self) -> None:
        """AI is creating summary for process_iteration
        """
        try:
            # Syncronising shared data
            self.sync_shd_data()
            # Receive and write alarms
            alarms = self.__receive_alarms()
            self.db_iface.write_new_alarm(alarms)
            log.debug("+++++ After write alarams in db_iface object +++++")
            ### Write measures and status changes
            self.db_iface.write_generic_measures(self.__gen_meas)
            self.db_iface.write_extended_measures(self.__ext_meas)
            self.db_iface.write_status_changes(self.__all_status)
            if not self.str_reqs.is_empty():
                # Ignore warning as receive_data return an object,
                # which in this case must be of type DrvCanCmdDataC
                command : MidStrCmdDataC = self.str_reqs.receive_data() # type: ignore
                log.debug(f"Command to apply: {command.cmd_type.name}")
                self.__apply_command(command)
            log.debug("+++++ Before commit changes in db_iface +++++")
            # TIMEOUT added to detect if database connection was ended
            func_timeout(TIMEOUT_CONNECTION, self.db_iface.commit_changes())
            log.debug("+++++ After commit changes in db_iface +++++")
        except FunctionTimedOut as exc:
            log.warning(("Timeout during commit changes to local database."
                         f"Database connection will be restarted. {exc}"))
            self.db_iface.reset_db_connection()
        except ConnectionError as exc:
            log.critical(exc)
        except Exception as exc:
            log.critical(f"Unexpected error in MID_STR_Node_c thread.\n{exc}")
            self.stop()

#######################            FUNCTIONS             #######################
