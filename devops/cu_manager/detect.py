#!/usr/bin/python3
"""
Cu Manager
"""
#######################        MANDATORY IMPORTS         #######################

#######################         GENERIC IMPORTS          #######################
from typing import List

#######################       THIRD PARTY IMPORTS        #######################

#######################    SYSTEM ABSTRACTION IMPORTS    #######################
from system_logger_tool import sys_log_logger_get_module_logger, SysLogLoggerC, Logger

#######################       LOGGER CONFIGURATION       #######################
if __name__ == '__main__':
    cycler_logger = SysLogLoggerC(file_log_levels='./log_config.yaml')
log: Logger = sys_log_logger_get_module_logger(__name__)

#######################          MODULE IMPORTS          #######################

#######################          PROJECT IMPORTS         #######################
from comm_data import CommDataDeviceC

#######################              ENUMS               #######################

#######################             CLASSES              #######################

    def detect_devices() -> List[CommDataDeviceC]:
        '''Detect the devices that are currently connected to the device.

        Returns:
            List[MidDataDeviceC]: List of devices connected to the device that are detected and
            which type has been previously defined.
        '''

        # TODO: implement this
        test_detected_device = CommDataDeviceC(dev_id=1,
                                                            manufacturer='test',
                                                            model='test',
                                                            serial_number='test',
                                                            device_type=MidDataDeviceTypeE.EPC,
                                                            iface_name='test',
                                                            mapping_names={'test':'test'},
                                                            link_configuration=MidDataLinkConfC(
                                                                baudrate=9600,
                                                                parity='N',
                                                                stopbits=1,
                                                                bytesize=8,
                                                                timeout=0.1,
                                                                write_timeout=0.1,
                                                                inter_byte_timeout=0.1,
                                                                separator='\n'))
        return [test_detected_device]
