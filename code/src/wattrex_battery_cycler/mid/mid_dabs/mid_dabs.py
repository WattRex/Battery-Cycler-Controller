#!/usr/bin/python3
"""
This module will create instances of epc device in order to control
the device and request info from it.
"""
#######################        MANDATORY IMPORTS         #######################
from __future__ import annotations

#######################         GENERIC IMPORTS          #######################
from enum import Enum

#######################       THIRD PARTY IMPORTS        #######################
from system_config_tool import sys_conf_read_config_params

from system_logger_tool import SysLogLoggerC, sys_log_logger_get_module_logger, Logger
if __name__ == '__main__':
    cycler_logger = SysLogLoggerC(file_log_levels= 'log_config.yaml')
log: Logger = sys_log_logger_get_module_logger(__name__)

from scpi_sniffer       import DrvScpiHandlerC
from wattrex_driver_epc import DrvEpcDeviceC
from wattrex_driver_ea  import DrvEaDeviceC
from wattrex_driver_rs  import DrvRsDeviceC
from wattrex_driver_bk import DrvBkDeviceC

from system_shared_tool import SysShdChanC
#######################          MODULE IMPORTS          #######################

#######################          PROJECT IMPORTS         #######################
from ..mid_data import MidDataDeviceTypeE, MidDataDeviceC, MidDataPwrLimitE
#######################              ENUMS               #######################
#######################             CLASSES              #######################
class MidDabsPwrMeterC:
    '''Instanciates an object enable to measure.
    '''
    def __init__(self, device: MidDataDeviceC, device_conf: dict, tx_queue: SysShdChanC) -> None:
        self.device_type = device.device_type
        self.__bisource   : DrvEaDeviceC | None = None
        self.__source     : DrvEaDeviceC | None = None
        self.__load       : DrvRsDeviceC | None = None
        self.__epc        : DrvEpcDeviceC| None = None
        self.__meter      : DrvBkDeviceC | None = None
        try:
            if self.device_type is MidDataDeviceTypeE.EPC:
                # TODO: UPDATE DrvEpcDeviceC-> no queues in arguments are created internally
                self.__epc : DrvEpcDeviceC = DrvEpcDeviceC(dev_id=int(device_conf['epc']['can_id']),
                                device_handler= SysShdChanC(), tx_can_queue= tx_queue)
                self.__epc.open()
            elif self.device_type is MidDataDeviceTypeE.SOURCE and 'source' in device_conf:
                # TODO: Update SCPI not needing
                self.__source : DrvEaDeviceC = DrvEaDeviceC(
                    DrvScpiHandlerC(port=device_conf['source']['port'],
                                    separator= device_conf['source']['separator'],
                                    baudrate = int(device_conf['source']['baudrate']),
                                    timeout = device_conf['source']['timeout'],
                                    write_timeout = device_conf['source']['write_timeout'],
                                    parity = device_conf['source']['parity']))
            elif self.device_type is MidDataDeviceTypeE.LOAD and 'load' in device_conf:
                self.__load : DrvRsDeviceC = DrvRsDeviceC(
                    DrvScpiHandlerC(port =device_conf['load']['port'],
                                    separator = device_conf['load']['separator'],
                                    baudrate = int(device_conf['load']['baudrate']),
                                    timeout = device_conf['load']['timeout'],
                                    write_timeout= device_conf['load']['write_timeout'],
                                    parity = device_conf['load']['parity']))
            elif self.device_type is MidDataDeviceTypeE.BISOURCE and 'bisource' in device_conf:
                self.__bisource : DrvEaDeviceC = DrvEaDeviceC(
                    DrvScpiHandlerC(port =device_conf['bisource']['port'],
                                    separator = device_conf['bisource']['separator'],
                                    baudrate = int(device_conf['bisource']['baudrate']),
                                    timeout = device_conf['bisource']['timeout'],
                                    write_timeout = device_conf['bisource']['write_timeout'],
                                    parity = device_conf['bisource']['parity']))
            elif self.device_type is MidDataDeviceTypeE.METER and 'meter' in device_conf:
                self.meter : DrvBkDeviceC = DrvBkDeviceC(
                            DrvScpiHandlerC(port=device_conf['port'],
                                    separator = device_conf['separator'],
                                    baudrate = int(device_conf['bisource']['baudrate']),
                                    timeout = device_conf['bisource']['timeout'],
                                    write_timeout = device_conf['bisource']['write_timeout'],
                                    parity = device_conf['bisource']['parity']))
            else:
                log.error("The dessire device doesn't have values in yaml file")
        except Exception as error:
            log.error(error)
            raise error

    def update(self):
        """Update the data from the hardware sendind the corresponding messages.
        """
        if self.device_type is MidDataDeviceTypeE.BISOURCE:
            self.__bisource.get_data()
        elif self.device_type is MidDataDeviceTypeE.SOURCE:
            self.__source.get_data()
        elif self.device_type is MidDataDeviceTypeE.LOAD:
            self.__load.get_data()
        elif self.device_type is MidDataDeviceTypeE.METER:
            self.meter.get_data()
        elif self.device_type is MidDataDeviceTypeE.EPC:
            self.__epc.get_data(update=True)

