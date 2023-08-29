#!/usr/bin/python3
"""
This module will create instances of epc device in order to control
the device and request info from it.
"""
#######################        MANDATORY IMPORTS         #######################
from __future__ import annotations

#######################         GENERIC IMPORTS          #######################
from enum import Enum
from typing import Dict

#######################       THIRD PARTY IMPORTS        #######################
from system_config_tool import sys_conf_read_config_params

from system_logger_tool import SysLogLoggerC, sys_log_logger_get_module_logger, Logger
if __name__ == '__main__':
    cycler_logger = SysLogLoggerC(file_log_levels= 'log_config.yaml')
log: Logger = sys_log_logger_get_module_logger(__name__)

from scpi_sniffer       import DrvScpiHandlerC
from wattrex_drv_epc import DrvEpcDeviceC
from wattrex_driver_ea  import DrvEaDeviceC
from wattrex_driver_rs  import DrvRsDeviceC
from wattrex_driver_bk import DrvBkDeviceC

from system_shared_tool import SysShdIpcChanC

#######################          MODULE IMPORTS          #######################

#######################          PROJECT IMPORTS         #######################
from mid.mid_data import MidDataDeviceTypeE, MidDataDeviceC, MidDataPwrLimitE
#######################              ENUMS               #######################

class _ConstantsC:
    ''' Constants the script may need
    '''
    TO_DECI_WATS = 100000
    MAX_READS    = 300
    MASK         = 0x7F0

#######################             CLASSES              #######################
class MidDabsPwrMeterC(MidDataDeviceC):
    '''Instanciates an object enable to measure.
    '''
    def __init__(self, manufacturer : str, model : str, serial_number : str,
                device_type : MidDataDeviceTypeE, iface_name : str, mapping_names : Dict) -> None:
        super().__init__(manufacturer, model, serial_number, device_type, iface_name, mapping_names)
        self.bisource  : DrvEaDeviceC| None = None
        self.source     : DrvEaDeviceC| None = None
        self.load       : DrvRsDeviceC| None = None
        self.epc        : DrvEpcDeviceC|None = None
        self.meter      : DrvBkDeviceC|None = None
        try:
            if self.device_type is MidDataDeviceTypeE.EPC:
                # TODO: UPDATE DrvEpcDeviceC-> no queues in arguments are created internally
                self.epc : DrvEpcDeviceC = DrvEpcDeviceC(dev_id=int(mapping_names['epc']['can_id']))
            elif self.device_type is MidDataDeviceTypeE.SOURCE and 'source' in mapping_names:
                # TODO: Update SCPI not needing 
                self.source : DrvEaDeviceC = DrvEaDeviceC(
                    DrvScpiHandlerC(port=mapping_names['source']['port'],
                                    separator= mapping_names['source']['separator'],
                                    baudrate = int(mapping_names['source']['baudrate']),
                                    timeout = mapping_names['source']['timeout'],
                                    write_timeout = mapping_names['source']['write_timeout'],
                                    parity = mapping_names['source']['parity']))
            elif self.device_type is MidDataDeviceTypeE.LOAD and 'load' in mapping_names:
                self.load : DrvRsDeviceC = DrvRsDeviceC(
                    DrvScpiHandlerC(port =mapping_names['load']['port'],
                                    separator = mapping_names['load']['separator'],
                                    baudrate = int(mapping_names['load']['baudrate']),
                                    timeout = mapping_names['load']['timeout'],
                                    write_timeout= mapping_names['load']['write_timeout'],
                                    parity = mapping_names['load']['parity']))
            elif self.device_type is MidDataDeviceTypeE.BISOURCE and 'bisource' in mapping_names:
                self.bisource : DrvEaDeviceC = DrvEaDeviceC(
                    DrvScpiHandlerC(port =mapping_names['bisource']['port'],
                                    separator = mapping_names['bisource']['separator'],
                                    baudrate = int(mapping_names['bisource']['baudrate']),
                                    timeout = mapping_names['bisource']['timeout'],
                                    write_timeout = mapping_names['bisource']['write_timeout'],
                                    parity = mapping_names['bisource']['parity']))
            elif self.device_type is MidDataDeviceTypeE.METER and 'meter' in mapping_names:
                self.meter : DrvBkDeviceC = DrvBkDeviceC(
                            DrvScpiHandlerC(port=mapping_names['port'],
                                    separator = mapping_names['separator'],
                                    baudrate = int(mapping_names['bisource']['baudrate']),
                                    timeout = mapping_names['bisource']['timeout'],
                                    write_timeout = mapping_names['bisource']['write_timeout'],
                                    parity = mapping_names['bisource']['parity']))
            else:
                log.error("The dessire device doesn't have values in yaml file")
        except Exception as error:
            log.error(error)
            raise error

    def update(self):
        """Update the data from the hardware sendind the corresponding messages.
        """
        if self.device_type is MidDataDeviceTypeE.BISOURCE:
            self.bisource.get_data()
        elif self.device_type is MidDataDeviceTypeE.SOURCE:
            self.source.get_data()
        elif self.device_type is MidDataDeviceTypeE.LOAD:
            self.load.get_data()
        elif self.device_type is MidDataDeviceTypeE.METER:
            self.meter.get_data()
        elif self.device_type is MidDataDeviceTypeE.EPC:
            self.epc.get_data(update=True)

