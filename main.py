import sys
import serial
import serial.tools.list_ports
import os
import time
import threading
from PyQt5.QtWidgets import QApplication, QLineEdit,QMainWindow, QPushButton, QLabel, QComboBox, QVBoxLayout, QWidget, QMessageBox, QFormLayout, QFileDialog, QProgressBar, QTextEdit, QHBoxLayout

from ymodem import YModem

class SerialTool(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("YModem 串口升级工具")
        self.resize(400, 450)

        self.port_label = QLabel("选择串口:")
        self.port_combo = QComboBox()
        self.refresh_ports()

        self.refresh_button = QPushButton("刷新")
        self.refresh_button.clicked.connect(self.refresh_ports)

        self.baudrate_label = QLabel("选择波特率:")
        self.baudrate_combo = QComboBox()

        self.baudrate_combo.addItem("9600")
        self.baudrate_combo.addItem("57600")
        self.baudrate_combo.addItem("115200")
        self.baudrate_combo.addItem("420000")
        self.baudrate_combo.addItem("921600")

        self.open_button = QPushButton("打开串口")  # 默认文本为打开串口
        self.open_button.clicked.connect(self.toggle_port)  # 按钮点击事件

        self.update_button = QPushButton("发送IAP升级命令")  # 默认文本为打开串口
        self.update_button.clicked.connect(self.send_update_command)  # 按钮点击事件

        self.file_label = QLabel("选择文件:")
        self.file_button = QPushButton("浏览")
        self.file_name = ""

        # 新增标签用于显示文件路径
        self.file_path_label = QLineEdit()

        self.file_button.clicked.connect(self.open_file_dialog)

        self.start_button = QPushButton("开始传输")
        self.start_button.clicked.connect(self.start_transfer)

        # 新增标签用于显示接收到的数据
        self.received_data_label = QLabel("接收到的数据: ")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)

        # 新增文本显示框
        self.received_data_text_edit = QTextEdit()
        self.received_data_text_edit.setReadOnly(True)  # 设置为只读

        layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        # 创建水平布局，用于包含串口选择框和刷新按钮
        port_layout = QHBoxLayout()
        port_layout.addWidget(self.port_combo)
        port_layout.addWidget(self.refresh_button)

        # 添加波特率选择框和打开按钮
        baudrate_layout = QHBoxLayout()
        baudrate_layout.addWidget(self.baudrate_combo)
        baudrate_layout.addWidget(self.open_button)

        # 添加波特率选择框和打开按钮
        file_layout = QHBoxLayout()
        file_layout.addWidget(self.file_path_label)
        file_layout.addWidget(self.file_button)

        # 将新的水平布局添加到表单布局中
        form_layout.addRow(self.port_label, port_layout)
        form_layout.addRow(self.baudrate_label, baudrate_layout)
        form_layout.addRow(self.update_button)
        form_layout.addRow(self.file_label, file_layout)

        layout.addLayout(form_layout)

        layout.addWidget(self.start_button)  # 新增开始传输按钮
        layout.addWidget(self.progress_bar)  # 新增进度条
        
        # 添加文本显示框到布局
        layout.addWidget(self.received_data_label)
        layout.addWidget(self.received_data_text_edit)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.serial = None  # 保存串口对象

    def refresh_ports(self):
        ports = serial.tools.list_ports.comports()
        self.port_combo.clear()
        for port in ports:
            self.port_combo.addItem(port.device)

    def open_file_dialog(self):
        self.file_name, _ = QFileDialog.getOpenFileName(self, "选择文件", "", "所有文件 (*)")
        if self.file_name: 
            self.file_path_label.setText(self.file_name)  # 更新文件路径标签显示

    def toggle_port(self):
        if self.serial and self.serial.is_open:  # 检查串口是否已打开
            self.serial.close()  # 关闭串口
            self.open_button.setText("打开串口")
            QMessageBox.information(self, "信息", "串口已关闭")
        else:
            selected_port = self.port_combo.currentText()
            selected_baudrate = self.baudrate_combo.currentText()

            if not selected_port or not selected_baudrate:
                QMessageBox.warning(self, "错误", "请选择串口和波特率")
                return
            
            try:

                self.serial = serial.Serial(selected_port, selected_baudrate, timeout=1)
                self.open_button.setText("关闭串口")
                # QMessageBox.information(self, "信息", f"成功打开串口 {selected_port}，波特率 {selected_baudrate}")
                # 开启一个新线程来接收串口数据
                threading.Thread(target=self.receive_data, daemon=True).start()
            except Exception as e:
                QMessageBox.critical(self, "错误", str(e))
                self.serial = None  # 确保 serial 在失败时被设置为 None

    def send_update_command(self):
        if self.serial and self.serial.is_open:  # 检查串口是否已打开
            # 发送特定的16进制命令
            command = bytearray([0x60, 0xF1, 0x55, 0x55])
            self.serial.write(command)


    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_received_data(self, data):
        # 在文本框中显示接收到的数据
        self.received_data_text_edit.append(data)  # 在文本框中追加数据

    def start_transfer(self):
        if not self.serial or not self.serial.is_open:
            QMessageBox.warning(self, "错误", "请先打开串口")
            return

        selected_port = self.port_combo.currentText()
        if not selected_port:
            QMessageBox.warning(self, "错误", "请先选择一个串口")
            return

        selected_baudrate = self.baudrate_combo.currentText()
        if not selected_baudrate:
            QMessageBox.warning(self, "错误", "请先选择一个波特率")
            return

        if not self.file_name:
            QMessageBox.warning(self, "错误", "请先选择一个文件")
            return

        QMessageBox.information(self, "信息", f"开始通过 {selected_port} 传输文件...")

        try:

            # 发送字符 '1'
            self.serial.write(b'1')  # 发送字符 '1'，以字节形式发送
            # 延时1秒
            time.sleep(1)
            # 开始文件传输
            # y_mode = YModem()

            # 计算文件大小
            total_size = os.path.getsize(self.file_name)
            sent_size = 0

            def callback(data):
                nonlocal sent_size
                sent_size += len(data)
                progress = int((sent_size / total_size) * 100)
                self.update_progress(progress)

            # y_mode.send(self.file_name, callback=callback)
            # success = y_mode.send(self.file_name)
            y_mode.send(r'.\gps_keil_app.bin')
            # 检查返回值
            # if success:
            #     print("文件发送成功")
            # else:
            #     print("文件发送失败")

            self.update_progress(100)  # 传输完成，更新进度条到100%

            y_mode.close()
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))

    def receive_data(self):
        while self.serial and self.serial.is_open:
                if self.serial.in_waiting > 0:
                    data = self.serial.read(self.serial.in_waiting)
                    self.update_received_data(data.decode('utf-8', errors='ignore'))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    y_mode = YModem()
    window = SerialTool()
    window.show()
    sys.exit(app.exec_())
