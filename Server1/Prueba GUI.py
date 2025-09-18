import math
import socket
import threading
import time
from datetime import datetime
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


def obtener_ultimo_aforo():
    try:
        with open("aforo_log.txt", "r") as archivo:
            lines = archivo.readlines()
            if lines:
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
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            data = client_socket.recv(1024).decode()
            print(f"{current_time} - {data}")

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

    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    hora_ultimo_mensaje[id_dispositivo] = time.time()
    clientes_conectados[id_dispositivo] = "Activo"

    if presentacion_variacion == "presentacion":
        print(
            f"{current_time} - Conexión establecida con el cliente {id_dispositivo} con IP y puerto: {addr}. ACTIVE THREADS: {threading.active_count() - 1}")
        print(f"{current_time} - {clientes_conectados}")

    elif presentacion_variacion in ["incrementa", "decrementa", "nada"]:
        if presentacion_variacion == "incrementa":
            aforo += 1
        elif presentacion_variacion == "decrementa" and aforo > 0:
            aforo -= 1
        with open("aforo_log.txt", "a") as archivo:
            archivo.write(
                f"{current_time} - Dispositivo: {id_dispositivo}, Secuencia: {numero_secuencia}, Aforo: {aforo}\n")

        # Actualizar gráfico
        actualizar_grafico_aforo()

        # Mostrar estado actual del aforo con hora a la que llega
        print(f"{current_time} - Dispositivo: {id_dispositivo}, Secuencia: {numero_secuencia}, Aforo: {aforo}")

    if id_dispositivo in id_disp_num_sec:
        if numero_secuencia < id_disp_num_sec[id_dispositivo]:
            print(f"{current_time} - Reinicio detectado en el cliente {id_dispositivo}")
    else:
        print(f"{current_time} - Primer mensaje del cliente {id_dispositivo}")

    id_disp_num_sec[id_dispositivo] = numero_secuencia
    actualizar_lista_clientes()


def monitor_conexiones(hora_ultimo_mensaje, clientes_conectados):
    while True:
        time.sleep(30)
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"{current_time} - {clientes_conectados}")
        for id_dispositivo, tiempo in hora_ultimo_mensaje.items():
            if clientes_conectados.get(id_dispositivo) == "Activo":
                print(
                    f"{current_time} - {time.time() - tiempo} TIEMPO DESDE EL ÚLTIMO MENSAJE DE DISPOSITIVO: {id_dispositivo}")
                if time.time() - tiempo > 65:
                    print(f"{current_time} - Cliente {id_dispositivo} desconectado por tiempo de espera.")
                    clientes_conectados[id_dispositivo] = "No activo"
                    print(f"Estado de las conexiones: {clientes_conectados}")
                    actualizar_lista_clientes()


def aceptar_conexiones(server_socket):
    while True:
        client_socket, addr = server_socket.accept()

        client_thread = threading.Thread(target=handle_client, args=(client_socket, addr))
        client_thread.start()


def actualizar_grafico_aforo():
    tiempos.append(datetime.now().strftime('%H:%M:%S'))
    aforos.append(aforo)

    ax.clear()
    ax.plot(tiempos, aforos, marker='o')
    ax.set_ylim(bottom=0)  # Asegurar que el eje y empieza en 0
    ax.set_xlabel('Tiempo')
    ax.set_ylabel('Aforo')
    ax.set_title('Aforo en tiempo real')

    # Ajustar el límite del eje x para desplazar el gráfico hacia la derecha
    if len(tiempos) > 10:
        ax.set_xlim(left=len(tiempos) - 10, right=len(tiempos))

    canvas.draw()


def actualizar_lista_clientes():
    for item in tree.get_children():
        tree.delete(item)

    for id_dispositivo, estado in clientes_conectados.items():
        tree.insert("", "end", values=(id_dispositivo, estado, id_disp_num_sec.get(id_dispositivo, "")))


# Inicializamos la variable aforo
aforo = obtener_ultimo_aforo()
clientes_conectados = {}
hora_ultimo_mensaje = {}
id_disp_num_sec = {}

# Inicializamos la IP y puerto del server
server_IP = socket.gethostbyname(socket.gethostname())
PORT = 12345

# Creamos el socket del server y lo ponemos en escucha
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((server_IP, PORT))
server_socket.listen()

print("Servidor TCP iniciado.")

monitor_thread = threading.Thread(target=monitor_conexiones, daemon=True,
                                  args=(hora_ultimo_mensaje, clientes_conectados))
monitor_thread.start()

# Iniciamos la interfaz gráfica
root = tk.Tk()
root.title("Monitor de Aforo")
root.iconbitmap("monitor.ico")

# Gráfico de aforo
fig, ax = plt.subplots()
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# Añadir barra de herramientas para permitir desplazamiento
toolbar = NavigationToolbar2Tk(canvas, root)
toolbar.update()
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

tiempos = []
aforos = []

# Tabla de clientes
frame = ttk.Frame(root)
frame.pack(fill=tk.BOTH, expand=True)

tree = ttk.Treeview(frame, columns=("ID Dispositivo", "Estado", "Número de Secuencia"), show="headings")
tree.heading("ID Dispositivo", text="ID Dispositivo")
tree.heading("Estado", text="Estado")
tree.heading("Número de Secuencia", text="Número de Secuencia")
tree.pack(fill=tk.BOTH, expand=True)

# Aceptar conexiones en un hilo separado para no bloquear la interfaz gráfica
conexion_thread = threading.Thread(target=aceptar_conexiones, args=(server_socket,))
conexion_thread.start()

root.mainloop()
