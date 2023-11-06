# Configure and deploy CAN_SNIFFER
First of all, `cd` to the folder where this README is stored (?/Battery-Cyclers-Controller/devops/can). After that, the following commands have to be executed in order:

```
sudo systemctl set-environment R_PATH=$(pwd)
```

```
sudo systemctl enable /home/user/Battery-Cyclers-Controller/devops/can/can_sniffer.service
```

The following command is used to start the service's execution
```
sudo systemctl start can_sniffer.service
```

The following command is used to stop the service's execution
```
sudo systemctl stop can_sniffer.service
```

To disable the service and avoid to be executed at reboot or with start command, execute the following command:
```
sudo systemctl disable can_sniffer.service
```

Useful command to track service working process
```
journalctl --since "1 min ago" -f -xeu can_sniffer.service
```