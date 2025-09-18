import math
import socket
import threading
import time
import sqlite3
from datetime import datetime

def crear_base_de_datos():
    conn = sqlite3.connect('aforo.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS aforo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_hora TEXT,
            id_dispositivo INTEGER,
            numero_secuencia INTEGER,
            aforo INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conexiones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_hora TEXT,
            id_dispositivo INTEGER,
            estado TEXT,
            numero_secuencia INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def actualizar_aforo_bd(fecha_hora, id_dispositivo, numero_secuencia, aforo):
    conn = sqlite3.connect('aforo.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO aforo (fecha_hora, id_dispositivo, numero_secuencia, aforo)
        VALUES (?, ?, ?, ?)
    ''', (fecha_hora, id_dispositivo, numero_secuencia, aforo))
    conn.commit()
    conn.close()

def actualizar_conexiones_bd(fecha_hora, id_dispositivo, estado, numero_secuencia):
    conn = sqlite3.connect('aforo.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO conexiones (fecha_hora, id_dispositivo, estado, numero_secuencia)
        VALUES (?, ?, ?, ?)
    ''', (fecha_hora, id_dispositivo, estado, numero_secuencia))
    conn.commit()
    conn.close()

def obtener_ultimo_aforo():
    try:
        with open("aforo_log.txt", "r") as archivo:
            lines = archivo.readlines()
            if lines:
                # Leemos el último valor del aforo
                last_line = lines[-1].strip()
                primero, _, aforo = last_line.split(',')
                fecha = primero.split(' ')[0]
                if fecha != datetime.now().strftime('%Y-%m-%d'):
                    return 0
                else:
                    return int(aforo.split(':')[1])
    except FileNotFoundError:
        return 0
    except Exception as e:
        print(f"Error al leer el archivo. Error: {e}")
        return 0

def handle_client(client_socket, addr):
    while True:
        try:
            # Recibimos datos del cliente
            fecha_hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            data = client_socket.recv(1024).decode()
            print(f"{fecha_hora} - {data}")

            numero_campos = len(data.split(','))
            numero_mensajes = math.trunc(numero_campos / 2)

            for i in range(numero_mensajes):
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

                contabilizar(id_dispositivo, numero_secuencia, presentacion_variacion, addr)

        except ValueError as ve:
            print(f"Datos inválidos recibidos. Error: {ve}")
            break

    client_socket.close()

def contabilizar(id_dispositivo, numero_secuencia, presentacion_variacion, addr):
    global aforo

    fecha_hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    hora_ultimo_mensaje[id_dispositivo] = time.time()
    # print(f"{current_time} - {hora_ultimo_mensaje}")
    clientes_conectados[id_dispositivo] = "Activo"

    actualizar_conexiones_bd(fecha_hora, id_dispositivo, "Activo", numero_secuencia)

    if presentacion_variacion == "presentacion":
        print(f"{fecha_hora} - Conexión establecida con el cliente {id_dispositivo} con IP y puerto: {addr}. ACTIVE THREADS: {threading.active_count() - 1}")
        print(f"{fecha_hora} - {clientes_conectados}")

    # Escribimos en el archivo el aforo y la hora a la que llega
    elif presentacion_variacion in ["incrementa", "decrementa", "nada"]:
        if presentacion_variacion == "incrementa":
            aforo += 1
        elif presentacion_variacion == "decrementa" and aforo > 0:
            aforo -= 1
        with open("aforo_log.txt", "a") as archivo:
            archivo.write(f"{fecha_hora} - Dispositivo: {id_dispositivo}, Secuencia: {numero_secuencia}, Aforo: {aforo}\n")

        actualizar_aforo_bd(fecha_hora, id_dispositivo, numero_secuencia, aforo)

        # Mostrar estado actual del aforo con hora a la que llega
        print(f"{fecha_hora} - Dispositivo: {id_dispositivo}, Secuencia: {numero_secuencia}, Aforo: {aforo}")
        # print(f"{current_time} - {clientes_conectados}")

    if id_dispositivo in id_disp_num_sec:
        if numero_secuencia < id_disp_num_sec[id_dispositivo]:
            print(f"{fecha_hora} - Reinicio detectado en el cliente {id_dispositivo}")
    else:
        print(f"{fecha_hora} - Primer mensaje del cliente {id_dispositivo}")

    id_disp_num_sec[id_dispositivo] = numero_secuencia
    # print(f"{current_time} - {id_disp_num_sec}")
    # print(f"{current_time} - {id_disp_num_sec[id_dispositivo]}")

def monitor_conexiones(hora_ultimo_mensaje, clientes_conectados):
    while True:
        time.sleep(30)
        fecha_hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"{fecha_hora} - {clientes_conectados}")
        for id_dispositivo, tiempo in hora_ultimo_mensaje.items():
            if clientes_conectados.get(id_dispositivo) == "Activo":
                print(f"{fecha_hora} - {time.time() - tiempo} TIEMPO DESDE EL ÚLTIMO MENSAJE DE DISPOSITIVO: {id_dispositivo}")
                if time.time() - tiempo > 65:
                    print(f"{fecha_hora} - Cliente {id_dispositivo} desconectado por tiempo de espera.")
                    clientes_conectados[id_dispositivo] = "No activo"
                    actualizar_conexiones_bd(fecha_hora, id_dispositivo, "No Activo", id_disp_num_sec[id_dispositivo])
                    print(f"Estado de las conexiones: {clientes_conectados}")

def aceptar_conexiones(server_socket):
    while True:
        client_socket, addr = server_socket.accept()

        client_thread = threading.Thread(target=handle_client, args=(client_socket, addr))
        client_thread.start()

#Creamos la base de datos y la tabla aforo si no existe
crear_base_de_datos()

# Inicializamos la variable aforo
aforo = obtener_ultimo_aforo()
print(f"Aforo inicial: {aforo}")
clientes_conectados = {}
hora_ultimo_mensaje = {}
id_disp_num_sec = {}

# Inicializamos la IP y puerto del server
server_IP = socket.gethostbyname(socket.gethostname())
print(f"IP del server: {server_IP}")
PORT = 12345

# Creamos el socket del server y lo ponemos en escucha
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((server_IP, PORT))
server_socket.listen()

print("Servidor TCP iniciado.")

monitor_thread = threading.Thread(target=monitor_conexiones, daemon=True, args=(hora_ultimo_mensaje, clientes_conectados))
monitor_thread.start()

aceptar_conexiones(server_socket)
