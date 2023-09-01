#!/usr/bin/python3
"""
This module will create instances of epc device in order to control
the device and request info from it.
"""
#######################        MANDATORY IMPORTS         #######################
from __future__ import annotations

#######################         GENERIC IMPORTS          #######################

#######################       THIRD PARTY IMPORTS        #######################

from system_logger_tool import SysLogLoggerC, sys_log_logger_get_module_logger, Logger
if __name__ == '__main__':
    cycler_logger = SysLogLoggerC(file_log_levels= 'log_config.yaml')
log: Logger = sys_log_logger_get_module_logger(__name__)

from scpi_sniffer       import DrvScpiHandlerC
from wattrex_driver_epc import DrvEpcDeviceC, DrvEpcDataC
from wattrex_driver_ea  import DrvEaDeviceC, DrvEaDataC
from wattrex_driver_rs  import DrvRsDeviceC, DrvRsDataC
from wattrex_driver_bk import DrvBkDeviceC, DrvBkDataC

#######################          MODULE IMPORTS          #######################

#######################          PROJECT IMPORTS         #######################
from ..mid_data import MidDataDeviceTypeE, MidDataDeviceC, MidDataPwrLimitE, \
                MidDataLinkConfSerialC
#######################              ENUMS               #######################
#######################             CLASSES              #######################
class MidDabsPwrMeterC:
    '''Instanciates an object enable to measure.
    '''
    def __init__(self, device: MidDataDeviceC) -> None:
        self.device_type = device.device_type
        self.bisource   : DrvEaDeviceC | None = None
        self.source     : DrvEaDeviceC | None = None
        self.load       : DrvRsDeviceC | None = None
        self.epc        : DrvEpcDeviceC| None = None
        self.meter      : DrvBkDeviceC | None = None
        link_conf = device.link_conf.__dict__
        if isinstance(device.link_conf, MidDataLinkConfSerialC):
            if link_conf['separator']=='\\n':
                link_conf['separator'] = '\n'
        try:
            if self.device_type is MidDataDeviceTypeE.EPC:
                self.epc : DrvEpcDeviceC = DrvEpcDeviceC(dev_id=int(link_conf['can_id']))
                self.epc.open()
            elif self.device_type is MidDataDeviceTypeE.SOURCE:
                # TODO: Update SCPI not needing handler
                self.source : DrvEaDeviceC = DrvEaDeviceC(DrvScpiHandlerC(**link_conf))
            elif self.device_type is MidDataDeviceTypeE.LOAD:
                self.load : DrvRsDeviceC = DrvRsDeviceC(DrvScpiHandlerC(**link_conf))
            elif self.device_type is MidDataDeviceTypeE.BISOURCE:
                self.bisource : DrvEaDeviceC = DrvEaDeviceC(DrvScpiHandlerC(**link_conf))
            elif self.device_type is MidDataDeviceTypeE.METER:
                self.meter : DrvBkDeviceC = DrvBkDeviceC(DrvScpiHandlerC(**link_conf))
            else:
                log.error("The dessire device doesn't have values in yaml file")
        except Exception as error:
            log.error(error)
            raise error

    def update(self) -> DrvEpcDataC | DrvEaDataC | DrvRsDataC | DrvBkDataC:
        """Update the data from the hardware sendind the corresponding messages.
        """
        res = None
        if self.device_type is MidDataDeviceTypeE.BISOURCE:
            res: DrvEaDataC = self.bisource.get_data()
        elif self.device_type is MidDataDeviceTypeE.SOURCE:
            res: DrvEaDataC = self.source.get_data()
        elif self.device_type is MidDataDeviceTypeE.LOAD:
            res: DrvRsDataC = self.load.get_data()
        elif self.device_type is MidDataDeviceTypeE.METER:
            res: DrvBkDataC = self.meter.get_data()
        elif self.device_type is MidDataDeviceTypeE.EPC:
            res: DrvEpcDataC  = self.epc.get_data(update=True)
        return res

class MidDabsPwrDevC(MidDabsPwrMeterC):
    """Instanciates an object enable to control the devices.
    """
    def _init__(self, device: MidDataDeviceC, )->None:
        super().__init__(device)

    def set_cv_mode(self,volt_ref: int, current_limit: int):
        """Set the CV mode with the given voltage and current limit.
        Args:
            volt_ref (int): [voltage in mV]
            current_limit (int): [current in mA]
        """
        try:
            if self.device_type is MidDataDeviceTypeE.BISOURCE:
                self.bisource.set_cv_mode(volt_ref, current_limit)
            elif self.device_type is MidDataDeviceTypeE.SOURCE:
                self.source.set_cv_mode(volt_ref, current_limit)
            elif self.device_type == MidDataDeviceTypeE.LOAD:
                # TODO: upgrade DrvRs to write limits when setting modes
                self.load.set_cv_mode(volt_ref)
            else:
                log.error("The device is not able to change between modes.")
                raise ValueError("The device is not able to change between modes")
        except Exception as err:
            log.error(f"Error while setting cv mode: {err}")
            raise Exception("Error while setting cv mode") from err #pylint: disable= broad-exception-raised

    def set_cc_mode(self, current_ref: int, volt_limit: int) -> None:
        """Set the CC mode with the given current and voltage limit.
        Args:
            current_ref (int): [current in mA]
            volt_limit (int): [voltage in mV]
        """
        try:
            if self.device_type is MidDataDeviceTypeE.BISOURCE:
                self.bisource.set_cc_mode(current_ref, volt_limit)
            elif self.device_type is MidDataDeviceTypeE.SOURCE:
                self.source.set_cc_mode(current_ref, volt_limit)
            elif self.device_type is MidDataDeviceTypeE.LOAD:
                # TODO: upgrade DrvRs to write limits when setting modes
                self.load.set_cc_mode(current_ref)
            else:
                log.error("The device is not able to change between modes.")
                raise ValueError("The device is not able to change between modes")
        except Exception as err:
            log.error(f"Error while setting cc mode: {err}")
            raise Exception("Error while setting cc mode") from err #pylint: disable= broad-exception-raised

    def disable(self) -> None:
        """Disable the devices.
        """
        try:
            if self.device_type is MidDataDeviceTypeE.BISOURCE:
                self.bisource.disable()
            elif self.device_type is MidDataDeviceTypeE.SOURCE:
                self.source.disable()
            elif self.device_type is MidDataDeviceTypeE.LOAD:
                self.load.disable()
            else:
                log.error("The device can not be disable")
                raise ValueError("The device can not be disable")
        except Exception as err:
            log.error(f"Error while disabling device: {err}")
            raise Exception("Error while disabling device") from err #pylint: disable= broad-exception-raised

    def close(self):
        """Close connection in serial with the device"""
        try:
            if self.device_type is MidDataDeviceTypeE.BISOURCE:
                self.bisource.close()
            elif self.device_type is MidDataDeviceTypeE.SOURCE:
                self.source.close()
            elif self.device_type is MidDataDeviceTypeE.LOAD:
                self.load.close()
            else:
                log.error("The device can not be disable")
                raise ValueError("The device can not be disable")
        except Exception as err:
            log.error(f"Error while closing device: {err}")
            raise Exception("Error while closing device") from err #pylint: disable= broad-exception-raised