class MidDabsPwrDevC(MidDabsPwrMeterC):
    """Instanciates an object enable to control the devices.
    """
    def _init__(self, device: MidDataDeviceC, device_conf: dict, tx_queue: SysShdChanC)->None:
        super().__init__(device, device_conf, tx_queue)

    def set_cv_mode(self,volt_ref: int, current_limit: int):
        """Set the CV mode with the given voltage and current limit.

        Args:
            volt_ref (int): [voltage in mV]
            current_limit (int): [current in mA]
        """
        try:
            if self.device_type is MidDataDeviceTypeE.BISOURCE:
                self.__bisource.set_cv_mode(volt_ref, current_limit)
            elif self.device_type is MidDataDeviceTypeE.SOURCE:
                self.__source.set_cv_mode(volt_ref, current_limit)
            elif self.device_type == MidDataDeviceTypeE.LOAD:
                # TODO: upgrade DrvRs to write limits when setting modes
                self.__load.set_cv_mode(volt_ref)
            else:
                log.error("The device is not able to change between modes.")
                raise ValueError("The device is not able to change between modes")
        except Exception as err:
            log.error(f"Error while setting cv mode: {err}")
            raise Exception("Error while setting cv mode") from err

    def set_cc_mode(self, current_ref: int, volt_limit: int) -> None:
        """Set the CC mode with the given current and voltage limit.

        Args:
            current_ref (int): [current in mA]
            volt_limit (int): [voltage in mV]
        """
        try:
            if self.device_type is MidDataDeviceTypeE.BISOURCE:
                self.__bisource.set_cc_mode(current_ref, volt_limit)
            elif self.device_type is MidDataDeviceTypeE.SOURCE:
                self.__source.set_cc_mode(current_ref, volt_limit)
            elif self.device_type is MidDataDeviceTypeE.LOAD:
                # TODO: upgrade DrvRs to write limits when setting modes
                self.__load.set_cc_mode(current_ref)
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
                self.__bisource.disable()
            elif self.device_type is MidDataDeviceTypeE.SOURCE:
                self.__bisource.disable()
            elif self.device_type is MidDataDeviceTypeE.LOAD:
                self.__load.disable()
            else:
                log.error("The device can not be disable")
                raise ValueError("The device can not be disable")
        except Exception as err:
            log.error(f"Error while setting cc mode: {err}")
            raise Exception("Error while setting cc mode") from err

class MidDabsEpcDevC(MidDabsPwrMeterC):
    """Class method for class - method that returns a class class for MIDDabsPwrC .
    """
    def _init__(self, device: MidDataDeviceC, device_conf: dict, tx_queue: SysShdChanC)->None:
        if device.device_type is MidDataDeviceTypeE.EPC:
            log.error((("Trying to instanciate a epc device but "
                             f"receive type {device.device_type.name}")))
            raise ValueError(("Trying to instanciate a epc device but "
                             f"receive type {device.device_type.name}"))
        super().__init__(device, device_conf, tx_queue)

    def set_cc_mode(self, current_ref: int, limit_type: MidDataPwrLimitE, limit_ref: int) -> None:
        """Set the CC mode with the specified limits.

        Args:
            current_ref (int): [description]
            limit_type (MidDataPwrLimitE): [description]
            limit_ref (int): [description]
        """
        try:
            self.__epc.set_cc_mode(current_ref, limit_type, limit_ref)
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
            self.__epc.set_cv_mode(volt_ref, limit_type, limit_ref)
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
            self.__epc.set_cp_mode(pwr_ref, limit_type, limit_ref)
        except Exception as err:
            log.error(f"Error while setting cp mode: {err}")
            raise Exception(f"Error while setting cp mode") from err
    
    def set_wait_mode(self, limit_type: MidDataPwrLimitE, limit_ref):
        try:
            self.__epc.set_wait_mode(limit_type, limit_ref)
        except Exception as err:
            log.error(f"Error while setting wait mode: {err}")
            raise Exception(f"Error while setting wait mode") from err

    def disable(self):
        """Disable the EPC device.
        """
        try:
            self.__epc.disable()
        except Exception as err:
            log.error(f"Error while setting cv mode: {err}")
            raise Exception(f"Error while setting cv mode") from err
