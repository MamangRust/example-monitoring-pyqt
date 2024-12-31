import sys
import psutil
import platform
import subprocess
import re
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QGridLayout,
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont
import pyqtgraph as pg

class SystemInfoDashboard(QWidget):
    def __init__(self):
        super().__init__()

        self.cpu_data = [0] * 50
        self.ram_data = [0] * 50
        self.network_receive_data = [0] * 50
        self.network_send_data = [0] * 50
        self.cpu_temp_data = [0] * 50
        self.cpu_freq_data = [0] * 50

    
        self.prev_network_stats = psutil.net_io_counters()

        self.initUI()

      
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_system_info)
        self.timer.start(2000)  

        
        self.graph_timer = QTimer(self)
        self.graph_timer.timeout.connect(self.update_graphs)
        self.graph_timer.start(500)  

    def initUI(self):
        main_layout = QVBoxLayout()

        title = QLabel("System Monitoring")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        card_layout1 = QGridLayout()

        self.os_label = self.create_card("Operating System", "")
        card_layout1.addWidget(self.os_label, 0, 0)

        self.kernel_label = self.create_card("Kernel Version", "")
        card_layout1.addWidget(self.kernel_label, 0, 1)

        self.memory_label = self.create_card("Total Memory", "")
        card_layout1.addWidget(self.memory_label, 1, 0)

        self.available_label = self.create_card("Available Memory", "")
        card_layout1.addWidget(self.available_label, 1, 1)

        self.swap_label = self.create_card("Total Swap", "")
        card_layout1.addWidget(self.swap_label, 2, 0)

        self.available_swap_label = self.create_card("Available Swap", "")
        card_layout1.addWidget(self.available_swap_label, 2, 1)

        main_layout.addLayout(card_layout1)

        graph_layout1 = QGridLayout()

        self.cpu_graph = pg.PlotWidget(title="CPU Usage (%)")
        self.cpu_graph.setYRange(0, 100)
        self.cpu_line = self.cpu_graph.plot(
            self.cpu_data, pen=pg.mkPen(color="r", width=2)
        )
        graph_layout1.addWidget(self.cpu_graph, 0, 0)

        
        self.ram_graph = pg.PlotWidget(title="RAM Usage (%)")
        self.ram_graph.setYRange(0, 100)
        self.ram_line = self.ram_graph.plot(
            self.ram_data, pen=pg.mkPen(color="b", width=2)
        )
        graph_layout1.addWidget(self.ram_graph, 0, 1)

        main_layout.addLayout(graph_layout1)

        
        graph_layout2 = QGridLayout()

        # CPU Temperature Graph
        self.cpu_temp_graph = pg.PlotWidget(title="CPU Temperature (°C)")
        self.cpu_temp_graph.setYRange(0, 100)
        self.cpu_temp_line = self.cpu_temp_graph.plot(
            self.cpu_temp_data, pen=pg.mkPen(color="r", width=2)
        )
        graph_layout2.addWidget(self.cpu_temp_graph, 0, 0)

        self.cpu_freq_graph = pg.PlotWidget(title="CPU Frequency (MHz)")
        self.cpu_freq_graph.setYRange(0, 5000) 
        self.cpu_freq_line = self.cpu_freq_graph.plot(
            self.cpu_freq_data, pen=pg.mkPen(color="g", width=2)
        )
        graph_layout2.addWidget(self.cpu_freq_graph, 0, 1)

        main_layout.addLayout(graph_layout2)

        hardware_layout = QGridLayout()

        self.cpu_temp_label = self.create_card("CPU Temperature", "")
        hardware_layout.addWidget(self.cpu_temp_label, 0, 0)

        self.cpu_freq_label = self.create_card("CPU Frequency", "")
        hardware_layout.addWidget(self.cpu_freq_label, 0, 1)

        self.battery_label = self.create_card("Battery Status", "")
        hardware_layout.addWidget(self.battery_label, 1, 0)

        main_layout.addLayout(hardware_layout)

        graph_layout3 = QGridLayout()

        self.network_receive_graph = pg.PlotWidget(title="Network Receive (bytes/s)")
        self.network_receive_graph.setYRange(0, 1000000)
        self.network_receive_line = self.network_receive_graph.plot(
            self.network_receive_data, pen=pg.mkPen(color="g", width=2)
        )
        graph_layout3.addWidget(self.network_receive_graph, 0, 0)

        self.network_send_graph = pg.PlotWidget(title="Network Send (bytes/s)")
        self.network_send_graph.setYRange(0, 1000000)
        self.network_send_line = self.network_send_graph.plot(
            self.network_send_data, pen=pg.mkPen(color="b", width=2)
        )
        graph_layout3.addWidget(self.network_send_graph, 0, 1)

        main_layout.addLayout(graph_layout3)

        network_layout = QGridLayout()
        self.network_receive_label = QLabel("Network Receive: 0 MB")
        self.network_send_label = QLabel("Network Send: 0 MB")
        network_layout.addWidget(self.network_receive_label, 0, 0)
        network_layout.addWidget(self.network_send_label, 0, 1)
        main_layout.addLayout(network_layout)

        self.setLayout(main_layout)

        self.setWindowTitle("System Monitoring")
        self.setGeometry(100, 100, 1200, 1000)

        self.update_system_info()

    def create_card(self, title, value):
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card_layout = QVBoxLayout()

        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)

        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 10))
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setObjectName(title.lower().replace(" ", "_") + "_value")

        card_layout.addWidget(title_label)
        card_layout.addWidget(value_label)
        card.setLayout(card_layout)

        return card

    def get_cpu_temperature(self):
        try:
            try:
                sensors_output = subprocess.check_output(["sensors"], universal_newlines=True)
                temp_match = re.search(r'Core 0:\s+\+(\d+\.\d+)°C', sensors_output)
                if temp_match:
                    return float(temp_match.group(1))
            except:
                pass
            
            # Method 2: Using psutil (if available)
            temps = psutil.sensors_temperatures()
            if 'coretemp' in temps:
                return temps['coretemp'][0].current
            
            # Method 3: Try thermal zone from sysfs
            try:
                with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                    return float(f.read().strip()) / 1000
            except:
                pass
            
            return 0
        except:
            return 0

    def update_system_info(self):
        self.os_label.findChild(QLabel, "operating_system_value").setText(
            f"{platform.system()} {platform.release()}"
        )
        self.kernel_label.findChild(QLabel, "kernel_version_value").setText(
            platform.version()
        )

        memory = psutil.virtual_memory()
        self.memory_label.findChild(QLabel, "total_memory_value").setText(
            f"{memory.total // (1024 ** 3)} GB"
        )
        self.available_label.findChild(QLabel, "available_memory_value").setText(
            f"{memory.available // (1024 ** 3)} GB"
        )

        swap = psutil.swap_memory()
        self.swap_label.findChild(QLabel, "total_swap_value").setText(
            f"{swap.total // (1024 ** 3)} GB"
        )
        self.available_swap_label.findChild(QLabel, "available_swap_value").setText(
            f"{swap.free // (1024 ** 3)} GB"
        )

        network_stats = psutil.net_io_counters()
        self.network_receive_label.setText(
            f"Network Receive: {network_stats.bytes_recv // (1024 ** 2)} MB"
        )
        self.network_send_label.setText(
            f"Network Send: {network_stats.bytes_sent // (1024 ** 2)} MB"
        )

        cpu_temp = self.get_cpu_temperature()
        self.cpu_temp_label.findChild(QLabel, "cpu_temperature_value").setText(
            f"{cpu_temp:.1f}°C"
        )

        cpu_freq = psutil.cpu_freq().current
        self.cpu_freq_label.findChild(QLabel, "cpu_frequency_value").setText(
            f"{cpu_freq:.0f} MHz"
        )

        try:
            battery = psutil.sensors_battery()
            if battery:
                battery_status = (
                    f"{'Charging' if battery.power_plugged else 'Discharging'}, "
                    f"{battery.percent}%, "
                    f"Time Left: {battery.secsleft // 3600}h {(battery.secsleft % 3600) // 60}m"
                )
                self.battery_label.findChild(QLabel, "battery_status_value").setText(battery_status)
            else:
                self.battery_label.findChild(QLabel, "battery_status_value").setText("No Battery")
        except:
            self.battery_label.findChild(QLabel, "battery_status_value").setText("N/A")

        
        self.prev_network_stats = network_stats

    def update_graphs(self):
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        ram_percent = memory.percent
        
        network_stats = psutil.net_io_counters()
        bytes_recv = network_stats.bytes_recv - self.prev_network_stats.bytes_recv
        bytes_sent = network_stats.bytes_sent - self.prev_network_stats.bytes_sent

        self.cpu_data = self.cpu_data[1:] + [cpu_percent]
        self.ram_data = self.ram_data[1:] + [ram_percent]
        self.network_receive_data = self.network_receive_data[1:] + [bytes_recv]
        self.network_send_data = self.network_send_data[1:] + [bytes_sent]

       
        cpu_temp = self.get_cpu_temperature()
        self.cpu_temp_data = self.cpu_temp_data[1:] + [cpu_temp]

        
        cpu_freq = psutil.cpu_freq().current
        self.cpu_freq_data = self.cpu_freq_data[1:] + [cpu_freq]

       
        self.cpu_line.setData(self.cpu_data)
        self.ram_line.setData(self.ram_data)
        self.network_receive_line.setData(self.network_receive_data)
        self.network_send_line.setData(self.network_send_data)
        self.cpu_temp_line.setData(self.cpu_temp_data)
        self.cpu_freq_line.setData(self.cpu_freq_data)

       
        self.prev_network_stats = network_stats

def main():
    app = QApplication(sys.argv)
    dashboard = SystemInfoDashboard()
    dashboard.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
