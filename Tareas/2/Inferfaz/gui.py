from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFormLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QHBoxLayout, QSpacerItem, QSizePolicy,
    QTabWidget, QTableWidget, QTableWidgetItem
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt


class ConfigWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Set the window title and size
        self.setWindowTitle("Configuración y Visualización ESP32")
        self.setGeometry(100, 100, 800, 600)

        # Create the tab widget
        self.tabs = QTabWidget()

        # Create the configuration tab
        self.config_tab = QWidget()
        self.create_config_tab()

        # Create the visualization tab
        self.visual_tab = QWidget()
        self.create_visual_tab()

        # Add tabs to the tab widget
        self.tabs.addTab(self.config_tab, "Configuración")
        self.tabs.addTab(self.visual_tab, "Visualización")

        # Set the layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    def create_config_tab(self):
        # Set the font
        self.config_tab.setFont(QFont("Arial", 10))

        # Create the main layout
        main_layout = QVBoxLayout(self.config_tab)

        # Create the title label
        title = QLabel("Configuración de Dispositivo ESP32")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        main_layout.addWidget(title)

        # Create a form layout
        form_layout = QFormLayout()

        # Add form fields
        self.status_field = QComboBox()
        self.status_field.addItems(["0", "20", "21", "22", "23", "30", "31"])
        form_layout.addRow("Status:", self.status_field)

        self.id_protocol_field = QLineEdit()
        form_layout.addRow("ID Protocol:", self.id_protocol_field)

        self.bmi270_sampling_field = QComboBox()
        self.bmi270_sampling_field.addItems(["10", "100", "400", "1000"])
        form_layout.addRow("BMI270 Sampling:", self.bmi270_sampling_field)

        self.bmi270_acc_sensibility_field = QComboBox()
        self.bmi270_acc_sensibility_field.addItems(["2", "4", "8", "16"])
        form_layout.addRow("BMI270 Acc Sensibility:", self.bmi270_acc_sensibility_field)

        self.bmi270_gyro_sensibility_field = QComboBox()
        self.bmi270_gyro_sensibility_field.addItems(["200", "250", "500"])
        form_layout.addRow("BMI270 Gyro Sensibility:", self.bmi270_gyro_sensibility_field)

        self.bme688_sampling_field = QComboBox()
        self.bme688_sampling_field.addItems(["1", "2", "3", "4"])
        form_layout.addRow("BME688 Sampling:", self.bme688_sampling_field)

        self.discontinuous_time_field = QLineEdit()
        form_layout.addRow("Discontinuous Time:", self.discontinuous_time_field)

        self.port_tcp_field = QLineEdit()
        form_layout.addRow("Port TCP:", self.port_tcp_field)

        self.port_udp_field = QLineEdit()
        form_layout.addRow("Port UDP:", self.port_udp_field)

        self.host_ip_addr_field = QLineEdit()
        form_layout.addRow("Host IP Address:", self.host_ip_addr_field)

        self.ssid_field = QLineEdit()
        form_layout.addRow("SSID:", self.ssid_field)

        self.pass_field = QLineEdit()
        form_layout.addRow("Password:", self.pass_field)

        # Add the form layout to the main layout
        main_layout.addLayout(form_layout)

        # Create the buttons layout
        buttons_layout = QHBoxLayout()

        # Add spacer to align buttons to the right
        buttons_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        # Add the submit button
        self.submit_button = QPushButton("Guardar Configuración")
        self.submit_button.setStyleSheet("background-color: lightgreen; color: black;")
        self.submit_button.clicked.connect(self.submit_config)
        buttons_layout.addWidget(self.submit_button)

        # Add the cancel button
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setStyleSheet("background-color: lightcoral; color: black;")
        self.cancel_button.clicked.connect(self.close)
        buttons_layout.addWidget(self.cancel_button)

        # Add the buttons layout to the main layout
        main_layout.addLayout(buttons_layout)

    def create_visual_tab(self):
        # Set the font
        self.visual_tab.setFont(QFont("Arial", 10))

        # Create the main layout
        main_layout = QVBoxLayout(self.visual_tab)

        # Create the title label
        title = QLabel("Visualización de Datos")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        main_layout.addWidget(title)

        # Create a table to display data
        self.data_table = QTableWidget(10, 5)
        self.data_table.setHorizontalHeaderLabels(["Timestamp", "Temp", "Press", "Hum", "Co"])
        main_layout.addWidget(self.data_table)

        # Create a refresh button
        self.refresh_button = QPushButton("Actualizar Datos")
        self.refresh_button.setStyleSheet("background-color: lightblue; color: black;")
        self.refresh_button.clicked.connect(self.refresh_data)
        main_layout.addWidget(self.refresh_button)

    def submit_config(self):
        # Collect data from the form fields
        config_data = {
            "status": self.status_field.currentText(),
            "id_protocol": self.id_protocol_field.text(),
            "bmi270_sampling": self.bmi270_sampling_field.currentText(),
            "bmi270_acc_sensibility": self.bmi270_acc_sensibility_field.currentText(),
            "bmi270_gyro_sensibility": self.bmi270_gyro_sensibility_field.currentText(),
            "bme688_sampling": self.bme688_sampling_field.currentText(),
            "discontinuous_time": self.discontinuous_time_field.text(),
            "port_tcp": self.port_tcp_field.text(),
            "port_udp": self.port_udp_field.text(),
            "host_ip_addr": self.host_ip_addr_field.text(),
            "ssid": self.ssid_field.text(),
            "password": self.pass_field.text()
        }
        print("Configuración guardada:", config_data)
        # Aquí se pueden agregar las funciones para guardar la configuración en la base de datos y enviar los datos al ESP32.

    def refresh_data(self):
        # Aquí se agregarían las funciones para actualizar los datos en la tabla
        # Por ahora, vamos a llenar la tabla con datos ficticios
        for row in range(10):
            self.data_table.setItem(row, 0, QTableWidgetItem("2024-05-30 12:00:00"))
            self.data_table.setItem(row, 1, QTableWidgetItem("25.0"))
            self.data_table.setItem(row, 2, QTableWidgetItem("1013"))
            self.data_table.setItem(row, 3, QTableWidgetItem("45"))
            self.data_table.setItem(row, 4, QTableWidgetItem("50"))


if __name__ == "__main__":
    app = QApplication([])
    window = ConfigWindow()
    window.show()
    app.exec()
