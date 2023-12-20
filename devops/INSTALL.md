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

2. Execute deploy script to deploy containers for db synchronizer and CAN and SCPI sniffers
```bash
./devops/deploy.sh
```

NOTE: **make sure that all files in the `devops` and `config` folders belong to**
**the wattrex group and have write permissions**

3. Export config file path
```bash
export CONFIG_FILE_PATH=$(pwd)/config/config_params.yaml
```