class MidDabsEpcDevC(MidDabsPwrMeterC):
    """Class method for class - method that returns a class class for MIDDabsPwrC .
    """
    def _init__(self, device: MidDataDeviceC)->None:
        if device.device_type is MidDataDeviceTypeE.EPC:
            log.error((("Trying to instanciate a epc device but "
                             f"receive type {device.device_type.name}")))
            raise ValueError(("Trying to instanciate a epc device but "
                             f"receive type {device.device_type.name}"))
        super().__init__(device)

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
            raise Exception("Error while setting cc mode") from err #pylint: disable= broad-exception-raised
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
            raise Exception("Error while setting cv mode") from err #pylint: disable= broad-exception-raised
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
            raise Exception("Error while setting cp mode") from err #pylint: disable= broad-exception-raised

    def set_wait_mode(self, limit_type: MidDataPwrLimitE, limit_ref):
        """Set the wait mode of the ECP to be used in the ECP .

        Args:
            limit_type (MidDataPwrLimitE): [description]
            limit_ref ([type]): [description]

        Raises:
            Exception: [description]
        """
        try:
            self.epc.set_wait_mode(limit_type, limit_ref)
        except Exception as err:
            log.error(f"Error while setting wait mode: {err}")
            raise Exception("Error while setting wait mode") from err #pylint: disable= broad-exception-raised
    def set_limits(self, ls_volt: tuple | None = None, ls_curr: tuple | None = None,
                   ls_pwr: tuple | None = None, hs_volt: tuple | None = None,
                   temp: tuple | None = None) -> None:
        """Set the limits of the ECP.

        Args:
            ls_volt (tuple, optional): [max_value, min_value]. Defaults to None.
            ls_curr (tuple, optional): [max_value, min_value]. Defaults to None.
            ls_pwr (tuple, optional): [max_value, min_value]. Defaults to None.
            hs_volt (tuple, optional): [max_value, min_value]. Defaults to None.
            temp (tuple, optional): [max_value, min_value]. Defaults to None.

        Raises:
            Exception: [description]
            Exception: [description]
            Exception: [description]
            Exception: [description]
            Exception: [description]
        """
        if isinstance(ls_curr, tuple):
            try:
                self.epc.set_ls_curr_limit(ls_curr[0], ls_curr[1])
            except Exception as err:
                log.error(f"Error while setting ls current limit: {err}")
                raise Exception("Error while setting wait mode") from err #pylint: disable= broad-exception-raised
        if isinstance(ls_volt, tuple):
            try:
                self.epc.set_ls_volt_limit(ls_volt[0], ls_volt[1])
            except Exception as err:
                log.error(f"Error while setting ls current limit: {err}")
                raise Exception("Error while setting wait mode") from err #pylint: disable= broad-exception-raised
        if isinstance(ls_pwr, tuple):
            try:
                self.epc.set_ls_pwr_limit(ls_pwr[0], ls_pwr[1])
            except Exception as err:
                log.error(f"Error while setting ls current limit: {err}")
                raise Exception("Error while setting wait mode") from err #pylint: disable= broad-exception-raised
        if isinstance(hs_volt, tuple):
            try:
                self.epc.set_hs_volt_limit(hs_volt[0], hs_volt[1])
            except Exception as err:
                log.error(f"Error while setting ls current limit: {err}")
                raise Exception("Error while setting wait mode") from err #pylint: disable= broad-exception-raised
        if isinstance(temp, tuple):
            try:
                self.epc.set_temp_limit(temp[0], temp[1])
            except Exception as err:
                log.error(f"Error while setting ls current limit: {err}")
                raise Exception("Error while setting wait mode") from err #pylint: disable= broad-exception-raised

    def disable(self):
        """Disable the EPC device.
        """
        try:
            self.epc.disable()
        except Exception as err:
            log.error(f"Error while disabling epc: {err}")
            raise Exception("Error while disabling epc") from err #pylint: disable= broad-exception-raised
    def close(self):
        """Close connection with epc not receiving more messages and not controlling it"""
        try:
            self.epc.close()
        except Exception as err:
            log.error(f"Error while closing epc: {err}")
            raise Exception("Error while closing epc") from err #pylint: disable= broad-exception-raised
