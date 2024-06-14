import mysql.connect

def get_connection():
    try:
        cnx = mysql.connector.connect(user='root', password='dcc',
                                      host='localhost',
                                      database='mydb')
        return cnx
    except mysql.connector.Error as err:
        print(f"Something went wrong: {err}")
        return None
    
def insert_config(config):
    cnx = get_connection()
    if cnx is None:
        return
    cursor = cnx.cursor()
    add_config = ("INSERT INTO configuration "
                  "(Status_conf, Protocol_conf, Acc_sampling, Acc_sensibility, Gyro_sensibility, BME688_sampling, Discontinuos_time, TCP_PORT, UDP_port, Host_ip_addr, Ssid, Pass) "
                  "VALUES (%(status)s, %(id_protocol)s, %(acc_sampling)s, %(acc_sensibility)s, %(gyro_sensibility)s, %(bme668_sampling)s, %(discontinuos_time)s, %(tcp_port)s, %(udp_port)s, %(host_ip_addr)s, %(ssid)s, %(pass)s)")

    cursor.execute(add_config, config)

    cnx.commit()
    cursor.close()
    cnx.close()
    
    
#Esta función se encarga de obtener la ultima configuración de la base de datos
def get_last_config():
    cnx = get_connection()
    cursor = cnx.cursor()
    # Obtenemos la ultima configuración insertada
    query = ("SELECT * FROM configuration ORDER BY Id_device DESC LIMIT 1")
    cursor.execute(query)

    config_tuple = cursor.fetchone()
    config = tuple_to_dict(config_tuple) if config_tuple else None
    cursor.close()
    cnx.close()

    return config if config is not None else None


def delete_all_configurations():
    cnx = get_connection()
    cursor = cnx.cursor()
    query = "DELETE FROM configuration"
    cursor.execute(query)
    cnx.commit()
    cursor.close()
    cnx.close()

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

# def main():
#     # Crear un diccionario de configuración de ejemplo
#     config = {
#         'status': 0,
#         'id_protocol': 1,
#         'acc_sampling': 100,
#         'acc_sensibility': 2,
#         'gyro_sensibility': 200,
#         'bme668_sampling': 50,
#         'discontinuos_time': 5,
#         'tcp_port': 8080,
#         'udp_port': 8081,
#         'host_ip_addr': '192.168.1.1',
#         'ssid': 'my_ssid',
#         'pass': 'my_password'
#     }

#     # Insertar la configuración en la base de datos
#     insert_config(config)

#     # Obtener la última configuración de la base de datos
#     last_config = get_last_config()

#     # Imprimir la última configuración
#     print(last_config)

# if __name__ == "__main__":
#     main()