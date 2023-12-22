# Proceso para realizar el análisis de tiempo:

1. **Clonar el repositorio de Battery Cycler Controller**
2. **Instalar todos los paquetes de Python necesarios.**
3. **Instalar el paquete `system-shared-tool-rt`.**
4. **Tener un archivo denominado `config_gpio.yaml`.**
5. **El archivo debe tener el modo que se va a usar para los GPIOs.**
6. **También debe tener los nombres que se han definido para los nodos junto con el número de GPIO.**
7. **La ubicación del archivo se designará en la variable `DEFAULT_GPIO_CONFIG_PATH` en el archivo `config_params.yaml` en la sección `system_shared_tool`.**
8. <span style="color:red">**IMPORTANTE: Se deben ejecutar los códigos manualmente, sin contenedores que instalen localmente los paquetes, en ventanas/screens distintas.**</span>
9. **Para ejecutar localmente, debes estar dentro del repositorio y ejecutar los siguientes comandos de forma ordenada:**

   9.1. `cd ubicación/del/repositorio`

   9.2. `export CONFIG_FILE_PATH=ubicación/al/config_params.yaml`

   9.3. `./devop/deploy.sh`  *(Para lanzar la base de datos cache)*

   9.4. `python3 /devops/can/can_node.py`

   9.5. `python3 /devops/scpi/scpi_node.py`

   9.6. `python3 /devops/cu_manager/run_cu_node.py`

   9.7. `python3 /devops/db_sync/run_db_node.py`

   9.8. `export CSID=numero_de_cycler_station_deseada`

   9.9. `python3 /devops/cycler/run_cycler.py`

## Esto es un ejemplo del fichero config_gpio.yaml
```
GPIO_BOARD      : 'BOARD'
MANAGER         : 11
STR             : 13
MEAS            : 15
cu_manager_node : 16
SYNC            : 18

# List of ports available en BOARD
# 11,13,15,16,18,22,29,31,36,37
# List of ports available en BCM
# 17,27,22,23,24,25,5,6,16,26
```