from models import *
from utils import get_ids
from packet_parser import *
import socket
from datetime import datetime, timedelta

HOST = '0.0.0.0'  # Escucha en todas las interfaces disponibles

def receive_data(socket, transport_layer, conn = None):
    if transport_layer == 0:
        # TCP
        if conn is None:
            conn, _ = socket.accept()  # Espera una conexion
        while True:
            data = conn.recv(1024)
            if data:
                return data, conn
    else:
        # UDP
        while True:
            data, _ = socket.recvfrom(1024)
            if data:
                return data, None
            
        


def start_communication(main_conn, id_protocol, id_transport_layer, comm_port, initial_timestamp):
    print("***********************************************")
    print("Iniciando comunicación")
    print(f"ID_protocol: {id_protocol}, ID_transport_layer: {id_transport_layer}")

    initial_datetime = datetime.now()

    while True:
        print("-----------------------------------------------")
        print(f"Esperando paquetes del protocolo {id_protocol}, por {'TCP' if id_transport_layer == 0 else 'UDP'}")
        protocol = int(id_protocol)

        # Crea un socket para comunicacion
        if id_transport_layer == 0:
            # Por TCP
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            # Por UDP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(10)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, comm_port))
                    
        if id_transport_layer == 0:
            s.listen(1)

        data, conn = receive_data(s, id_transport_layer)
        
        data_string = data.hex().upper()
        print("Recibido: ", ' '.join(a + b for a,b in zip(data_string[::2], data_string[1::2])))
        packet = parse_packet(data) # esto obtiene todo lo que tenga el paquete

        expected_length = packet["packet_length"]
        received_length = len(data)

        if protocol == 4:
            print("Empezando protocolo 4!")
            # Hay que recibir los otros 48 paquetes
            packet.update(prepare_kpi())
            for i in range(48):
                data, _ = receive_data(s, id_transport_layer, conn)
                data_string = data.hex().upper()
                print(f"Recibido paquete {i+1}/48: ", ' '.join(a + b for a,b in zip(data_string[::2], data_string[1::2])))
                packet = parse_kpi(packet, data, i)
                received_length += len(data)

        print("Received packet: ")
        print_packet(packet)

        if protocol != packet["protocol"]:
            print("Protocolo incorrecto, pero se guarda de todas maneras")

        # Parseamos el datetime del paquete según su timestamp
        if "timestamp" in packet:
            print(f"Timestamp: {packet['timestamp']}")
            print(f"initial_timestamp: {initial_timestamp}")
            packet_datetime = initial_datetime + (timedelta(seconds=packet["timestamp"] - initial_timestamp))
            print(f"packet_datetime: {packet_datetime}")
            delay = (datetime.now() - packet_datetime).seconds
            packet["timestamp"] = packet_datetime
        else:
            delay = 0

        packet_loss = expected_length - received_length

        # eliminamos el dato "packet_length" del packet
        packet.pop("packet_length")
        
        Datos.insert(packet).execute()
        Logs.insert(
            id_device=packet["id_device"],
            transport_layer=packet["transport_layer"],
            protocol=packet["protocol"]
        ).execute()
        Loss.insert(
            delay=delay,
            packet_loss=packet_loss
        ).execute()
        
        if id_transport_layer == "0":
            # TCP
            main_conn.close()
            s.close()
            return
        else:
            # UDP
            # Se envia el protocol e ID activos y se vuelve a conversar
            new_id_protocol, new_id_transport_layer = get_ids()
            if new_id_protocol != id_protocol or new_id_transport_layer != id_transport_layer:
                print(f"Hubo un cambio!: P -> {new_id_transport_layer} | TL -> {new_id_transport_layer}")
                id_protocol = new_id_protocol
                id_transport_layer = new_id_transport_layer
            # se informa de la nueva configuracion
            main_conn.send(f"{new_id_protocol}{new_id_transport_layer}".encode('utf-8'))
            if id_transport_layer == 0:
                print(f"Como TL == {id_transport_layer}, retornamos")
                main_conn.close()
                s.close()
                return
            else:
                print(f"Como TL == {id_transport_layer}, continuamos")

            
