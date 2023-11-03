#!/usr/bin/python3
"""
This module will create a node that will gathers the measurements of the devices.
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

from system_shared_tool import SysShdSharedObjC, SysShdNodeC, SysShdNodeParamsC, SysShdErrorC, SysShdNodeStatusE
from wattrex_battery_cycler_datatypes.cycler_data import (CyclerDataDeviceC, CyclerDataGenMeasC,
            CyclerDataDeviceTypeE, CyclerDataExtMeasC, CyclerDataAllStatusC, CyclerDataMergeTagsC)

#######################          MODULE IMPORTS          #######################
from ..mid_dabs import MidDabsPwrMeterC, MidDabsExtraMeterC #pylint: disable= relative-beyond-top-level
#######################          PROJECT IMPORTS         #######################

#######################              ENUMS               #######################

#######################             CLASSES              #######################
# meter_counter: int = 0

class MidMeasNodeC(SysShdNodeC): #pylint: disable=too-many-instance-attributes
    """Returns a removable version of the DRv command .

    Args:
        threading ([type]): [description]
    """

    def __init__(self,shared_gen_meas: SysShdSharedObjC, shared_ext_meas: SysShdSharedObjC, #pylint: disable= too-many-arguments
                 shared_status: SysShdSharedObjC, cycle_period: int, working_flag : Event,
                 devices: List[CyclerDataDeviceC], excl_tags: CyclerDataMergeTagsC,
                 meas_params: SysShdNodeParamsC= SysShdNodeParamsC()) -> None:
        '''
        Initialize the thread node used to update measurements from devices.
        '''
        super().__init__(name= "Meas_Node",cycle_period= cycle_period, working_flag= working_flag,
                        node_params= meas_params)
        self.working_flag = working_flag
        self.__extra_meter: List[MidDabsExtraMeterC] = []
        for dev in devices:
            if dev.device_type in (CyclerDataDeviceTypeE.BK, CyclerDataDeviceTypeE.BMS):
                self.__extra_meter.append(MidDabsExtraMeterC(dev))
                devices.remove(dev)
        self.__pwr_dev: MidDabsPwrMeterC = MidDabsPwrMeterC(devices)
        self.globlal_gen_meas: SysShdSharedObjC = shared_gen_meas
        self.globlal_ext_meas: SysShdSharedObjC = shared_ext_meas
        self.globlal_all_status: SysShdSharedObjC = shared_status
        self.__shd_excl_tags: CyclerDataMergeTagsC = excl_tags
        self._all_status: CyclerDataAllStatusC = self.globlal_all_status.read()
        self._gen_meas: CyclerDataGenMeasC = self.globlal_gen_meas.read()
        self._ext_meas: CyclerDataExtMeasC = self.globlal_ext_meas.read()
        ## Period for extra meters
        # self.__meter_period: int = 10

    def sync_shd_data(self) -> None:
        '''Update
        '''
        try:
            ## TODO: CHANGE TO MERGE EXCLUDE TAGS
            # self.globlal_all_status.merge_exclude_tags(self._all_status,
            #                                     included_tags= self.__shd_excl_tags.status_attrs)
            # self.globlal_gen_meas.merge_included_tags(new_obj= self._gen_meas,
            #                                     included_tags= self.__shd_excl_tags.gen_meas_attrs)
            # self.globlal_ext_meas.merge_included_tags(self._ext_meas,
            #                                     included_tags= self.__shd_excl_tags.ext_meas_attrs)
            self.globlal_all_status.write(self._all_status)
            self.globlal_gen_meas.write(self._gen_meas)
            self.globlal_ext_meas.write(self._ext_meas)
        except SysShdErrorC as err:
            log.error(f"Failed to sync ext shared data: {err}")

    def process_iteration(self) -> None:
        """Processes a single iteration.
        """
        # Update the measurements and status of the devices.
        self.__pwr_dev.update(self._gen_meas, self._ext_meas, self._all_status)
        # Update the measurements and status of the extra devices.
        # Future versions could include period for each extra meter
        # global meter_counter
        # if meter_counter == 0:
        #     meter_counter = meter_counter % self.__meter_period
        # meter_counter += 1
        for dev in self.__extra_meter:
            log.info("Updating extra meter")
            dev.update(self._ext_meas)
        # Sync the shared data with the updated data.
        self.sync_shd_data()
        if self._gen_meas.current is not None and self._gen_meas.voltage is not None:
            self.status = SysShdNodeStatusE.OK

    def stop(self) -> None:
        """Close the thread.
        """
        for dev in self.__extra_meter:
            dev.close()
        self.__pwr_dev.close()
        super().stop()
