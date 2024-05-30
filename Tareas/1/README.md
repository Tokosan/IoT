# T1

## Integrantes

- Camilo Araya
- Bastián Bas
- Emmanuel Faúndez

---

## Flujo de datos

La manera en que se comunican los componentes es:

0. La Raspberry Pi tiene dos instancias de servidor (una para cada ESP) escuchando en `(0.0.0.0, 1234)` y `(0.0.0.0, 1235)` con un socket TCP que denominamos *socket principal* o *socket de conexión*.

1. Las ESP se bootean, y cada una se conecta a un servidor distinto. En la demostración la ESP conectada por el puerto COM3 se conectaba al servidor del puerto 1234, y la conectada por el puerto COM4 se conectaba al servidor del puerto 1235. Para que cada ESP tuviera un destino distinto, hicimos dos carpetas de proyecto ESPRESSIF; `codigo_esp_1234` y `codigo_esp_1235`. Los archivos `main.c` de cada proyecto son exactamente idénticos salvo por el puerto de conexión y comunicación.

De ahora en adelante hablaremos de la ESP conectada por el puerto COM3, pero todo lo dicho es análogo para la ESP conectada por el puerto COM4.

2. La Raspberry Pi recibe la conexión de la ESP.

3. La ESP envía la petición de protocolo y capa de transporte a la Raspberry Pi.

4. La Raspberry Pi recibe la petición y manda el protocolo y capa de transporte que esté activo según la base de datos. La manera en que implementamos esto es añadirle un campo `active` a la tabla `Configuracion`, permitiendo que cada vez que revise la tabla pueda buscar qué configuración está activa.

5. La ESP recibe la configuración y comienza a generar y mandar los paquetes del protocolo recibido, con un socket correspondiente a la capa de transporte solicitada. Este socket se abre también en la Raspberry Pi, pero en el puerto 12340 (o 12350 en el otro servidor). Este socket lo denominamos *socket de comunicación*.

6. La Raspberry Pi recibe los paquetes y los guarda en la base de datos.

7. Dependiendo de la capa de transporte, en la Raspberry Pi ocurre una de dos cosas:

    - Si la capa de transporte es `UDP`, la Raspberry Pi vuelve a mandarle inmediatamente la configuración que esté activa a la ESP.
    - Si la capa de transporte es `TCP`, la Raspberry Pi no le manda nada a la ESP.

8. Dependiendo de la capa de transporte, en la ESP ocurre una de dos cosas:

    - Si la capa de transporte es `UDP`, la ESP recibe la configuración y revisa si es que hubo un cambio de protocolo o capa de transporte. Si hay un cambio de protocolo únicamente entonces sigue mandando los paquetes por el socket de comunicación, pero si hay un cambio de capa de transporte entonces cierra el socket de comunicación (la Rasp también lo hace) y reinicia la ESP.
    - Si la capa de transporte es `TCP`, la ESP no recibe la configuración, y siempre se reinicia al terminar el envío de un paquete. Esto cierra todos los sockets. La Rasp sólo cierra el de comunicación y sigue esperando la conexión de la ESP por el socket de conexión.

9. En cualquier momento se puede utilizar la API que desarrollamos para cambiar la configuración activa. La manera de hacer esto es ejecutar la aplicación con Flask en `app.py`. Para hacer esto se recomienda crear un ambiente virtual, instalar los paquetes especificados en `requirements.txt`, y ejecutar `python3 app.py`. Esto abrirá una API en `0.0.0.0:5000` que tiene la interfaz mostrada en la demotración. Si no se quiere hacer esto, la otra opción es conectarse a la base de datos por algún gestor como Beekeeper Studio o DBeaver y cambiar el campo `active` de la tabla `Configuracion` a `1` (y el resto a `0`) para la configuración que se quiera activar.

## Implementaciones

### Servidores

Como se mencionó arriba, tenemos dos instancias de servidor, eso implica que en dos terminales distintas hay que ejecutar 
```bash
python3 server.py 1234
```

y

```bash
python3 server.py 1235
```

### Protocolo 4

Para el protocolo 4 lo que hicimos fue mandar primero un paquete igual al del protocolo 2, y luego mandar 48 paquetes de largo 1012 bytes (header + 1000). Estos paquetes conforman los 48kB que hay que hacer llegar a la Rasp.

### Timestamp

Debido a cómo funciona la ESP, su epoch no está bien definido y siempre parte en 0 al prenderse.

Para implementar el timestamp lo que hicimos fue añadirle al mensaje de petición de protocolo de la ESP (`get_ids`) un entero que corresponde al `time(NULL)` al momento de mandar la petición. La Rasp recibe este entero y lo compara con lael `time.now()` interno, permitiéndole calcular la diferencia de tiempo entre la ESP y la Rasp. Luego, cuando la ESP manda paquetes con un timestamp (protocolos >= 1) la Rasp le suma la diferencia de tiempo a este timestamp, permitiéndole tener un timestamp más o menos correcto.

### Loss

La tabla de Loss no pudo ser bien implementada, nuestra implementación parece ser correcta, pero por alguna razón hay valores que no tienen sentido en la tabla (al final de la demostración se puede observar esto). No tenemos tiempo para debuggear esto.




## Base de datos

### Iniciar la base de datos

```bash
docker compose up -d
```

### Detener la base de datos

```bash
docker compose down
```

### Borrar la base de datos

```bash
docker compose down 
docker volume rm tarea1-iot_postgres_data_iot
```

### Recrear la base de datos

```bash
docker compose down 
docker volume rm tarea1-iot_postgres_data_iot
python3 codigo_rasp/models.py
```

### Eliminar datos de la DB

```bash
python3 utils.py
```