# Configure and deploy CAN_SNIFFER
First of all, `cd` to the folder where this README is stored (?/Battery-Cyclers-Controller/devops/can). After that, the following commands have to be executed in order:

```
systemctl --user set-environment SRC_PATH=$(pwd)
```

```
systemctl --user enable /home/user/Battery-Cyclers-Controller/devops/can/can_sniffer.service
```

The following command is used to start the service's execution
```
systemctl --user start can_sniffer.service
```

The following command is used to stop the service's execution
```
systemctl --user stop can_sniffer.service
```

To disable the service and avoid to be executed at reboot or with start command, execute the following command:
```
systemctl --user disable can_sniffer.service
```

Useful command to track service working process
```
journalctl --user --since "1 min ago" -f -xeu can_sniffer.service
```

Useful command to check service status
```
systemctl --user status can_sniffer.service
```