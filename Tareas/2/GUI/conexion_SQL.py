import mysql.connector
import pymysql
import logging
import sshtunnel
from sshtunnel import SSHTunnelForwarder

ssh_host = '192.168.0.9'
ssh_username = 'iot'
ssh_password = 'dcc'
database_username = 'root'
database_password = 'dcc'
database_name = 'mydb'
localhost = '127.0.0.1'

def open_ssh_tunnel(verbose=False):
    """Open an SSH tunnel and connect using a username and password.
    
    :param verbose: Set to True to show logging
    :return tunnel: Global SSH tunnel connection
    """
    
    if verbose:
        sshtunnel.DEFAULT_LOGLEVEL = logging.DEBUG
    
    global tunnel
    tunnel = SSHTunnelForwarder(
        (ssh_host, 202),
        ssh_username = ssh_username,
        ssh_password = ssh_password,
        remote_bind_address = ('127.0.0.1', 3306)
    )
    
    tunnel.start()

def mysql_connect():
    """Connect to a MySQL server using the SSH tunnel connection
    
    :return connection: Global MySQL database connection
    """
    
    global conn
    
    conn = pymysql.connect(
        host='127.0.0.1',
        user=database_username,
        passwd=database_password,
        db=database_name,
        port=tunnel.local_bind_port
    )

def mysql_disconnect():
    """Closes the MySQL database connection.
    """
    
    conn.close()

def close_ssh_tunnel():
    """Closes the SSH tunnel connection.
    """
    
    tunnel.close
    
def connect():
    open_ssh_tunnel()
    mysql_connect()

def disconnect():
    mysql_disconnect()
    close_ssh_tunnel()
    
def insert_config(config):
    connect()
    if conn is None:
        return
    cursor = conn.cursor()
    add_config = ("INSERT INTO configuration "
                  "(Status_conf, Protocol_conf, Acc_sampling, Acc_sensibility, Gyro_sensibility, BME688_sampling, Discontinuos_time, TCP_PORT, UDP_port, Host_ip_addr, Ssid, Pass) "
                  "VALUES (%(status)s, %(id_protocol)s, %(acc_sampling)s, %(acc_sensibility)s, %(gyro_sensibility)s, %(bme668_sampling)s, %(discontinuos_time)s, %(tcp_port)s, %(udp_port)s, %(host_ip_addr)s, %(ssid)s, %(pass)s)")

    cursor.execute(add_config, config)

    conn.commit()
    disconnect()

    
#Esta función se encarga de obtener la ultima configuración de la base de datos
def get_last_config():
    connect()
    cursor = conn.cursor()
    # Obtenemos la ultima configuración insertada
    query = ("SELECT * FROM configuration ORDER BY Id_device DESC LIMIT 1")
    cursor.execute(query)

    config_tuple = cursor.fetchone()
    config = tuple_to_dict(config_tuple) if config_tuple else None 
    disconnect()
    return config

def delete_all_configurations():
    connect()
    cursor = conn.cursor()
    query = "DELETE FROM configuration"
    cursor.execute(query)
    conn.commit()
    disconnect()

def tuple_to_dict(config_tuple):
    keys = [
        "id_device",
        "status",
        "id_protocol",
        "acc_sampling",
        "acc_sensibility",
        "gyro_sensibility",
        "bme668_sampling",
        "discontinuos_time",
        "tcp_port",
        "udp_port",
        "host_ip_addr",
        "ssid",
        "pass"
    ]

    return dict(zip(keys, config_tuple))

# TEST para probar la conexión a la base de datos

def main():
    # Crear un diccionario de configuración de ejemplo
    config = {
        'status': 0,
        'id_protocol': 2,
        'acc_sampling': 100,
        'acc_sensibility': 2,
        'gyro_sensibility': 200,
        'bme668_sampling': 50,
        'discontinuos_time': 5,
        'tcp_port': 8080,
        'udp_port': 8081,
        'host_ip_addr': '10.20.1.1',
        'ssid': 'iot-wifi',
        'pass': 'iotdcc123'
    }

    # Insertar la configuración en la base de datos
    insert_config(config)

    # Obtener la última configuración de la base de datos
    last_config = get_last_config()

    # Imprimir la última configuración
    print(last_config)

if __name__ == "__main__":
    open_ssh_tunnel()
    main()