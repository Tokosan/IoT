#import conexion_SQL as sql
from PyQt5 import QtWidgets
from base_interfaz import Ui_Dialog


#Esta clase se encarga de recolectar los datos de la interfaz
#y guardarlos en la base de datos de configuración
class InputCollector:
    def __init__(self, dialog):
        self.interface = Ui_Dialog()
        self.interface.setupUi(dialog)
        # cuando se aprete el boton configuracion se obtienen los datos de los campos
        # y se guardan en la base de datos
        self.interface.boton_configuracion.clicked.connect(self.get_and_save_config)

        # Mapeo de las opciones del combobox a los id_protocol compatibles
        self.op_mode = {"options": [
            {"name": "Configuración por Bluetooth", "protocols": ["1"], "value": 0},
            {"name": "Configuración vía TCP en BD", "protocols": ["1"], "value": 20},
            {"name": "Conexión TCP continua", "protocols": ["1", "2", "3", "4", "5"], "value": 21},
            {"name": "Conexión TCP discontinua", "protocols": ["1", "2", "3", "4", "5"], "value": 22},
            {"name": "Conexión UDP", "protocols": ["1", "2", "3", "4", "5"], "value": 23},
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
        self.discontinuos_time = ""
        self.tcp_port = ""
        self.udp_port = ""
        self.host_ip_addr = ""
        self.ssid = ""
        self.passw = ""

        self.interface.box_modo_op.addItems([mode.get("name") for mode in self.op_mode.get("options")])
        self.interface.box_modo_op.currentIndexChanged.connect(self.update_op_mode)

        self.interface.box_id_protocol.addItems(self.op_mode.get("current").get("protocols", []))
        self.interface.box_acc_sampling.addItems(self.acc_samplings.get("options", []))
        self.interface.box_acc_sensibility.addItems(self.acc_sensibilities.get("options", []))
        self.interface.box_gyro_sensibility.addItems(self.gyro_sensibilities.get("options", []))
        self.interface.box_bme_sampling.addItems(self.bme688_samplings.get("options", []))

        self.interface.box_id_protocol.currentIndexChanged.connect(self.update_id_protocol)
        self.interface.box_acc_sampling.currentIndexChanged.connect(self.update_acc_sampling)
        self.interface.box_acc_sensibility.currentIndexChanged.connect(self.update_acc_sensibility)
        self.interface.box_gyro_sensibility.currentIndexChanged.connect(self.update_gyro_sensibility)
        self.interface.box_bme_sampling.currentIndexChanged.connect(self.update_BME688_sampling)
        self.interface.text_disc_time.textChanged["QString"].connect(self.update_discontinuous_time)
        self.interface.text_tcp_port.textChanged["QString"].connect(self.update_tcp_port)
        self.interface.text_udp_port.textChanged["QString"].connect(self.update_udp_port)
        self.interface.text_host_ip.textChanged["QString"].connect(self.update_host_ip_addr)
        self.interface.text_ssid.textChanged["QString"].connect(self.update_ssid)
        self.interface.text_pass.textChanged["QString"].connect(self.update_passw)

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

    #Esta función se encarga de actualizar el combobox de id_protocol
    #según la opción seleccionada en el combobox de modo de operación,
    #mostrando solo los id_protocol compatibles con la opción seleccionada
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

    #Esta función se encarga de guardar los datos en la MongoDB y retorna el
    #diccionario con los datos recolectados
    def get_and_save_config(self):
        for key, value in self.config.items():
            self.interface.consola_1.setText(self.interface.consola_1.toPlainText() + f"{key}: {value}\n")

        #sql.insert_config(config)

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

    def update_passw(self, val):
        # Update the instance values
        self.passw = val
        self.config["pass"] = self.passw


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    util_parser = InputCollector(Dialog)
    Dialog.show()
    sys.exit(app.exec_())
