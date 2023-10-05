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
First of all, you need to launch the script with the following command. This command will launch and start up the cache database, the database syncronizer and the SCPI and CAN sniffer services.
```
./deploy.sh
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