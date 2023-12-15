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
from system_shared_tool import (SysShdSharedObjC, SysShdNodeC, SysShdNodeParamsC, SysShdChanC,
                        SysShdNodeStatusE)
from wattrex_battery_cycler_datatypes.cycler_data import (CyclerDataAlarmC, CyclerDataGenMeasC,
                                              CyclerDataExtMeasC, CyclerDataAllStatusC,
                                              CyclerDataCyclerStationC, CyclerDataExpStatusE)

######################             CONSTANTS              ######################
from .context import (DEFAULT_TIMEOUT_CONNECTION, DEFAULT_NODE_NAME, DEFAULT_NODE_PERIOD,
                      DEFAULT_CRED_FILEPATH)
#######################          MODULE IMPORTS          #######################
from .mid_str_facade import MidStrFacadeC
from .mid_str_cmd import MidStrCmdDataC, MidStrDataCmdE, MidStrReqCmdE

#######################              ENUMS               #######################

#######################             CLASSES              #######################
### THREAD ###
class MidStrNodeC(SysShdNodeC): #pylint: disable= too-many-instance-attributes
    """This class will create a node that communicates with the databases reading and writing data.
    """
    def __init__(self, working_flag : Event, shared_gen_meas: SysShdSharedObjC, #pylint: disable= too-many-arguments
                 shared_ext_meas: SysShdSharedObjC, shared_status: SysShdSharedObjC,
                 str_reqs: SysShdChanC, str_data: SysShdChanC, str_alarms: SysShdChanC,
                 cycler_station: int, str_params: SysShdNodeParamsC= SysShdNodeParamsC()) -> None:
        '''
        Initialize the MID_STR thread used as database proxy.

        Args:
            cycle_period (int): Period of the thread cycle in seconds.
            working_flag (threading.Event): Flag used to stop the thread.
            name (str, optional): Name of the thread. Defaults to 'MID_STR'.
        '''
        super().__init__(DEFAULT_NODE_NAME, DEFAULT_NODE_PERIOD, working_flag, str_params)
        log.info(f"Initializing {DEFAULT_NODE_NAME} node...")
        self.db_iface = MidStrFacadeC(cred_file= DEFAULT_CRED_FILEPATH,
                                      cycler_station_id= cycler_station)
        self.str_reqs: SysShdChanC = str_reqs
        self.str_data: SysShdChanC = str_data
        self.str_alarms: SysShdChanC = str_alarms
        self.globlal_gen_meas: SysShdSharedObjC = shared_gen_meas
        self.globlal_ext_meas: SysShdSharedObjC = shared_ext_meas
        self.globlal_all_status: SysShdSharedObjC = shared_status
        self.__actual_exp_id: int = -1
        self.__new_raised_alarms: List[CyclerDataAlarmC] = []
        ## Once it has been initilizated all atributes ask for the cycler station info
        cycler_info: CyclerDataCyclerStationC = self.db_iface.get_cycler_station_info()
        self.str_data.send_data(MidStrCmdDataC(cmd_type= MidStrDataCmdE.CS_DATA,
                                               station= cycler_info))

    def __receive_alarms(self) -> None:
        alarm = self.str_alarms.receive_data_unblocking()
        while alarm is not None:
            self.__new_raised_alarms.append(alarm)
            alarm = self.str_alarms.receive_data_unblocking()

    def __apply_command(self, command : MidStrCmdDataC) -> None: #pylint: disable= too-many-branches
        '''
        Apply a command to the Storage node.

        Args:
            command (DrvCanCmdDataC): Data to process, does not know if its for the channel or
            a message to a device

        Raises:
            err (CanOperationError): Raised when error with CAN connection occurred
        '''
        #Check which type of command has been received and matchs the payload type
        if command.cmd_type == MidStrReqCmdE.GET_NEW_EXP:
            log.info('Getting new experiment info from database')
            exp_info, battery_info, profile_info = self.db_iface.get_start_queued_exp()
            if exp_info is not None:
                self.__actual_exp_id = exp_info.exp_id
            ## If there is an error gathering experiment info, manager will manage it
            log.debug("Sending new experiment to APP_MANAGER")
            self.str_data.send_data(MidStrCmdDataC(cmd_type= MidStrDataCmdE.EXP_DATA,
                    experiment= exp_info, battery= battery_info, profile= profile_info))
        elif command.cmd_type == MidStrReqCmdE.GET_EXP_STATUS:
            if self.__actual_exp_id == -1:
                log.warning("No experiment is running")
                exp_status = None
            else:
                exp_status = self.db_iface.get_exp_status(exp_id= self.__actual_exp_id)
            self.str_data.send_data(MidStrCmdDataC(cmd_type= MidStrDataCmdE.EXP_STATUS,
                                                   exp_status= exp_status))
        elif command.cmd_type == MidStrReqCmdE.GET_CS:
            cycler_info = self.db_iface.get_cycler_station_info()
            self.str_data.send_data(MidStrCmdDataC(cmd_type= MidStrDataCmdE.CS_DATA,
                                                   station= cycler_info))
        elif command.cmd_type == MidStrReqCmdE.GET_CS_STATUS:
            cycler_status = self.db_iface.get_cycler_station_status()
            self.str_data.send_data(data= MidStrCmdDataC(cmd_type= MidStrDataCmdE.CS_STATUS,
                                                station_status = cycler_status))
        elif command.cmd_type == MidStrReqCmdE.SET_EXP_STATUS and command.exp_status is not None:
            if self.__actual_exp_id == -1:
                log.warning("No experiment is running")
            else:
                self.db_iface.modify_current_exp(exp_status= command.exp_status,
                                             exp_id= self.__actual_exp_id)
                if command.exp_status in (CyclerDataExpStatusE.ERROR,
                                          CyclerDataExpStatusE.FINISHED):
                    self.__actual_exp_id = -1
        elif command.cmd_type == MidStrReqCmdE.TURN_DEPRECATED:
            log.info("Turning cycler station to deprecated")
            self.db_iface.turn_cycler_station_deprecated(
                exp_id= self.__actual_exp_id if self.__actual_exp_id != -1 else None)
            self.working_flag.clear()
        else:
            log.error(("Can`t apply command. Error in command format, "
                       "check command type and payload type"))

    def sync_shd_data(self) -> None:
        '''Update local data
        '''
        self.db_iface.all_status: CyclerDataAllStatusC = self.globlal_all_status.read()
        self.db_iface.gen_meas: CyclerDataGenMeasC     = self.globlal_gen_meas.read()
        self.db_iface.ext_meas: CyclerDataExtMeasC     = self.globlal_ext_meas.read()


    def stop(self) -> None:
        """Stop the node if it is not already closed .
        """
        #Before closing connection commit all changes
        self.db_iface.commit_changes()
        self.db_iface.close_db_connection()
        self.working_flag.clear()
        self.status = SysShdNodeStatusE.STOP
        log.critical(f"Stopping {current_thread().name} node")

    def process_iteration(self) -> None:
        """AI is creating summary for process_iteration
        """
        try:
            # Syncronising shared data
            self.sync_shd_data()
            # Receive and write alarms
            self.__receive_alarms()

            if len(self.__new_raised_alarms)>0:
                self.db_iface.write_new_alarm(alarms= self.__new_raised_alarms,
                                              exp_id= self.__actual_exp_id)
                self.__new_raised_alarms.clear()
            ### Write measures and status changes
            if self.db_iface.gen_meas.instr_id is not None and self.__actual_exp_id != -1:
                self.db_iface.write_generic_measures(exp_id= self.__actual_exp_id)
                ## TODO: remove commit, should work without this commit # pylint: disable=fixme
                self.db_iface.commit_changes()
                self.db_iface.write_status_changes(exp_id= self.__actual_exp_id)
                self.db_iface.write_extended_measures(exp_id= self.__actual_exp_id)
                self.db_iface.meas_id += 1
            if not self.str_reqs.is_empty():
                # Ignore warning as receive_data return an object,
                # which in this case must be of type DrvCanCmdDataC
                command : MidStrCmdDataC = self.str_reqs.receive_data() # type: ignore
                log.debug(f"Command to apply: {command.cmd_type.name}")
                self.__apply_command(command)
            # TIMEOUT added to detect if database connection was ended
            func_timeout(DEFAULT_TIMEOUT_CONNECTION, self.db_iface.commit_changes)
        except FunctionTimedOut as exc:
            log.warning(("Timeout during commit changes to local database."
                         f"Database connection will be restarted. {exc}"))
            self.status = SysShdNodeStatusE.COMM_ERROR
            self.db_iface.reset_db_connection()
        except ConnectionError as exc:
            self.status = SysShdNodeStatusE.COMM_ERROR
            log.critical(f"Communication error in str node {exc}")
        except Exception as exc:
            self.status = SysShdNodeStatusE.INTERNAL_ERROR
            log.critical(f"Unexpected error in MID_STR_Node_c thread.\n{exc}")
            self.working_flag.clear()

#######################            FUNCTIONS             #######################
