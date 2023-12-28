#!/usr/bin/python3
"""
Cu Manager
"""
#######################        MANDATORY IMPORTS         #######################

#######################         GENERIC IMPORTS          #######################
import sys, os
import threading
from signal import signal, SIGINT

#######################       THIRD PARTY IMPORTS        #######################

#######################    SYSTEM ABSTRACTION IMPORTS    #######################
from system_logger_tool import sys_log_logger_get_module_logger, SysLogLoggerC, Logger

#######################       LOGGER CONFIGURATION       #######################
if __name__ == '__main__':
    cycler_logger = SysLogLoggerC(file_log_levels='./config/cu_manager/log_config.yaml')
log: Logger = sys_log_logger_get_module_logger(__name__)

#######################          MODULE IMPORTS          #######################
#sys.path.append(os.path.dirname(__file__)+'/../../code')
# from cu_manager.src.wattrex_cycler_cu_manager import CuManagerNodeC
from wattrex_cycler_cu_manager import CuManagerNodeC

#######################          PROJECT IMPORTS         #######################

#######################              ENUMS               #######################

#######################             CLASSES              #######################

#######################            FUNCTIONS             #######################
cu_manager_node = None

def signal_handler(sig, frame) -> None: #pylint: disable= unused-argument
    """Called when the user presses Ctrl + C to stop test.

    Args:
        sig ([type]): [description]
        frame ([type]): [description]
    """
    if isinstance(cu_manager_node, CuManagerNodeC):
        log.critical(msg='You pressed Ctrl+C! Stopping test...')
        cu_manager_node.stop()
        sys.exit(0)

if __name__ == '__main__':
    working_flag_event : threading.Event = threading.Event()
    working_flag_event.set()
    cu_manager_node = CuManagerNodeC(working_flag=working_flag_event,
                                          cycle_period=1000,
                                          cu_id_file_path='./config/cu_manager/.cu_id')
    signal(SIGINT, signal_handler)
    cu_manager_node.run()
