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
    def __init__(self, name: str| None= None, model : str| None= None,
                 elec_ranges: MidDataPwrRangeC|None= None) -> None:

        self.name : str|None = name
        self.model : str|None = model
        self.elec_ranges: MidDataPwrRangeC|None = elec_ranges

class MidDataRedoxBatC(MidDataBatteryC):
    '''
    Redox flow specific battery info.
    '''
    # pylint: disable=too-many-arguments
    def __init__(self, electrolyte_vol : int| None= None, name: str| None= None,
                model : str| None= None, elec_ranges: MidDataPwrRangeC|None = None) -> None:

        self.electrolyte_vol : int| None = electrolyte_vol
        super().__init__(name= name, model= model, elec_ranges= elec_ranges)


class MidDataLithiumBatC(MidDataBatteryC):
    '''
    Lithium specific battery info.
    '''
    # pylint: disable=too-many-arguments
    def __init__(self, capacity : int| None= None, name: str| None= None, model : str| None= None,
                elec_ranges: MidDataPwrRangeC|None= None) -> None:

        self.capacity : int| None= capacity
        super().__init__(name= name, model= model, elec_ranges= elec_ranges)
