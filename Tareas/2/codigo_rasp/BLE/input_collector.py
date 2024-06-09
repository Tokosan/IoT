from PyQt5 import QtWidgets
from interfaz import Ui_Dialog
from pymongo import MongoClient

#Esta clase se encarga de recolectar los datos de la interfaz
#y guardarlos en la base de datos de configuración
class InputCollector:
    def __init__(self, dialog):
        self.interface = Ui_Dialog()
        self.interface.setupUi(dialog)
        # cuando se aprete el boton configuracion se obtienen los datos de los campos
        # y se guardan en la base de datos
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


    #Esta función se encarga de actualizar el combobox de id_protocol
    #según la opción seleccionada en el combobox de modo de operación,
    #mostrando solo los id_protocol compatibles con la opción seleccionada
    def update_id_protocol(self):
        selected_option = self.interface.box_modo_op.currentText().strip()
        compatible_id_protocols = self.modo_op_compatibilities.get(selected_option, [])
        self.interface.box_id_protocol.clear()
        for id_protocol in compatible_id_protocols:
            self.interface.box_id_protocol.addItem(id_protocol)

    #Esta función se encarga de guardar los datos en la MongoDB y retorna el
    #diccionario con los datos recolectados
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
        client.close()
        return config

#Esta función se encarga de obtener la ultima configuración de la base de datos
def get_last_config():
    client = MongoClient('localhost', 27017)
    db = client['config']
    collection = db['parametros']
    # Obtenemos la ultima configuración insertada
    config = collection.find().sort('_id', -1).limit(1)
    client.close()
    return config[0] if config.count() > 0 else None


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    util_parser = InputCollector(Dialog)
    Dialog.show()
    sys.exit(app.exec_())
