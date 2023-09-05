#!/usr/bin/python3
"""
This module will create instances of epc device in order to control
the device and request info from it.
"""
#######################        MANDATORY IMPORTS         #######################
from __future__ import annotations

#######################         GENERIC IMPORTS          #######################
from threading import Event
from datetime import datetime
#######################       THIRD PARTY IMPORTS        #######################

from system_logger_tool import SysLogLoggerC, sys_log_logger_get_module_logger, Logger
if __name__ == '__main__':
    cycler_logger = SysLogLoggerC(file_log_levels= 'log_config.yaml')
log: Logger = sys_log_logger_get_module_logger(__name__)

from system_config_tool import sys_conf_read_config_params
from system_shared_tool import SysShdSharedObjC, SysShdNodeC, SysShdParamsC

#######################          MODULE IMPORTS          #######################
from ..mid_dabs import MidDabsPwrMeterC
from ..mid_data import MidDataDeviceTypeE, MidDataDeviceC,\
            MidDataGenMeasC, MidDataExtMeasC, MidDataAllStatusC
#######################          PROJECT IMPORTS         #######################

#######################              ENUMS               #######################

#######################             CLASSES              #######################

class MidMeasNodeC(SysShdNodeC):
    """Returns a removable version of the DRv command .

    Args:
        threading ([type]): [description]
    """

    def __init__(self, cycle_period: float, working_flag : Event, config_file: str,
                 meas_params: SysShdParamsC= SysShdParamsC()) -> None:
        '''
        Initialize the thread node used to update measurements from devices.
        '''

        super().__init__(cycle_period, working_flag, meas_params)
        conf_param = sys_conf_read_config_params(config_file)
        self.working_flag = working_flag
        self.devices: MidDabsPwrMeterC = MidDabsPwrMeterC([MidDataDeviceC(**conf_param)])
        self.globlal_gen_meas: SysShdSharedObjC
        self.globlal_ext_meas: SysShdSharedObjC
        self.globlal_all_status: SysShdSharedObjC
        self.__all_status: MidDataAllStatusC
        self.__gen_meas: MidDataGenMeasC
        self.__ext_meas: MidDataExtMeasC

    def sync_shd_data(self) -> None:
        '''Update 
        '''
        self.__all_status = self.globlal_all_status.merge_exclude_tags(self.__all_status, [])
        self.__gen_meas = self.globlal_gen_meas.merge_exclude_tags(self.__gen_meas, [])
        self.__ext_meas = self.globlal_ext_meas.merge_exclude_tags(self.__ext_meas, [])

    def process_iteration(self) -> None:
        """Processes a single iteration.
        """
        # Update the measurements and status of the devices.
        self.devices.update(self.__gen_meas, self.__ext_meas, self.__all_status)
        # Sync the shared data with the updated data.
        self.sync_shd_data()

#######################            FUNCTIONS             #######################
