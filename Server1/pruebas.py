import math
import time
from datetime import datetime

aforo = 0
clientes_conectados = {}
hora_ultimo_mensaje = {}
id_disp_num_sec = {}

def contabilizar(id_dispositivo, numero_secuencia, presentacion_variacion):

    global aforo

    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    hora_ultimo_mensaje[id_dispositivo] = time.time()
    # print(f"{current_time} - {hora_ultimo_mensaje}")
    clientes_conectados[id_dispositivo] = "Activo"

    if presentacion_variacion == "presentacion":
        print(f"{current_time} - Conexión establecida con el cliente {id_dispositivo}")
        print(f"{current_time} - CLIENTES CONECTADOS: {clientes_conectados}")

    # Escribimos en el archivo el aforo y la hora a la que llega
    elif presentacion_variacion in ["incrementa", "decrementa", "nada"]:
        if presentacion_variacion == "incrementa":
            aforo += 1
        elif presentacion_variacion == "decrementa" and aforo > 0:
            aforo -= 1
        with open("aforo_log.txt", "a") as archivo:
            archivo.write(
                f"{current_time} - Dispositivo: {id_dispositivo}, Secuencia: {numero_secuencia}, Aforo: {aforo}\n")

        # Mostrar estado actual del aforo con hora a la que llega
        print(f"{current_time} - Dispositivo: {id_dispositivo}, Secuencia: {numero_secuencia}, Aforo: {aforo}")
        print(f"{current_time} - CLIENTES CONECTADOS: {clientes_conectados}")

    if id_dispositivo in id_disp_num_sec:
        if numero_secuencia < id_disp_num_sec[id_dispositivo]:
            print(f"{current_time} - Reinicio detectado en el cliente {id_dispositivo}")
    else:
        print(f"{current_time} - Primer mensaje del cliente {id_dispositivo}")

    id_disp_num_sec[id_dispositivo] = numero_secuencia
    print(f"{current_time} - ID_DISP/NUM_SEC: {id_disp_num_sec}")
    #print(f"{current_time} - {id_disp_num_sec[id_dispositivo]}")

data = "1,7,incrementa2,567,decrementa1,7895,nada1,23,nada1,24,incrementa"
print(f"Datos recibidos: {data}")

numero_campos = len(data.split(','))
print(f"Número de campos: {numero_campos}")
numero_mensajes = math.trunc(numero_campos/2)
print(f"Número de mensajes {numero_mensajes}")

for i in range (numero_mensajes):
    id_dispositivo_prov = data.split(',')[0 + 2 * i]
    cadena1 = ""
    for char in id_dispositivo_prov:
        if char.isdigit():
            cadena1 += char
    id_dispositivo = int(cadena1)
    numero_secuencia_prov = data.split(',')[1 + 2 * i]
    cadena2 = ""
    for char in numero_secuencia_prov:
        if char.isdigit():
            cadena2 += char
    numero_secuencia = int(cadena2)
    presentacion_variacion_prov = data.split(',')[2 + 2 * i]
    cadena3 = ""
    for char in presentacion_variacion_prov:
        if char.isalpha():
            cadena3 += char
    presentacion_variacion = str(cadena3)

    print(f"ID DISPOSITIVO: {id_dispositivo}, NÚMERO DE SECUENCIA: {numero_secuencia}, PRESENTACIÓN/VARIACIÓN: {presentacion_variacion}")

    contabilizar(id_dispositivo, numero_secuencia, presentacion_variacion)


