import socket
import struct

from utils import *
from models import *
from protocolos import start_communication
from sys import argv

HOST = '0.0.0.0' # Escucha en todas las interfaces disponibles
PORT =  int(argv[1])     # Puerto en el que se escucha

set_active(4, 0)

# Crea un socket para IPv4 y conexión TCP
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()
    s.settimeout(5)
    while True:
        try:
            print("El servidor está esperando conexiones en el puerto", PORT)
            conn, addr = s.accept()  # Espera una conexión
            print("Conectado por", addr)
            data = conn.recv(1024)  # Recibe hasta 1024 bytes del cliente
            if data:
                print("Datos recibidos:", ' '.join(a + b for a,b in zip(data.hex()[::2], data.hex()[1::2])))
                if data[:7].decode('utf-8') != "get_ids":
                    continue
                initial_timestamp = struct.unpack('i', data[7:11])[0]
                id_protocol, id_transport_layer = get_ids()
                if id_protocol is None:
                    continue
                conn.send(f"{id_protocol}{id_transport_layer}".encode('utf-8'))
                
                start_communication(conn, id_protocol, id_transport_layer, 10*PORT, initial_timestamp)
        except socket.timeout:
            print("Timeout esperando conexión")
            continue
