from PyQt5 import QtWidgets
from interfaz import Ui_Dialog
from pymongo import MongoClient


class UtilParser:
    def __init__(self, dialog):
        self.interface = Ui_Dialog()
        self.interface.setupUi(dialog)
        self.interface.boton_configuracion.clicked.connect(self.get_and_save_config)

        # Mapeo de los status a valores numericos
        self.modo_op_values = {
            "Configuración por Bluetooth": 0,
            "Configuración vía TCP en BD": 20,
            "Conexión TCP continua": 21,
            "Conexión TCP discontinua": 22,
            "Conexión UDP": 23,
            "BLE continua": 30,
            "BLE discontinua": 31
        }

        # Mapeo de las opciones del combobox a los id_protocol compatibles
        self.modo_op_compatibilities = {
            "Configuración por Bluetooth": ["1"],
            "Configuración vía TCP en BD": ["1"],
            "Conexión TCP continua": ["1", "2", "3", "4", "5"],
            "Conexión TCP discontinua": ["1", "2", "3", "4", "5"],
            "Conexión UDP": ["1", "2", "3", "4", "5"],
            "BLE continua": ["1", "2", "3", "4"],
            "BLE discontinua": ["1", "2", "3", "4"]
        }
        self.interface.box_modo_op.currentIndexChanged.connect(self.update_id_protocol)



    def update_id_protocol(self):
        selected_option = self.interface.box_modo_op.currentText().strip()
        compatible_id_protocols = self.modo_op_compatibilities.get(selected_option, [])
        self.interface.box_id_protocol.clear()
        for id_protocol in compatible_id_protocols:
            self.interface.box_id_protocol.addItem(id_protocol)

    def get_and_save_config(self) -> dict:
        config = {
            "status": self.modo_op_values.get(self.interface.box_modo_op.currentText().strip(), 0),
            "id_protocol": self.interface.box_id_protocol.currentText().strip(),
            "acc_sampling": self.interface.box_acc_sampling.currentText().strip(),
            "acc_sensibility": self.interface.box_acc_sensibility.currentText().strip(),
            "gyro_sensibility": self.interface.box_gyro_sensibility.currentText().strip(),
            "bme668_sampling": self.interface.box_bme_sampling.currentText().strip(),
            "discontinuos_time": self.interface.text_disc_time.toPlainText().strip(),
            "tcp_port": self.interface.text_tcp_port.toPlainText().strip(),
            "udp_port": self.interface.text_udp_port.toPlainText().strip(),
            "host_ip_addr": self.interface.text_host_ip.toPlainText().strip(),
            "ssid": self.interface.text_ssid.toPlainText().strip(),
            "pass": self.interface.text_pass.toPlainText().strip()

        }
        for key, value in config.items():
            self.interface.consola_1.setText(self.interface.consola_1.toPlainText() + f"{key}: {value}\n")

        client = MongoClient('localhost', 27017)
        db = client['config']
        collection = db['parametros']
        collection.insert_one(config)
        return config


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    util_parser = UtilParser(Dialog)
    Dialog.show()
    sys.exit(app.exec_())
