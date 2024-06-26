from PyQt5 import QtWidgets, QtCore
from base_interfaz import Ui_Dialog
import asyncio
from math import sin
import time, random
import db
from bleak import BleakClient, BleakScanner
from parser import encode_config

CHARACTERISTIC_UUID = "0000FF01-0000-1000-8000-00805F9B34FB"


# Esta clase se encarga de recolectar los datos de la interfaz
# y guardarlos en la base de datos de configuración
class InputCollector:
    def __init__(self, dialog):
        self.interface = Ui_Dialog()
        self.interface.setupUi(dialog)
        # cuando se aprete el boton configuracion se obtienen los datos de los campos
        # y se guardan en la base de datos
        self.interface.boton_configuracion.clicked.connect(self.get_and_save_config)
        self.interface.boton_configuracion_3.clicked.connect(self.scan_devices)

        # Mapeo de las opciones del combobox a los id_protocol compatibles
        self.op_mode = {"options": [
            {"name": "Configuración por Bluetooth", "protocols": ["1"], "value": 0},
            {"name": "BLE continua", "protocols": ["1", "2", "3", "4"], "value": 30},
            {"name": "BLE discontinua", "protocols": ["1", "2", "3", "4"], "value": 31}
        ]}
        self.acc_samplings = {"options": ["10", "100", "400", "1000"]}
        self.acc_sensibilities = {"options": ["2", "4", "8", "16"]}
        self.gyro_sensibilities = {"options": ["200", "250", "500"]}
        self.bme688_samplings = {"options": ["1", "2", "3", "4"]}

        self.op_mode["current"] = self.op_mode.get("options")[0]
        self.id_protocol = "1"
        self.acc_samplings["current"] = int(self.acc_samplings.get("options")[0])
        self.acc_sensibilities["current"] = int(self.acc_sensibilities.get("options")[0])
        self.gyro_sensibilities["current"] = int(self.gyro_sensibilities.get("options")[0])
        self.bme688_samplings["current"] = int(self.bme688_samplings.get("options")[0])
        self.discontinuos_time = "1"
        self.tcp_port = "8080"
        self.udp_port = "8081"
        self.host_ip_addr = "10.20.1.1"
        self.ssid = "iot-wifi"
        self.passw = "iotdcc123"

        self.mac = ""

        self.interface.box_modo_op.addItems([mode.get("name") for mode in self.op_mode.get("options")])
        self.interface.box_modo_op.currentIndexChanged.connect(self.update_op_mode)

        self.interface.box_id_protocol.addItems(self.op_mode.get("current").get("protocols", []))
        self.interface.box_acc_sampling.addItems(self.acc_samplings.get("options", []))
        self.interface.box_acc_sensibility.addItems(self.acc_sensibilities.get("options", []))
        self.interface.box_gyro_sensibility.addItems(self.gyro_sensibilities.get("options", []))
        self.interface.box_bme_sampling.addItems(self.bme688_samplings.get("options", []))

        self.interface.selec_esp.currentIndexChanged.connect(self.update_device)
        self.interface.box_id_protocol.currentIndexChanged.connect(self.update_id_protocol)
        self.interface.box_acc_sampling.currentIndexChanged.connect(self.update_acc_sampling)
        self.interface.box_acc_sensibility.currentIndexChanged.connect(self.update_acc_sensibility)
        self.interface.box_gyro_sensibility.currentIndexChanged.connect(self.update_gyro_sensibility)
        self.interface.box_bme_sampling.currentIndexChanged.connect(self.update_BME688_sampling)
        
        self.interface.selec_plot1.currentIndexChanged.connect(self.update_plots)
        self.interface.selec_plot2.currentIndexChanged.connect(self.update_plots)
        self.interface.selec_plot3.currentIndexChanged.connect(self.update_plots)
        
        self.interface.text_disc_time.textChanged["QString"].connect(self.update_discontinuous_time)
        self.interface.text_tcp_port.textChanged["QString"].connect(self.update_tcp_port)
        self.interface.text_udp_port.textChanged["QString"].connect(self.update_udp_port)
        self.interface.text_host_ip.textChanged["QString"].connect(self.update_host_ip_addr)
        self.interface.text_ssid.textChanged["QString"].connect(self.update_ssid)
        self.interface.text_pass.textChanged["QString"].connect(self.update_pass)

        self.interface.boton_inicio.clicked.connect(self.start_worker)
        self.interface.boton_detener.clicked.connect(self.stop_worker)

        # Config init
        self.config = {
            "status": self.op_mode.get("current").get("value", 0),
            "id_protocol": self.id_protocol,
            "acc_sampling": self.acc_samplings.get("current"),
            "acc_sensibility": self.acc_sensibilities.get("current"),
            "gyro_sensibility": self.gyro_sensibilities.get("current"),
            "bme668_sampling": self.bme688_samplings.get("current"),
            "discontinuos_time": self.discontinuos_time,
            "tcp_port": self.tcp_port,
            "udp_port": self.udp_port,
            "host_ip_addr": self.host_ip_addr,
            "ssid": self.ssid,
            "pass": self.passw
        }

        self.window = 20

        self.data = {
            "batt_level": {"data": [], "protocols": [1, 2, 3, 4]},
            
            "temp": {"data": [], "protocols": [2, 3, 4]},
            "hum": {"data": [], "protocols": [2, 3, 4]},
            "press": {"data": [], "protocols": [2, 3, 4]},
            "co": {"data": [], "protocols": [2, 3, 4]},
            
            "rms": {"data": [], "protocols": [3, 4]},
            
            "amp_x": {"data": [], "protocols": [4]},
            "amp_y": {"data": [], "protocols": [4]},
            "amp_z": {"data": [], "protocols": [4]},
            
            "freq_x": {"data": [], "protocols": [4]},
            "freq_y": {"data": [], "protocols": [4]},
            "freq_z": {"data": [], "protocols": [4]},
        }
        
        self.worker = None
        self.monitoring = False
        self.threadpool = QtCore.QThreadPool()
        self.threadpool.setMaxThreadCount(1)

        self.plotting = True
        self.timer = QtCore.QTimer()
        self.timer.setInterval(30)
        self.timer.timeout.connect(self.update_plots)
        self.timer.start()

    async def send_config(self):
        pass
        # client = BleakClient(self.mac)
        # print("Trying to connect to: ", client)
        # i = 0
        # while True:
        #     i += 1
        #     try:
        #         await client.connect()
        #         break
        #     except:
        #         continue
        # print(f"Connected (after {i} tries)")
        # await client.write_gatt_char(CHARACTERISTIC_UUID, encode_config())

    def scan_devices(self):
        asyncio.run(self.scan())

    async def scan(self):
        # Eliminamos los items que tenga selec_esp
        self.interface.selec_esp.clear()
        # Con esto podemos ver los dispositivos que estan disponibles
        # scanner = BleakScanner()
        # devices = await scanner.discover()
        # esps = []
        # for device in devices:
        #     if "ESP" in device.name:
        #         esps.append(device.address)
        # devices = esps
        devices = ["MAC1", "MAC2"]
        for device in devices:
            self.interface.selec_esp.addItem(device)

    async def get_data_cont(self):
        pass
        """ 
        client = BleakClient(self.mac)
        print("Trying to connect to: ", client)
        i = 0
        while True:
            try:
                await client.connect()
                break
            except:
                i += 1
        print(f"Connected (after {i} tries)")
        """
        i = 0
        while self.monitoring:
            # data = await client.read_gatt_char(CHARACTERISTIC_UUID)
            # data = parse_packet(data)
            i += 1
            data = {
                'batt_level': random.randint(0, 100),
                
                'temp': sin(i) * 100,
                'hum': random.randint(0, 100),
                'press': random.randint(0, 100),
                'co': random.randint(0, 100),
                
                'rms': random.randint(0, 100),
                
                'amp_x': random.randint(0, 100),
                'amp_y': random.randint(0, 100),
                'amp_z': random.randint(0, 100),
                
                'freq_x': random.randint(0, 100),
                'freq_y': random.randint(0, 100),
                'freq_z': random.randint(0, 100),
            }
            
            for key in data:
                self.data[key]['data'].append(data[key])
            
            print("Data:", data)
                
            if self.plotting:
                self.update_plots()
            time.sleep(.03)

    async def get_data_desc(self):
        while self.monitoring:
            """ 
            client = BleakClient(self.mac)
            print("Trying to connect to: ", client)
            i = 0
            while True:
                try:
                    await client.connect()
                    break
                except:
                    i += 1
            print(f"Connected (after {i} tries)")
            """
            # data = await client.read_gatt_char(CHARACTERISTIC_UUID)
            # data = parse_packet(data)
            for key in data:
                self.data[key]['data'].append(data[key])
            
            print("Data:", data)
                
            if self.plotting:
                self.update_plots()
        

    def clear_data(self):
        self.data = {
            "batt_level": {"data": [], "protocols": [1, 2, 3, 4]},
            
            "temp": {"data": [], "protocols": [2, 3, 4]},
            "hum": {"data": [], "protocols": [2, 3, 4]},
            "press": {"data": [], "protocols": [2, 3, 4]},
            "co": {"data": [], "protocols": [2, 3, 4]},
            
            "rms": {"data": [], "protocols": [3, 4]},
            
            "amp_x": {"data": [], "protocols": [4]},
            "amp_y": {"data": [], "protocols": [4]},
            "amp_z": {"data": [], "protocols": [4]},
            
            "freq_x": {"data": [], "protocols": [4]},
            "freq_y": {"data": [], "protocols": [4]},
            "freq_z": {"data": [], "protocols": [4]},
        }
        
    # Esta función se encarga de guardar los datos en la DB y retorna el
    # diccionario con los datos recolectados
    def get_and_save_config(self):
        self.config = {
            "status": self.op_mode.get("current").get("value", 0),
            "id_protocol": self.id_protocol,
            "acc_sampling": self.acc_samplings.get("current"),
            "acc_sensibility": self.acc_sensibilities.get("current"),
            "gyro_sensibility": self.gyro_sensibilities.get("current"),
            "bme668_sampling": self.bme688_samplings.get("current"),
            "discontinuos_time": self.discontinuos_time,
            "tcp_port": self.tcp_port,
            "udp_port": self.udp_port,
            "host_ip_addr": self.host_ip_addr,
            "ssid": self.ssid,
            "pass": self.passw
        }
        for key, value in self.config.items():
            print(f"{key}: {value}")
        db.insert_config(self.config)
        asyncio.run(self.send_config())

    def start_worker(self):
        self.toggle_fields_tab1(False)

        self.monitoring = True
        self.worker = Worker(self.start_monitoring, )
        self.threadpool.start(self.worker)

    def stop_worker(self):
         self.toggle_fields_tab1(True)
         self.monitoring = False
         self.clear_data()
         
         # If plotting, stop
         if self.plotting:
             self.stop_plotting()
        
    def update_plot_selectors(self):
        print("self.interface.selec_plot1", self.interface.selec_plot1)
        self.interface.selec_plot1.clear()
        self.interface.selec_plot2.clear()
        self.interface.selec_plot3.clear()
        for key in self.data:
            
            print("Searching for protocol:", self.id_protocol, "in", self.data[key]["protocols"])
            
            if int(self.id_protocol) not in self.data[key]["protocols"]:
                print("Not found")
                continue
            
            self.interface.selec_plot1.addItem(key)
            self.interface.selec_plot2.addItem(key)
            self.interface.selec_plot3.addItem(key)
        
    def start_monitoring(self):
        QtWidgets.QApplication.processEvents()
        self.update_plot_selectors()
        print("Iniciando obtencion de datos")
        if self.config["status"] == 31:
            asyncio.run(self.get_data_desc())
        else:
            asyncio.run(self.get_data_cont())
        print("Obtencion finalizada")

    def start_plotting(self):
        self.plotting = True
        self.toggle_fields_tab2(False)

    def stop_plotting(self):
        self.plotting = False
        self.toggle_fields_tab2(True)
        self.clear_data()

    def update_plots(self):
        # Obtenemos el parametro a graficar en el plot 1
        selectors = [self.interface.selec_plot1, self.interface.selec_plot2, self.interface.selec_plot3]
        cuves = [self.interface.curve1, self.interface.curve2, self.interface.curve3]
        for i in range(3):
            try:
                param = self.data[selectors[i].currentText()]
            except KeyError:
                continue
            data = param["data"]
            
            if len(data) > self.window:
                data = data[-self.window:]
                x = [i + len(data) - self.window for i in range(self.window)]
            else:
                x = list(range(len(data)))

            cuves[i].setData(x, data)

    def update_device(self, index):
        self.mac = self.interface.selec_esp.itemText(index)

    # Esta función se encarga de actualizar el combobox de id_protocol
    # según la opción seleccionada en el combobox de modo de operación,
    # mostrando solo los id_protocol compatibles con la opción seleccionada
    def update_op_mode(self, index):
        # Retrieve the selected operation mode
        selected_mode = self.op_mode.get("options")[index]

        # Update the instance values
        self.op_mode["current"] = selected_mode
        self.id_protocol = "1"

        # Refresh the interface
        compatible_id_protocols = selected_mode.get("protocols", [])
        self.interface.box_id_protocol.clear()
        for id_protocol in compatible_id_protocols:
            self.interface.box_id_protocol.addItem(id_protocol)

    def update_id_protocol(self, index):
        # Update the instance values
        self.id_protocol = self.op_mode.get("current").get("protocols")[index]
        self.config["id_protocol"] = self.id_protocol

    def update_acc_sensibility(self, index):
        # Update the instance values
        self.acc_sensibilities["current"] = int(self.acc_sensibilities.get("options")[index])
        self.config["acc_sensibility"] = self.acc_sensibilities.get("current")

    def update_acc_sampling(self, index):
        # Update the instance values
        self.acc_samplings["current"] = int(self.acc_samplings.get("options")[index])
        self.config["acc_sampling"] = self.acc_samplings.get("current")

    def update_gyro_sensibility(self, index):
        # Update the instance values
        self.gyro_sensibilities["current"] = int(self.gyro_sensibilities.get("options")[index])
        self.config["gyro_sensibility"] = self.gyro_sensibilities.get("current")

    def update_BME688_sampling(self, index):
        # Update the instance values
        self.bme688_samplings["current"] = int(self.bme688_samplings.get("options")[index])
        self.config["bme668_sampling"] = self.bme688_samplings.get("current")

    def update_discontinuous_time(self, val):
        # Update the instance values
        self.discontinuos_time = val
        self.config["discontinuos_time"] = self.discontinuos_time

    def update_tcp_port(self, val):
        # Update the instance values
        self.tcp_port = val
        self.config["tcp_port"] = self.tcp_port

    def update_udp_port(self, val):
        # Update the instance values
        self.udp_port = val
        self.config["udp_port"] = self.udp_port

    def update_host_ip_addr(self, val):
        # Update the instance values
        self.host_ip_addr = val
        self.config["host_ip_addr"] = self.host_ip_addr

    def update_ssid(self, val):
        # Update the instance values
        self.ssid = val
        self.config["ssid"] = self.ssid

    def update_pass(self, val):
        # Update the instance values
        self.passw = val
        self.config["pass"] = self.passw

    def toggle_fields_tab1(self, value: bool):
        self.interface.boton_detener.setEnabled(not value)
        self.interface.boton_configuracion.setEnabled(value)
        self.interface.boton_inicio.setEnabled(value)
        self.interface.selec_esp.setEnabled(value)
        self.interface.box_acc_sampling.setEnabled(value)
        self.interface.box_acc_sensibility.setEnabled(value)
        self.interface.box_gyro_sensibility.setEnabled(value)
        self.interface.box_bme_sampling.setEnabled(value)
        self.interface.box_modo_op.setEnabled(value)
        self.interface.box_id_protocol.setEnabled(value)
        self.interface.text_disc_time.setEnabled(value)
        self.interface.text_tcp_port.setEnabled(value)
        self.interface.text_udp_port.setEnabled(value)
        self.interface.text_host_ip.setEnabled(value)
        self.interface.text_ssid.setEnabled(value)
        self.interface.text_pass.setEnabled(value)

    def toggle_fields_tab2(self, value: bool):
        self.interface.selec_plot1.setEnabled(value)
        self.interface.selec_plot2.setEnabled(value)
        self.interface.selec_plot3.setEnabled(value)
        

# www.pyshine.com
class Worker(QtCore.QRunnable):

	def __init__(self, function, *args, **kwargs):
		super(Worker, self).__init__()
		self.function = function
		self.args = args
		self.kwargs = kwargs

	@QtCore.pyqtSlot()
	def run(self):

		self.function(*self.args, **self.kwargs)

if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    util_parser = InputCollector(Dialog)
    Dialog.show()
    sys.exit(app.exec_())
