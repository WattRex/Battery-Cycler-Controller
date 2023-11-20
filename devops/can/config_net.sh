#!/bin/bash

sudo sh -c 'echo 350 > /proc/sys/fs/mqueue/msg_max'
sudo sh -c 'echo 350 > /proc/sys/fs/mqueue/msgsize_max'
