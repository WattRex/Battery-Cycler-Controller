# INSTALL

1. Create a wattrex user to execute cyclers and change password
```bash

su -
# Create user, group and change password
groupadd -g 69976 wattrex
useradd -u 69976 -g wattrex wattrex
mkhomedir_helper wattrex
passwd wattrex

# Add new user to docker group
usermod -aG docker wattrex
exit

# Login to new user
su - wattrex
```
2. Change system queue sizes. For this, follow this [guide](https://github.com/WattRex/System-Tools/tree/develop/code/sys_shd)
3. Execute deploy script to deploy containers for db synchronizer and CAN and SCPI sniffers
```bash
./devops/deploy.sh
```

NOTE: **make sure that all files in the `devops` and `config` folders belong to**
**the wattrex group and have write permissions**
2.1 If get a message like this: 
```
Failed to connect to bus: No medium found
```
You must execute these commands:
```bash
export XDG_RUNTIME_DIR="/run/user/$UID"
export DBUS_SESSION_BUS_ADDRESS="unix:path=${XDG_RUNTIME_DIR}/bus"
```
For further information, look up this [answer](https://askubuntu.com/questions/1374347/error-running-systemd-as-user-failed-to-connect-to-bus-dbus-session-bus-addr).

3. Export config file path
```bash
export CONFIG_FILE_PATH=$(pwd)/config/config_params.yaml
```
