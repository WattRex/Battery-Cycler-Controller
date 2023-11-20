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
MAPPING_GEN_MEAS: Dict[str, str] = {
    "Voltage": 'voltage',
    "Current": 'current',
    "Power": 'power',
    "InstrID": 'instr_id',
}

MAPPING_EXPERIMENT: Dict[str, str] = {
    'ExpID': "exp_id",
    "Name": 'name',
    "Status": 'status',
    'DateBegin': "date_begin",
    'DateFinish': "date_finish"
}

MAPPING_ALARM: Dict[str, str] = {
    "Timestamp": 'timestamp',
    "Code": 'code',
    "Value": 'value',
}

MAPPING_STATUS: Dict[str, str] = {
    'Status': "name",
    'ErrorCode': 'error_code',
    'DevID': 'dev_db_id'

}

MAPPING_CS_DB: Dict[str, str] = {
    'Name': 'name',
    'CSID': 'cs_id',
    'Deprecated': 'deprecated'}

MAPPING_DEV_DB: Dict[str, str] = {
    'DevID': 'dev_db_id',
    'Manufacturer': 'manufacturer',
    'DeviceType': 'device_type',
    'LinkName': 'iface_name',
    'SN': 'serial_number'}

MAPPING_BATT_DB: Dict[str, str] = {
    'Name': 'name',
    'Model': 'model'}

MAPPING_INSTR_DB: Dict[str, str] = {
    'InstrID': 'instr_id',
    'Mode': 'mode',
    'SetPoint': 'ref',
    'LimitType': 'limit_type',
    'LimitPoint': 'limit_ref'}

MAPPING_INSTR_MODES: Dict[str, int] = {
    'WAIT'      : 0,
    'CV_MODE'   : 1,
    'CC_MODE'   : 2,
    'CP_MODE'   : 3}

MAPPING_INSTR_LIMIT_MODES: Dict[str, int] = {
    'TIME'      : 0,
    'VOLTAGE'   : 1,
    'CURRENT'   : 2,
    'POWER'   : 3}
