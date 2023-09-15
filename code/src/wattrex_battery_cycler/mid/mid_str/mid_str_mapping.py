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
#######################       LOGGER CONFIGURATION       #######################
#######################          MODULE IMPORTS          #######################
#######################          PROJECT IMPORTS         #######################
#######################              ENUMS               #######################
mapping_gen_meas: Dict[str, str] = {
    "voltage": 'Voltage',
    "current": 'Current',
    "power": 'Power',
    "pwr_mode": 'PwrMode',
}

# mapping_experiment: Dict[str, str] = {
#     "exp_id": 'ExpID',
#     "name": 'Name',
#     "status": 'Status',
#     "date_begin": 'DateBegin',
#     "date_finish": 'DateFinish'
# }

mapping_alarm: Dict[str, str] = {
    "timestamp": 'Timestamp',
    "code": 'Code',
    "value": 'Value',
}

mapping_status: Dict[str, str] = {
    "exp_id": 'ExpID',
    "status": 'Status',
    "date": 'Date'
}

map_cs_db: Dict[str, str] = {
    'Name': 'name',
    'CSID': 'cycler_id'}
    # 'Deprecated': 'deprecated'}

map_dev_db: Dict[str, str] = {
    'Manufacturer': 'manufacturer',
    'DeviceType': 'device_type',
    'UdevName': 'iface_name',
    'SN': 'serial_number'}

map_batt_db: Dict[str, str] = {
    'Name': 'name',
    'Model': 'model'}

map_batt_range_db: Dict[str, str] = {
    'VoltMax': 'volt_max',
    'VoltMin': 'volt_min',
    'CurrMax': 'curr_max',
    'CurrMin': 'curr_min'}

map_profile_db: Dict[str, str] = {
    'Name': 'volt_max',
    'VoltMin': 'volt_min',
    'CurrMax': 'curr_max',
    'CurrMin': 'curr_min'}

map_inst_db: Dict[str, str] = {
    'InstrID': 'instr_id',
    'Mode': 'mode',
    'SetPoint': 'ref',
    'LimitType': 'limit_type',
    'LimitPoint': 'limit_ref'}

#######################             CLASSES              #######################
def remap_dict(data: dict, mapping: dict) -> dict:
    """Change the key names of the data dictionary with the names of the mapping dictionary.
    Args:
        data (dict): [description]
        mapping (dict): [description]

    Returns:
        dict: [description]
    """
    return {mapping[k]:data[k] for k in data}
