#!/usr/bin/python3
"""
This module will manage CAN messages and channels
in order to configure channels and send/received messages.
"""
#######################        MANDATORY IMPORTS         #######################
from __future__ import annotations

#######################         GENERIC IMPORTS          #######################
from enum import Enum

#######################       THIRD PARTY IMPORTS        #######################

#######################    SYSTEM ABSTRACTION IMPORTS    #######################
from system_logger_tool import sys_log_logger_get_module_logger, SysLogLoggerC, Logger

#######################       LOGGER CONFIGURATION       #######################
if __name__ == '__main__':
    cycler_logger = SysLogLoggerC(file_log_levels='../log_config.yaml')
log: Logger = sys_log_logger_get_module_logger(__name__)

#######################          MODULE IMPORTS          #######################
from wattrex_battery_cycler_datatypes.cycler_data import (CyclerDataProfileC, CyclerDataExpStatusE,
            CyclerDataBatteryC, CyclerDataExperimentC, CyclerDataCyclerStationC)
#######################          PROJECT IMPORTS         #######################

#######################              ENUMS               #######################


#######################             CLASSES              #######################

class MidStrReqCmdE(Enum):
    """
    Type of command for the CAN
    """
    GET_NEW_EXP     = 0
    GET_EXP_STATUS  = 1
    GET_CS          = 2
    GET_CS_STATUS   = 3
    SET_EXP_STATUS  = 4
    TURN_DEPRECATED = 5

class MidStrDataCmdE(Enum):
    """Type of data send as return for the request.
    """
    EXP_DATA    = 0
    EXP_STATUS  = 1
    CS_DATA     = 2
    CS_STATUS   = 3


class MidStrCmdDataC:
    """Class that wrapp the messages send through the queue, containing the request and returns.
    """
    def __init__(self, cmd_type: MidStrDataCmdE|MidStrDataCmdE, #pylint: disable= too-many-arguments
                exp_status: CyclerDataExpStatusE|None= None,
                experiment: CyclerDataExperimentC|None= None,
                profile: CyclerDataProfileC|None= None, battery: CyclerDataBatteryC|None= None,
                station: CyclerDataCyclerStationC|None= None, station_status: bool|None= None):
        self.cmd_type = cmd_type
        self.error_flag = True
        if cmd_type is MidStrDataCmdE.EXP_DATA:
            ## Check if the experiment is ok or if there is no experiment at all
            if (all(var is not None for var in (experiment, profile, battery)) or
                    all(var is None for var in (experiment, profile, battery))):
                self.error_flag = False
            self.experiment = experiment
            self.profile = profile
            self.battery = battery
        elif cmd_type is MidStrDataCmdE.CS_DATA:
            if station is not None:
                self.error_flag = False
            self.station = station
        elif cmd_type is MidStrDataCmdE.CS_STATUS:
            if station_status is not None:
                self.error_flag = False
            self.station_status = station_status
        elif cmd_type is MidStrDataCmdE.EXP_STATUS or cmd_type is MidStrReqCmdE.SET_EXP_STATUS:
            if exp_status is not None:
                self.error_flag = False
            self.exp_status = exp_status
