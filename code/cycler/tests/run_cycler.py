#!/usr/bin/python3
from os import getenv
from time import sleep

print("Cycler ID: " + getenv('CSID'))
while 1:
    print("Ha pasado 1 minuto desde que pasó el último")
    sleep(60)
