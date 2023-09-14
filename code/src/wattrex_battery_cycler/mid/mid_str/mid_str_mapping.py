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
