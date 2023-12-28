#!/bin/bash

DEVOPS_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" && pwd )
REPO_ROOT_DIR=$( cd "${DEVOPS_DIR}/../" && pwd)
CONFIG_DIR="${REPO_ROOT_DIR}/config"
ENV_FILE=".cred.env"
DOCKER_FOLDER=./
DOCKER_COMPOSE=docker-compose.yml
CYCLER_SRC_DIR="${REPO_ROOT_DIR}/code/cycler"
INT_RE='^[0-9]+$'
DOCKER_COMPOSE_ARGS="-f ${DEVOPS_DIR}/${DOCKER_FOLDER}/${DOCKER_COMPOSE} --env-file ${CONFIG_DIR}/${ENV_FILE}"

ARG1=$1
ARG2=$2
ARG3=$3

export USER_ID=$(id -u)
export GROUP_ID=$(id -g)

initial_deploy () {
    force_stop
    python3 -m pip install --upgrade can-sniffer
    python3 -m pip install --upgrade SCPI-sniffer
    python3 -m pip install --upgrade wattrex-cycler-cu-manager
    mkdir -p "${REPO_ROOT_DIR}/log"

    docker compose ${DOCKER_COMPOSE_ARGS} up cache_db db_sync -d

    check_sniffer "can"
    check_sniffer "scpi"
}

instance_new_cycler () {
    check_sniffer "can"
    check_sniffer "scpi"
    export CYCLER_TARGET=cycler_prod

    #docker compose ${DOCKER_COMPOSE_ARGS} build --build-arg UPDATE_REQS=$(date +%s) cycler
    docker compose ${DOCKER_COMPOSE_ARGS} run -d -e CSID=${1} --name wattrex_cycler_node_${1} cycler
}

test_cycler () {
    export CYCLER_TARGET=cycler_test
    cp ${CYCLER_SRC_DIR}/tests/log_config_${ARG3}.yaml ${DEVOPS_DIR}/cycler/log_config.yaml
    cp ${CYCLER_SRC_DIR}/tests/test_${ARG3}.py ${CYCLER_SRC_DIR}/tests/test_cycler.py
    docker compose ${DOCKER_COMPOSE_ARGS} build --build-arg UPDATE_REQS=$(date +%s) cycler
    docker compose ${DOCKER_COMPOSE_ARGS} run --rm -e CSID=${1} --name wattrex_cycler_node_test_${1} cycler pytest -s /cycler/code/cycler/tests/test_cycler.py
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
        systemctl --user status can_sniffer.service > /dev/null
        if ! [[ $? -eq 0 ]]; then
            echo "Setting up can sniffer"
            systemctl --user set-environment SRC_PATH=${DEVOPS_DIR}
            systemctl --user set-environment CONFIG_FILE_PATH=${CONFIG_DIR}/config_params.yaml
            systemctl --user enable ${DEVOPS_DIR}/can/can_sniffer.service
            systemctl --user start can_sniffer.service
        else
            echo "Can sniffer is working"
        fi
    fi

    if [[ ${ARG2} = "scpi" ]] || [[ ${1} = "scpi" ]]; then
        systemctl --user status scpi_sniffer.service > /dev/null
        if ! [[ $? -eq 0 ]]; then
            echo "Setting up scpi sniffer"
            systemctl --user set-environment SRC_PATH=${DEVOPS_DIR}
            systemctl --user set-environment CONFIG_FILE_PATH=${CONFIG_DIR}/config_params.yaml
            systemctl --user enable ${DEVOPS_DIR}/scpi/scpi_sniffer.service
            systemctl --user start scpi_sniffer.service
        else
            echo "Scpi sniffer is working"
        fi
    fi
}

stop_sniffer () {
    if [[ ${ARG2} = "can" ]] || [[ ${1} = "can" ]]; then
        systemctl --user stop can_sniffer.service &> /dev/null
        systemctl --user disable can_sniffer.service &> /dev/null
    fi

    if [[ ${ARG2} = "scpi" ]] || [[ ${1} = "scpi" ]]; then
        systemctl --user stop scpi_sniffer.service &> /dev/null
        systemctl --user disable scpi_sniffer.service &> /dev/null
    fi
}

force_stop () {
    docker compose ${DOCKER_COMPOSE_ARGS} down

    stop_sniffer "can"
    stop_sniffer "scpi"

    rm -f /dev/mqueue/*
}


# MAIN
if ! [ -f "${CONFIG_DIR}/${ENV_FILE}" ]; then
    >&2 echo "[ERROR] .cred.env file not found"
    exit 2
fi

if ! [ -d "${DEVOPS_DIR}/${DOCKER_FOLDER}" ]; then
    >&2 echo "[ERROR] ${DEVOPS_DIR}/${DOCKER_FOLDER} folder not found"
    exit 2
else
    if ! [ -f "${DEVOPS_DIR}/${DOCKER_FOLDER}/${DOCKER_COMPOSE}" ]; then
        >&2 echo "[ERROR] ${DEVOPS_DIR}/${DOCKER_FOLDER}/${DOCKER_COMPOSE} file not found"
        exit 2
    fi
fi

# Check if the required files are present.
required_file_list=("${DEVOPS_DIR}/docker-compose.yml"
                    "${DEVOPS_DIR}/cache_db/createCacheCyclerTables.sql"
                    "${CONFIG_DIR}/.cred.env"
                    "${CONFIG_DIR}/.cred.yaml"
                    "${CONFIG_DIR}/config_params.yaml"
                    "${CONFIG_DIR}/scpi/log_config.yaml"
                    "${CONFIG_DIR}/cycler/log_config.yaml"
                    "${CONFIG_DIR}/cu_manager/log_config.yaml"
                    "${CONFIG_DIR}/can/log_config.yaml"
                    "${CONFIG_DIR}/db_sync/log_config.yaml" )

for file_path in ${required_file_list}
do
    if [ ! -f ${file_path} ]; then
        echo "${file_path} not found"
        exit 1
    fi
done

case ${ARG1} in
    "")
        # echo "Initial Deploy"
        export CYCLER_TARGET=db_sync_prod
        docker compose ${DOCKER_COMPOSE_ARGS} pull db_sync
        docker compose ${DOCKER_COMPOSE_ARGS} pull cycler
        initial_deploy
        ;;
    "build")
        # echo "Initial Deploy"
        export CYCLER_TARGET=db_sync_local
        docker compose ${DOCKER_COMPOSE_ARGS} build --build-arg UPDATE_REQS=$(date +%s) db_sync
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
            # echo "Sniffer ${2}"
            check_sniffer "${ARG2}"
        else
            >&2 echo "[ERROR] Invalid sniffer"
            exit 3
        fi
        ;;
    "stop-sniffer")
        # echo "Stop Sniffer"
        if [[ "${ARG2}" = "can" ]] || [[ "${ARG2}" = "scpi" ]]; then
            # echo "Sniffer ${2}"
            stop_sniffer "${ARG2}"
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
