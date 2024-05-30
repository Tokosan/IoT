from peewee import Model, PostgresqlDatabase, CharField, DateTimeField, IntegerField, FloatField, SmallIntegerField
from playhouse.postgres_ext import ArrayField
import datetime

# Tabla con los tipos de fields que hay en peewee
# https://docs.peewee-orm.com/en/latest/peewee/models.html#fields

# Configuración de la base de datos
db_config = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',
    'database': 'iot_db'
}
db = PostgresqlDatabase(**db_config)


# Definición de un modelo
class BaseModel(Model):
    class Meta:
        database = db


# Ahora puedes definir tus modelos específicos heredando de BaseModel
# y db estará conectado al servicio de PostgreSQL cuando realices operaciones de base de datos.


class Logs(BaseModel):
    """Esta tabla registrará la información de cada conexión recibida por el servidor,
    incluyendo el ID_device, el tipo de capa de transporte (Transport_Layer), el protocolo
    utilizado y su timestamp.
    """
    id_device       = CharField()
    transport_layer = CharField()
    protocol        = CharField(1)
    timestamp_real  = DateTimeField(default=datetime.datetime.now)


class Configuracion(BaseModel):
    """Esta tabla contendrá las variables ID_protocol y Transport_Layer,
    que se utilizarán para configurar el envío de datos al iniciar la conexión del ESP32.
    Estas variables deben poder modificarse de alguna manera.
    """
    id_protocol        = SmallIntegerField()
    id_transport_layer = SmallIntegerField()
    active             = SmallIntegerField(default=0)


class Loss(BaseModel):
    """Esta tabla almacenará el tiempo de demora en la comunicación (tiempo desde el momento de envío
    hasta el momento de escritura en la base de datos,calculado usando la diferencia entre esos timestamps)
    y la cantidad de pérdida de paquetes (packet loss) en bytes para cada comunicación que haya ocurrido."""
    delay   = IntegerField()
    packet_loss = IntegerField()


class Datos(BaseModel):
    """Esta tabla almacenará todos los datos recibidos, incluyendo un sello de tiempo (timestamp)
     y el identificador del dispositivo (Id_device y MAC)."""
    id_device       = CharField()
    mac             = CharField()
    protocol        = IntegerField()
    transport_layer = SmallIntegerField()
    
    # Data del protocolo 0
    batt_level = IntegerField()

    # Data del protocolo 1
    # timestamp = IntegerField(null=True)
    timestamp = DateTimeField(null=True)
    
    # Data del protocolo 2
    temp  = IntegerField(null=True)
    press = IntegerField(null=True)
    hum   = IntegerField(null=True)
    co    = FloatField(null=True)

    # Data del protocolo 3
    rms    = FloatField(null=True)
    amp_x  = FloatField(null=True)
    freq_x = FloatField(null=True)
    amp_y  = FloatField(null=True)
    freq_y = FloatField(null=True)
    amp_z  = FloatField(null=True)
    freq_z = FloatField(null=True)

    # Data del protocolo 4
    acc_x   = ArrayField(FloatField, null=True)
    acc_y   = ArrayField(FloatField, null=True)
    acc_z   = ArrayField(FloatField, null=True)
    r_gyr_x = ArrayField(FloatField, null=True)
    r_gyr_y = ArrayField(FloatField, null=True)
    r_gyr_z = ArrayField(FloatField, null=True)
    
    # timestamp real
    # timestamp_real = DateTimeField(default=datetime.datetime.now)


class Devices(BaseModel):
    """Esta tabla almacenará los datos de los dispositivos conectados al servidor,
    incluyendo el ID_device y la MAC address."""
    mac       = CharField()

db.create_tables([Logs, Configuracion, Loss, Datos,Devices])


# AcA se insertan los valores de la tabla Configuracion
# con las todas las posibles combinaciones de ID_protocol y Transport_Layer
# para que el Servidor pueda seleccionar la configuración que desee
for i in range(10):
    (Configuracion
    .insert(
        id=i+1,
        id_protocol=i//2,
        id_transport_layer=i%2,
    ).on_conflict(
        conflict_target=[Configuracion.id],
        preserve=[Configuracion.id_protocol, Configuracion.id_transport_layer],
        update={}
    ).execute())