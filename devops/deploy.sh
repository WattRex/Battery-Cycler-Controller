#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ENV_FILE=.cred.env
DOCKER_FOLDER=docker
DOCKER_COMPOSE=docker-compose.yml
CYCLER_DOCKERFILE=Dockerfile.cycler
DB_SYNC_DOCKERFILE=Dockerfile.db_sync
INT_RE='^[0-9]+$'

arg1=$1
arg2=$2

initial_deploy () {
    force-stop
    sudo sh -c 'echo 250 > /proc/sys/fs/mqueue/msg_max'
    docker compose -f ${SCRIPT_DIR}/${DOCKER_FOLDER}/${DOCKER_COMPOSE} --env-file ${SCRIPT_DIR}/${ENV_FILE} up cache_db db_sync -d
    
    check_sniffer "can"
    # check_sniffer "scpi"
}

instance_new_cycler () {
    check_sniffer "can"
    # check_sniffer "scpi"
    docker compose -f ${SCRIPT_DIR}/${DOCKER_FOLDER}/${DOCKER_COMPOSE} --env-file ${SCRIPT_DIR}/${ENV_FILE} run -d -e CSID=${1} --name wattrex_cycler_node_${1} cycler
}

stop_active_cycler () {
    echo "Stopping container..."
    docker stop wattrex_cycler_node_${1}
    if [[ $? -eq 0 ]]; then
        echo "Removing residual container..."
        docker container rm wattrex_cycler_node_${1}
    fi
}

check_sniffer () {
    if [[ ${arg2} = "can" ]] || [[ ${1} = "can" ]]; then
        service can_sniffer status > /dev/null
        if ! [[ $? -eq 0 ]]; then
            echo "Setting up can sniffer"
            sudo systemctl set-environment R_PATH=${SCRIPT_DIR}/can
            sudo systemctl enable ${SCRIPT_DIR}/can/can_sniffer.service
            sudo systemctl start can_sniffer.service
        else
            echo "Can sniffer is working"
        fi
    fi

    if [[ ${arg2} = "scpi" ]] || [[ ${1} = "scpi" ]]; then
        service scpi_sniffer status > /dev/null
        if ! [[ $? -eq 0 ]]; then
            echo "Setting up scpi sniffer"
            sudo systemctl set-environment R_PATH=${SCRIPT_DIR}/scpi
            sudo systemctl enable ${SCRIPT_DIR}/scpi/scpi_sniffer.service
            sudo systemctl start scpi_sniffer.service
        else
            echo "Scpi sniffer is working"
        fi
    fi
}

force_stop () {
    docker compose -f ${SCRIPT_DIR}/${DOCKER_FOLDER}/${DOCKER_COMPOSE} --env-file ${SCRIPT_DIR}/${ENV_FILE} down
    sudo systemctl stop can_sniffer.service
    # sudo systemctl stop scpi_sniffer.service
}


# MAIN
if ! [ -f "${SCRIPT_DIR}/${ENV_FILE}" ]; then
    echo "[ERROR] .cred.env file not found"
    exit 2
fi

if ! [ -d "${SCRIPT_DIR}/${DOCKER_FOLDER}" ]; then
    echo "[ERROR] ${SCRIPT_DIR}/${DOCKER_FOLDER} folder not found"
    exit 2
else
    if ! [ -f "${SCRIPT_DIR}/${DOCKER_FOLDER}/${DOCKER_COMPOSE}" ]; then
        echo "[ERROR] ${SCRIPT_DIR}/${DOCKER_FOLDER}/${DOCKER_COMPOSE} file not found"
        exit 2
    fi
fi

case ${arg1} in
    "")
        # echo "Initial Deploy"
        initial_deploy
        ;;
    "cycler")
        if [[ ${arg2} =~ $INT_RE ]]; then
            # echo "Cycler ${2}"
            instance_new_cycler "${arg2}"
        else
            echo "[ERROR] Invalid Cycler Station ID"
        fi
        ;;
    "sniffer")
        # echo "Check Sniffer"
        if [[ "${arg2}" = "can" ]] || [[ "${arg2}" = "scpi" ]]; then
            # echo "Cycler ${2}"
            check_sniffer "${arg2}"
        else
            echo "[ERROR] Invalid sniffer"
        fi 
        ;;
    "stop-cycler")
        # echo "Stop cycler ${arg2}"
        if [[ ${arg2} =~ $INT_RE ]]; then
            # echo "Cycler ${2}"
            stop_active_cycler "${arg2}"
        else
            echo "[ERROR] Invalid Cycler Station ID"
        fi
        ;;
    "force-stop")
        # echo "Stop all"
        force_stop
        ;;
    *)
        echo "[ERROR] Invalid command type: ${arg1}"
        exit 3
        ;;
esac