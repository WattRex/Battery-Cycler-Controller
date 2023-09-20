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
    docker compose -f ${SCRIPT_DIR}/${DOCKER_FOLDER}/${DOCKER_COMPOSE} --env-file ${SCRIPT_DIR}/${ENV_FILE} up cache_db db_sync -d
}

instance_new_cycler () {
    echo "a"
}

check_sniffer () {
    echo "a"
}

# echo "${SCRIPT_DIR}/${ENV_FILE}"

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
            instance_new_cycler
        else
            echo "[ERROR] Invalid Cycler Station ID"
        fi
        ;;
    "sniffer")
        # echo "Check Sniffer"
        if [[ "${arg2}" = "can" ]] || [[ "${arg2}" = "scpi" ]] || [[ "${arg2}" = "" ]]; then
            # echo "Cycler ${2}"
            check_sniffer "${arg2}"
        else
            echo "[ERROR] Invalid sniffer"
        fi 
        ;;
    "force-stop")
        # echo "Stop all"
        docker compose -f ${SCRIPT_DIR}/${DOCKER_FOLDER}/${DOCKER_COMPOSE} --env-file ${SCRIPT_DIR}/${ENV_FILE} down
        ;;
    *)
        echo "[ERROR] Invalid command type: ${arg1}"
        exit 3
        ;;
esac