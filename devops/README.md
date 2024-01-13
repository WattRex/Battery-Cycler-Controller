# Deploy.sh

## Description
This script is used to deploy the cache database, the database syncronizer and the SCPI and CAN sniffer services. In addition, it will also allow to deploy battery cycler instances.

## Requirements
This script requires the following software to be installed:
- sudo
- systemctl
- docker
- docker-compose
- python3
- python3-pip

## Usage
Before launching, is mandatory to change the queue length and message length:
```
sudo sh -c 'echo 400 > /proc/sys/fs/mqueue/msg_max'
sudo sh -c 'echo 400 > /proc/sys/fs/mqueue/msgsize_max'
```
First of all, you need to launch the script with the following command. This command will launch and start up the cache database, the database syncronizer and the SCPI and CAN sniffer services.
```
./deploy.sh
```
To launch CU MANAGER node, inside the folder of the repository:
```
export CONFIG_FILE_PATH=config/config_params.yaml
pip install wattrex-battery-cycler-cu-manager
python3 /devops/cu_manager/run_cu_node.py
```
To deploy a battery cycler instance, you need to launch the script with the following command changing the _<cycler_station_id>_ with the id of the station you want to deploy:
```
./deploy.sh cycler <cycler_station_id>
```

To check if the sniffer is working properly, and relaunch it if it was deactivated or in error state, you can use the following command changing the _<scpi|can>_ with the protocol you want to check (scpi or can):
```
./deploy.sh sniffer <scpi|can>
```

To stop any cycler, use the following command changing the _<cycler_station_id>_ with the id of the station you want to stop:
```
./deploy.sh stop-cycler <cycler_station_id>
```

To stop all system services configurated by the deploy.sh script, use the following command:
```
./deploy force-stop
```
___
___

# Self-Hosted Runner
Once the self-hosted runner has been properly configurated, it can be deployed as a system service. To do that, the following commands are useful:
## [Commands to manage self-hosted runner working as a service](https://docs.github.com/en/actions/hosting-your-own-runners/managing-self-hosted-runners/configuring-the-self-hosted-runner-application-as-a-service)
Inside the actions-runner folder:
### Install runner as service
```
sudo ./svc.sh install
```
### Install runner as service
```
sudo ./svc.sh start
```
### Checking the status of the service
```
sudo ./svc.sh status
```
### Stopping the service
```
sudo ./svc.sh stop
```
### Uninstalling the service
```
sudo ./svc.sh uninstall
```
