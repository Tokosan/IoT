from peewee import *
from models import *

db_config = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',
    'database': 'iot_db'
}

def conexionDB():
    return PostgresqlDatabase(**db_config)

def get_ids():
    active_config = Configuracion.select().where(Configuracion.active == 1)
    resultado = conexionDB().execute(active_config)
    id_protocol = None
    id_transport_layer = None
    for r in resultado:
        print(r)
        id_protocol = r[1]
        id_transport_layer = r[2]
    return id_protocol, id_transport_layer

def set_active(protocol, transport_layer):
    q = Configuracion.update(active=0).where(Configuracion.id > 0)
    conexionDB().execute(q)
    q = Configuracion.update(active=1).where(
        (Configuracion.id_protocol == protocol) &
        (Configuracion.id_transport_layer == transport_layer)
    )
    conexionDB().execute(q)


def get_device_id(macaddress):
    device = Devices.select().where(Devices.mac == macaddress)
    response = conexionDB().execute(device).fetchone()
    if response is not None:
        return response[0]
    else:
        q = Devices.insert(mac=macaddress)
        response = conexionDB().execute(q).fetchone()
        return response[0]

def remove_all_data():
    q = Datos.delete()
    conexionDB().execute(q)
    q = Logs.delete()
    conexionDB().execute(q)
    q = Loss.delete()
    conexionDB().execute(q)
    
if __name__ == "__main__":
    remove_all_data()