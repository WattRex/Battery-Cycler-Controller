#!/usr/bin/python3
"""
This module will create instances of epc device in order to control
the device and request info from it.
"""
#######################        MANDATORY IMPORTS         #######################
from __future__ import annotations
from typing import List
#######################         GENERIC IMPORTS          #######################
from threading import Event
#######################       THIRD PARTY IMPORTS        #######################

from system_logger_tool import SysLogLoggerC, sys_log_logger_get_module_logger, Logger
if __name__ == '__main__':
    cycler_logger = SysLogLoggerC(file_log_levels= 'log_config.yaml')
log: Logger = sys_log_logger_get_module_logger(__name__)

from system_shared_tool import SysShdSharedObjC, SysShdNodeC, SysShdNodeParamsC, SysShdErrorC

#######################          MODULE IMPORTS          #######################
from ..mid_dabs import MidDabsPwrMeterC #pylint: disable= relative-beyond-top-level
from ..mid_data import MidDataDeviceC, MidDataGenMeasC, MidDataExtMeasC, MidDataAllStatusC #pylint: disable= relative-beyond-top-level
#######################          PROJECT IMPORTS         #######################

#######################              ENUMS               #######################

#######################             CLASSES              #######################

class MidMeasNodeC(SysShdNodeC): #pylint: disable=too-many-instance-attributes
    """Returns a removable version of the DRv command .

    Args:
        threading ([type]): [description]
    """

    def __init__(self,shared_gen_meas: SysShdSharedObjC, shared_ext_meas: SysShdSharedObjC, #pylint: disable= too-many-arguments
                 shared_status: SysShdSharedObjC, cycle_period: int, working_flag : Event,
                 devices: List[MidDataDeviceC],
                 meas_params: SysShdNodeParamsC= SysShdNodeParamsC()) -> None:
        '''
        Initialize the thread node used to update measurements from devices.
        '''
        super().__init__(name= "Meas_Node",cycle_period= cycle_period, working_flag= working_flag, 
                        node_params= meas_params)
        self.working_flag = working_flag
        self.devices: MidDabsPwrMeterC = MidDabsPwrMeterC(devices)
        self.globlal_gen_meas: SysShdSharedObjC = shared_gen_meas
        self.globlal_ext_meas: SysShdSharedObjC = shared_ext_meas
        self.globlal_all_status: SysShdSharedObjC = shared_status
        self._all_status: MidDataAllStatusC = MidDataAllStatusC()
        self._gen_meas: MidDataGenMeasC = MidDataGenMeasC(voltage= 0, current= 0, power= 0)
        self._ext_meas: MidDataExtMeasC = MidDataExtMeasC()

    def sync_shd_data(self) -> None:
        '''Update 
        '''
        try:
            self.globlal_all_status.write(self._all_status)
            self.globlal_gen_meas.write(self._gen_meas)
            self.globlal_ext_meas.write(self._ext_meas)
        except SysShdErrorC as err:
            log.error(f"Failed to sync shared data: {err}")

    def process_iteration(self) -> None:
        """Processes a single iteration.
        """
        # Update the measurements and status of the devices.
        self.devices.update(self._gen_meas, self._ext_meas, self._all_status)
        # Sync the shared data with the updated data.
        self.sync_shd_data()

    def stop(self) -> None:
        """Close the thread.
        """
        self.devices.close()
        super().stop()
