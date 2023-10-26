#!/usr/bin/python3
"""
This file contains the definition of the MID STR mapping between the objects attributes and
the database columns.
"""
#######################        MANDATORY IMPORTS         #######################
from __future__ import annotations

#######################         GENERIC IMPORTS          #######################
from typing import Dict

#######################       THIRD PARTY IMPORTS        #######################
#######################    SYSTEM ABSTRACTION IMPORTS    #######################
from system_logger_tool import sys_log_logger_get_module_logger
log = sys_log_logger_get_module_logger(__name__)
#######################       LOGGER CONFIGURATION       #######################
#######################          MODULE IMPORTS          #######################
#######################          PROJECT IMPORTS         #######################
#######################              ENUMS               #######################
mapping_gen_meas: Dict[str, str] = {
    "Voltage": 'voltage',
    "Current": 'current',
    "Power": 'power',
    "InstrID": 'instr_id',
}

mapping_experiment: Dict[str, str] = {
    'ExpID': "exp_id",
    "Name": 'name',
    "Status": 'status',
    'DateBegin': "date_begin",
    'DateFinish': "date_finish"
}

mapping_alarm: Dict[str, str] = {
    "Timestamp": 'timestamp',
    "Code": 'code',
    "Value": 'value',
}

mapping_status: Dict[str, str] = {
    'Status': "name",
    'ErrorCode': 'error_code',
    'DevID': 'dev_id'

}

mapping_cs_db: Dict[str, str] = {
    'Name': 'name',
    'CSID': 'cs_id',
    'Deprecated': 'deprecated'}

mapping_dev_db: Dict[str, str] = {
    'Manufacturer': 'manufacturer',
    'DeviceType': 'device_type',
    'LinkName': 'iface_name',
    'SN': 'serial_number'}

mapping_batt_db: Dict[str, str] = {
    'Name': 'name',
    'Model': 'model'}

mapping_instr_db: Dict[str, str] = {
    'InstrID': 'instr_id',
    'Mode': 'mode',
    'SetPoint': 'ref',
    'LimitType': 'limit_type',
    'LimitPoint': 'limit_ref'}

mapping_instr_modes: Dict[str, int] = {
    'WAIT'      : 0,
    'CV_MODE'   : 1,
    'CC_MODE'   : 2,
    'CP_MODE'   : 3}

mapping_instr_limit_modes: Dict[str, int] = {
    'TIME'      : 0,
    'VOLTAGE'   : 1,
    'CURRENT'   : 2,
    'POWER'   : 3}

#######################             CLASSES              #######################
# def remapping_dict(data: dict, mapping: dict) -> dict:
#     """Change the key names of the data dictionary with the names of the mapping dictionary.
#     Args:
#         data (dict): [description]
#         mapping (dict): [description]

#     Returns:
#         dict: [description]
#     """
#     log.debug(f"Remapping data {data} with mapping keys: {mapping}")
#     aux = {n_key:data[key] for key, n_key in zip(data.keys(), mapping.keys())}
#     log.debug(f"Returning: {aux}")
#     return {n_key:data[key] for key, n_key in zip(data.keys(), mapping.keys())}
