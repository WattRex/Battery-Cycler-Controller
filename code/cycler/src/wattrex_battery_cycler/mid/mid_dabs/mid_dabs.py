#!/usr/bin/python3
"""
This module will create instances of epc device in order to control
the device and request info from it.
"""
#######################        MANDATORY IMPORTS         #######################
from __future__ import annotations
from typing import List, Dict
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
from wattrex_battery_cycler_datatypes.cycler_data import (CyclerDataDeviceTypeE, CyclerDataDeviceC,
                                CyclerDataPwrLimitE, CyclerDataDeviceStatusC, CyclerDataExtMeasC,
                                CyclerDataGenMeasC, CyclerDataAllStatusC)

#######################          PROJECT IMPORTS         #######################

#######################          MODULE IMPORTS          #######################

#######################              ENUMS               #######################

#######################             CLASSES              #######################
# TODO: SET PERIODIC TO RECEIVE ELECT AND TEMP MEASURES
class _ConstantsC:
    PERIOD_ELECT_MEAS   = 5 # value *10ms
    PERIOD_TEMP_MEAS    = 5 # value *10ms
class MidDabsPwrMeterC: #pylint: disable= too-many-instance-attributes
    '''Instanciates an object enable to measure.
    '''
    def __init__(self, device: list [CyclerDataDeviceC]) -> None:
        self.device_type = [x.device_type for x in device]
        self.dev_id: List = [x.dev_id for x in device]
        self.bisource   : DrvEaDeviceC | None = None
        self.source     : DrvEaDeviceC | None = None
        self.load       : DrvRsDeviceC | None = None
        self.epc        : DrvEpcDeviceC| None = None
        self.meter      : DrvBkDeviceC | None = None
        try:
            for dev in device:
                if dev.device_type is CyclerDataDeviceTypeE.EPC:
                    dev_id= 0
                    if isinstance(dev.iface_name, str):
                        dev_id = int(dev.iface_name,16)
                    else:
                        dev_id = int(dev.iface_name)
                    self.epc : DrvEpcDeviceC = DrvEpcDeviceC(dev_id=dev_id)
                    self.epc.open()
                    self.mapping_epc = dev.mapping_names
                    self.epc.set_periodic(ack_en = False,
                        elect_en = True, elect_period = _ConstantsC.PERIOD_ELECT_MEAS,
                        temp_en = True, temp_period = _ConstantsC.PERIOD_TEMP_MEAS)
                elif dev.device_type is CyclerDataDeviceTypeE.SOURCE:
                    link_conf = __prepare_link_conf(dev.link_conf.__dict__)
                    self.source : DrvEaDeviceC = DrvEaDeviceC(DrvScpiHandlerC(**link_conf))
                    self.mapping_source = dev.mapping_names
                elif dev.device_type is CyclerDataDeviceTypeE.LOAD:
                    # TODO: Update SCPI not needing handler
                    link_conf = __prepare_link_conf(dev.link_conf.__dict__)
                    self.load : DrvRsDeviceC = DrvRsDeviceC(DrvScpiHandlerC(**link_conf))
                    self.mapping_load = dev.mapping_names
                elif self.device_type is CyclerDataDeviceTypeE.BISOURCE:
                    link_conf = __prepare_link_conf(dev.link_conf.__dict__)
                    self.bisource : DrvEaDeviceC = DrvEaDeviceC(DrvScpiHandlerC(**link_conf))
                    self.mapping_bisource = dev.mapping_names
                elif self.device_type is CyclerDataDeviceTypeE.METER:
                    link_conf = __prepare_link_conf(dev.link_conf.__dict__)
                    self.meter : DrvBkDeviceC = DrvBkDeviceC(DrvScpiHandlerC(**link_conf))
                    self.mapping_meter = dev.mapping_names
                else:
                    log.error(f"The dessire device doesn't have type {self.device_type}")
        except Exception as error:
            log.error(error)
            raise error

    def __update_source_load_status(self, status: CyclerDataAllStatusC):
        if status.source.value > 0 :
            status.pwr_dev = status.source
        elif status.load.value > 0:
            status.pwr_dev = status.load
        elif status.source.value < 0:
            status.pwr_dev = status.source
        elif status.load.value < 0:
            status.pwr_dev = status.load
        else:
            status.pwr_dev = status.source

    def update(self, gen_meas: CyclerDataGenMeasC, ext_meas: CyclerDataExtMeasC,
               status: CyclerDataAllStatusC) -> None: #pylint: disable= too-many-branches
        """Update the data from the hardware sendind the corresponding messages.
        Update the variables of the class with the data received from the device.
        Depending on the device type, the data will be updated in a way or another.
        """
        res = None
        for dev_type, dev_id in zip(self.device_type, self.dev_id):
            if dev_type is CyclerDataDeviceTypeE.BISOURCE:
                res: DrvEaDataC = self.bisource.get_data()
                status.pwr_dev = CyclerDataDeviceStatusC(error= res.status.error_code,
                                                        dev_id= dev_id)
            elif dev_type is CyclerDataDeviceTypeE.SOURCE:
                res: DrvEaDataC = self.source.get_data()
                status.source = CyclerDataDeviceStatusC(error= res.status.error_code,
                                                dev_id= dev_id)
            elif dev_type is CyclerDataDeviceTypeE.LOAD:
                res: DrvRsDataC = self.load.get_data()
                status.load = CyclerDataDeviceStatusC(error= res.status.error_code,
                                                dev_id= dev_id)
            elif dev_type is CyclerDataDeviceTypeE.METER:
                res: DrvBkDataC = self.meter.get_data()
                res = res.__dict__
                for att_name in self.mapping_meter:
                    setattr(ext_meas,att_name, getattr(res, att_name))
            elif dev_type is CyclerDataDeviceTypeE.EPC:
                msg_elect_meas = self.epc.get_elec_meas(periodic_flag= True)
                msg_temp_meas = self.epc.get_temp_meas(periodic_flag= True)
                msg_mode: DrvEpcDataC  = self.epc.get_mode()
                epc_status = self.epc.get_status()
                status.pwr_dev = CyclerDataDeviceStatusC(error= epc_status.error_code,
                                                        dev_id= dev_id)
                gen_meas.voltage = msg_elect_meas.ls_voltage
                gen_meas.current = msg_elect_meas.ls_current
                gen_meas.power   = msg_elect_meas.ls_power
                status.pwr_mode = msg_mode.mode
                if self.mapping_epc is not None:
                    for key in self.mapping_epc.keys():
                        if key == 'hs_voltage':
                            setattr(ext_meas, self.mapping_epc[key],
                                    getattr(msg_elect_meas, key))
                        elif key == 'temp_body':
                            setattr(ext_meas, self.mapping_epc[key],
                                    getattr(msg_temp_meas, key))
                        elif key == 'temp_anod':
                            setattr(ext_meas, self.mapping_epc[key],
                                    getattr(msg_temp_meas, key))
                        elif key == 'temp_amb':
                            setattr(ext_meas, self.mapping_epc[key],
                                    getattr(msg_temp_meas, key))
        if (CyclerDataDeviceTypeE.SOURCE in self.device_type and
            CyclerDataDeviceTypeE.LOAD in self.device_type):
            self.__update_source_load_status(status= status)

    def close(self):
        """Close connection in serial with the device"""
        try:
            for dev in self.device_type:
                if dev is CyclerDataDeviceTypeE.BISOURCE:
                    self.bisource.close()
                elif dev is CyclerDataDeviceTypeE.SOURCE:
                    self.source.close()
                elif dev is CyclerDataDeviceTypeE.LOAD:
                    self.load.close()
                elif dev is CyclerDataDeviceTypeE.EPC:
                    self.epc.close()
                else:
                    log.error("The device can not be close")
                    raise ValueError("The device can not be close")
        except Exception as err:
            log.error(f"Error while closing device: {err}")
            raise Exception("Error while closing device") from err #pylint: disable= broad-exception-raised

