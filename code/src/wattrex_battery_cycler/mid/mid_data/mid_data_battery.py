#!/usr/bin/python3
'''
Definition of MID DATA battery related info.
'''
#######################        MANDATORY IMPORTS         #######################
from __future__ import annotations

#######################         GENERIC IMPORTS          #######################

#######################       THIRD PARTY IMPORTS        #######################

#######################      SYSTEM ABSTRACTION IMPORTS  #######################
from system_logger_tool import sys_log_logger_get_module_logger
log = sys_log_logger_get_module_logger(__name__)
#######################          PROJECT IMPORTS         #######################

#######################          MODULE IMPORTS          #######################
from .mid_data_experiment import MidDataPwrRangeC
#######################              ENUMS               #######################

#######################             CLASSES              #######################

class MidDataBatteryC:
    '''
    Generic battery info.
    '''
    # pylint: disable=too-many-arguments
    def __init__(self, name: str| None= None, model : str| None= None, volt_min : int = 800,
                 volt_max : int = 1200, curr_min : int = 0,
                 curr_max : int = 5000) -> None:

        self.name : str = name
        self.model : str = model
        self.elec_ranges: MidDataPwrRangeC = MidDataPwrRangeC(volt_min, volt_max,
                                                              curr_min, curr_max)


class MidDataRedoxBatC(MidDataBatteryC):
    '''
    Redox flow specific battery info.
    '''
    # pylint: disable=too-many-arguments
    def __init__(self, electrolyte_vol : int| None= None, name: str| None= None,
                model : str| None= None, volt_min : int = 800, volt_max : int = 1200,
                curr_min : int = 0, curr_max : int = 5000) -> None:

        self.electrolyte_vol : int| None = electrolyte_vol
        super().__init__(name, model, volt_min, volt_max, curr_min, curr_max)


class MidDataLithiumBatC(MidDataBatteryC):
    '''
    Lithium specific battery info.
    '''
    # pylint: disable=too-many-arguments
    def __init__(self, capacity : int| None= None, name: str| None= None, model : str| None= None,
                volt_min : int = 800, volt_max : int = 1200, curr_min : int = 0,
                curr_max : int = 5000) -> None:

        self.capacity : int| None= None = capacity
        super().__init__(name, model, volt_min, volt_max, curr_min, curr_max)