class MidDabsPwrDevC(MidDabsPwrMeterC):
    """Instanciates an object enable to control the devices.
    """
    def _init__(self, manufacturer : str, model : str, serial_number : str,
                device_type : MidDataDeviceTypeE, iface_name : str, mapping_names : Dict)->None:
        super().__init__(manufacturer, model, serial_number, device_type, iface_name, mapping_names)

    def set_cv_mode(self,volt_ref: int, current_limit: int):
        """Set the CV mode with the given voltage and current limit.

        Args:
            volt_ref (int): [voltage in mV]
            current_limit (int): [current in mA]
        """
        try:
            if self.device_type == [MidDataDeviceTypeE.BISOURCE, MidDataDeviceTypeE.SOURCE]:
                self.bisource.set_cv_mode(volt_ref, current_limit)
            elif self.device_type == MidDataDeviceTypeE.LOAD:
                # TODO: upgrade DrvRs to write limits when setting modes
                self.load.set_cv_mode(volt_ref)
            else:
                log.error("The device is not able to change between modes.")
                raise ValueError("The device is not able to change between modes")
        except Exception as err:
            log.error(f"Error while setting cv mode: {err}")
            raise Exception(f"Error while setting cv mode") from err

    def set_cc_mode(self,current_ref: int, volt_limit: int) -> None:
        """Set the CC mode with the given current and voltage limit.

        Args:
            current_ref (int): [current in mA]
            volt_limit (int): [voltage in mV]
        """
        try:
            if self.device_type is MidDataDeviceTypeE.BISOURCE:
                self.bisource.set_cc_mode(current_ref, volt_limit)
            elif self.device_type is MidDataDeviceTypeE.SOURCE:
                self.bisource.set_cc_mode(current_ref, volt_limit)
            elif self.device_type is MidDataDeviceTypeE.LOAD:
                # TODO: upgrade DrvRs to write limits when setting modes
                self.load.set_cc_mode(current_ref)
            else:
                log.error("The device is not able to change between modes.")
                raise ValueError("The device is not able to change between modes")
        except Exception as err:
            log.error(f"Error while setting cc mode: {err}")
            raise Exception("Error while setting cc mode") from err

    def disable(self) -> None:
        """Disable the devices.
        """
        try:
            if self.device_type is MidDataDeviceTypeE.BISOURCE:
                self.bisource.disable()
            elif self.device_type is MidDataDeviceTypeE.SOURCE:
                self.bisource.disable()
            elif self.device_type is MidDataDeviceTypeE.LOAD:
                self.load.disable()
            else:
                log.error("The device can not be disable")
                raise ValueError("The device can not be disable")
        except Exception as err:
            log.error(f"Error while setting cc mode: {err}")
            raise Exception("Error while setting cc mode") from err

class MidDabsPwrDevEpcC(MidDabsPwrMeterC):
    """Class method for class - method that returns a class class for MIDDabsPwrC .
    """
    def __init__(self,manufacturer : str, model : str, serial_number : str,
            device_type : MidDataDeviceTypeE, iface_name : str, mapping_names : Dict)->None:
        if device_type is MidDataDeviceTypeE.EPC:
            log.error((("Trying to instanciate a epc device but "
                             f"receive type {device_type.name}")))
            raise ValueError(("Trying to instanciate a epc device but "
                             f"receive type {device_type.name}"))
        super().__init__(manufacturer, model, serial_number, device_type, iface_name, mapping_names)
    
    def set_cc_mode(self, current_ref: int, limit_type: MidDataPwrLimitE, limit_ref: int) -> None:
        """Set the CC mode with the specified limits.

        Args:
            current_ref (int): [description]
            limit_type (MidDataPwrLimitE): [description]
            limit_ref (int): [description]
        """
        try:
            self.epc.set_cc_mode(current_ref, limit_type, limit_ref)
        except Exception as err:
            log.error(f"Error while setting cc mode: {err}")
            raise Exception(f"Error while setting cc mode") from err
    def set_cv_mode(self, volt_ref: int, limit_type: MidDataPwrLimitE, limit_ref: int) -> None:
        """Set the CV mode with the specified limits.

        Args:
            volt_ref (int): [description]
            limit_type (MidDataPwrLimitE): [description]
            limit_ref (int): [description]
        """
        try:
            self.epc.set_cv_mode(volt_ref, limit_type, limit_ref)
        except Exception as err:
            log.error(f"Error while setting cv mode: {err}")
            raise Exception(f"Error while setting cv mode") from err
    def set_cp_mode(self, pwr_ref: int, limit_type: MidDataPwrLimitE, limit_ref: int) -> None:
        """Set the CP mode with the specified limits.

        Args:
            pwr_ref (int): [description]
            limit_type (MidDataPwrLimitE): [description]
            limit_ref (int): [description]
        """
        try:
            self.epc.set_cp_mode(pwr_ref, limit_type, limit_ref)
        except Exception as err:
            log.error(f"Error while setting cp mode: {err}")
            raise Exception(f"Error while setting cp mode") from err
    def disable(self):
        """Disable the EPC device.
        """
        try:
            self.epc.disable()
        except Exception as err:
            log.error(f"Error while setting cv mode: {err}")
            raise Exception(f"Error while setting cv mode") from err
