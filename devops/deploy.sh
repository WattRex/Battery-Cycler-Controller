#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ENV_FILE=.cred.env
DOCKER_FOLDER=docker
DOCKER_COMPOSE=docker-compose.yml
CYCLER_DOCKERFILE=Dockerfile.cycler
DB_SYNC_DOCKERFILE=Dockerfile.db_sync
INT_RE='^[0-9]+$'

ARG1=$1
ARG2=$2

initial_deploy () {
    force-stop
    sudo python3 -m pip install can-sniffer
    # python3 -m pip install scpi-sniffer
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

test_cycler () {
    docker compose -f ${SCRIPT_DIR}/${DOCKER_FOLDER}/${DOCKER_COMPOSE} --env-file ${SCRIPT_DIR}/${ENV_FILE} run --rm -e CSID=${1} --name wattrex_cycler_node_test_${1} cycler pytest /cycler/code/cycler/tests/tests_cycler.py -s
    exit $?
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
    if [[ ${ARG2} = "can" ]] || [[ ${1} = "can" ]]; then
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

    if [[ ${ARG2} = "scpi" ]] || [[ ${1} = "scpi" ]]; then
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
    sudo systemctl disable can_sniffer.service
    # sudo systemctl disable scpi_sniffer.service
}


# MAIN
if ! [ -f "${SCRIPT_DIR}/${ENV_FILE}" ]; then
    >&2 echo "[ERROR] .cred.env file not found"
    exit 2
fi

if ! [ -d "${SCRIPT_DIR}/${DOCKER_FOLDER}" ]; then
    >&2 echo "[ERROR] ${SCRIPT_DIR}/${DOCKER_FOLDER} folder not found"
    exit 2
else
    if ! [ -f "${SCRIPT_DIR}/${DOCKER_FOLDER}/${DOCKER_COMPOSE}" ]; then
        >&2 echo "[ERROR] ${SCRIPT_DIR}/${DOCKER_FOLDER}/${DOCKER_COMPOSE} file not found"
        exit 2
    fi
fi

case ${ARG1} in
    "")
        # echo "Initial Deploy"
        initial_deploy
        ;;
    "cycler")
        if [[ ${ARG2} =~ $INT_RE ]]; then
            # echo "Cycler ${2}"
            instance_new_cycler "${ARG2}"
        else
            >&2 echo "[ERROR] Invalid Cycler Station ID"
            exit 3
        fi
        ;;
    "sniffer")
        # echo "Check Sniffer"
        if [[ "${ARG2}" = "can" ]] || [[ "${ARG2}" = "scpi" ]]; then
            # echo "Cycler ${2}"
            check_sniffer "${ARG2}"
        else
            >&2 echo "[ERROR] Invalid sniffer"
            exit 3
        fi 
        ;;
    "stop-cycler")
        # echo "Stop cycler ${ARG2}"
        if [[ ${ARG2} =~ $INT_RE ]]; then
            # echo "Cycler ${2}"
            stop_active_cycler "${ARG2}"
        else
            >&2 echo "[ERROR] Invalid Cycler Station ID"
            exit 3
        fi
        ;;
    "force-stop")
        # echo "Stop all"
        force_stop
        ;;
    "test")
        if [[ ${ARG2} =~ $INT_RE ]]; then
            # echo "Cycler ${2}"
            test_cycler "${ARG2}"
        else
            >&2 echo "[ERROR] Invalid Cycler Station ID"
            exit 3
        fi
        ;;
    *)
        >&2 echo "[ERROR] Invalid command type: ${ARG1}"
        exit 3
        ;;
esac