class MidDabsPwrDevC(MidDabsPwrMeterC):
    """Instanciates an object enable to control the devices.
    """
    def _init__(self, device: List[CyclerDataDeviceC])->None:
        super().__init__(device)

    def set_cv_mode(self,volt_ref: int, limit_ref: int,
                    limit_type: CyclerDataPwrLimitE = None) -> None:
        """Set the CV mode with the given voltage and current limit.
        To set cv mode in epc must have argument limit_type
        Args:
            volt_ref (int): [voltage in mV]
            limit_ref (int): [limit reference, for the epc could be mA/dW/ms the rest of devices
                            is mA]
        """
        try:
            if CyclerDataDeviceTypeE.BISOURCE in self.device_type:
                self.bisource.set_cv_mode(volt_ref, limit_ref)
            elif (CyclerDataDeviceTypeE.SOURCE in self.device_type and
                CyclerDataDeviceTypeE.LOAD in self.device_type):
                if limit_ref>0:
                    self.load.disable()
                    self.source.set_cv_mode(volt_ref, limit_ref)
                else:
                    # TODO: upgrade DrvRs to write limits when setting modes
                    self.source.disable()
                    self.load.set_cv_mode(volt_ref)
            elif CyclerDataDeviceTypeE.EPC in self.device_type:
                self.epc.set_cv_mode(volt_ref,limit_type, limit_ref)
            else:
                log.error("The device is not able to change between modes.")
                raise ValueError("The device is not able to change between modes")
        except Exception as err:
            log.error(f"Error while setting cv mode: {err}")
            raise Exception("Error while setting cv mode") from err #pylint: disable= broad-exception-raised

    def set_cc_mode(self, current_ref: int, limit_ref: int,
                    limit_type: CyclerDataPwrLimitE = None) -> None:
        """Set the CC mode with the given current and voltage limit.
            To set cc mode in epc must have argument limit_type
        Args:
            current_ref (int): [current in mA]
            limit_ref (int): [limit reference, for the epc could be mV/dW/ms the rest of devices
                            is mV]
        """
        try:
            if CyclerDataDeviceTypeE.BISOURCE in self.device_type:
                self.bisource.set_cc_mode(current_ref, limit_ref)
            elif (CyclerDataDeviceTypeE.SOURCE in self.device_type and
                CyclerDataDeviceTypeE.LOAD in self.device_type):
                if current_ref>0:
                    self.load.disable()
                    self.source.set_cc_mode(current_ref, limit_ref)
                else:
                    # TODO: upgrade DrvRs to write limits when setting modes
                    self.source.disable()
                    self.load.set_cc_mode(current_ref)
            elif CyclerDataDeviceTypeE.EPC in self.device_type:
                log.warning("Setting cc mode in epc")
                self.epc.set_cc_mode(current_ref,limit_type, limit_ref)
            else:
                log.error("The device is not able to change between modes.")
                raise ValueError("The device is not able to change between modes")
        except Exception as err:
            log.error(f"Error while setting cc mode: {err}")
            raise Exception("Error while setting cc mode") from err #pylint: disable= broad-exception-raised

    def set_cp_mode(self, pwr_ref: int, limit_type: CyclerDataPwrLimitE, limit_ref: int) -> None:
        """Set the CP mode with the specified limits, only possible in the epc.

        Args:
            pwr_ref (int): [description]
            limit_type (CyclerDataPwrLimitE): [description]
            limit_ref (int): [description]
        """
        try:
            if CyclerDataDeviceTypeE.EPC in self.device_type:
                self.epc.set_cp_mode(pwr_ref, limit_type, limit_ref)
            else:
                log.error('This device is incompatible with power control mode')
        except Exception as err:
            log.error(f"Error while setting cp mode: {err}")
            raise Exception("Error while setting cp mode") from err #pylint: disable= broad-exception-raised

    def set_wait_mode(self, time_ref: int = 0):
        """Set the wait mode for the device.
        To set the wait mode in epc must write argument time_ref = number_in_ms
        """
        try:
            if CyclerDataDeviceTypeE.EPC in self.device_type:
                self.epc.set_wait_mode(limit_ref = time_ref)
            else:
                self.disable()
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
        """
        if CyclerDataDeviceTypeE.EPC in self.device_type:
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
        else:
            log.error("The limits can not be change in this device")

    def disable(self) -> None:
        """Disable the devices.
        """
        try:
            if CyclerDataDeviceTypeE.BISOURCE in self.device_type:
                self.bisource.disable()
            elif (CyclerDataDeviceTypeE.SOURCE in self.device_type and
                CyclerDataDeviceTypeE.LOAD in self.device_type):
                self.source.disable()
                self.load.disable()
            elif CyclerDataDeviceTypeE.EPC in self.device_type:
                log.info("Disabling epc")
                self.epc.disable()
            else:
                log.error("The device can not be disable")
                raise ValueError("The device can not be disable")
        except Exception as err:
            log.error(f"Error while disabling device: {err}")
            raise Exception("Error while disabling device") from err #pylint: disable= broad-exception-raised

def __prepare_link_conf(link_conf: dict) -> dict:
    """Convert link configuration types to correct ones.
    Args:
        link_conf (dict): [description]

    Returns:
        [dict]: [correct dictionary with the correct types]
    """
    map_link_conf: Dict[str, str] = {
                    'timeout' : 'float',
                    'write_timeout' : 'float',
                    'baudrate' : 'int',
                    'bytesize' : 'int',
                    'stopbits' : 'int',
                    'inter_byte_timeout' : 'float'
                }
    res = {}
    for key in link_conf.keys():
        if key in map_link_conf:
            res[key] = __convert_data(link_conf[key], map_link_conf[key])
        else:
            # Translation between parity specified by user and parity understable by python serial
            if key == 'parity':
                link_parity = link_conf[key].lower()
                if 'odd' in link_parity:
                    parity = 'O'
                elif 'even' in link_parity:
                    parity = 'E'
                elif 'none' in link_parity:
                    parity = 'N'
                elif 'mark' in link_parity:
                    parity = 'M'
                elif 'space' in link_parity:
                    parity = 'S'
                else:
                    log.error("Wrong value for parity")
                    raise ValueError("Wrong value for parity")
                res[key] = parity
            if  key == 'separator' and link_conf[key]=='\\n':
                res[key] = '\n'
            else:
                res[key] = link_conf[key]
    return res

def __convert_data(data:str, data_type: str):
    """Convert string data to float or int

    Args:
        data (str): [data to convert]
        data_type (str): [type to convert]

    Returns:
        [type]: [description]
    """
    res = None
    if data_type == 'int':
        res = int(data)
    elif data_type =='float':
        res = float(data)
    return res
