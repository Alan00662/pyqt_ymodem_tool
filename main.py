import sys
import serial.tools.list_ports
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLineEdit, QLabel, QFileDialog, QVBoxLayout, QWidget, QComboBox, QTextEdit
from ymodem import YModem

import tkinter as tk
import time
import threading

class YModemUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('YModem File Sender')
        self.setGeometry(100, 100, 400, 300)

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.port_label = QLabel('Select Serial Port:')
        self.port_input = QComboBox()  # 使用 QComboBox 替换 QLineEdit
        self.populate_ports()  # 填充可用串口

        self.baudrate_label = QLabel('Select Baud Rate:')
        self.baudrate_input = QComboBox()  # 创建波特率下拉框
        self.baudrate_input.addItems(['115200', '420000', '921600'])  # 添加可选波特率

        self.file_label = QLabel('File to Send:')
        self.file_input = QLineEdit()
        self.browse_button = QPushButton('Browse')
        self.browse_button.clicked.connect(self.browse_file)

        self.send_button = QPushButton('Send File')
        self.send_button.clicked.connect(self.send_file)

        # 添加发送IAP升级命令的按钮
        self.send_iap_button = QPushButton('发送IAP升级命令')
        self.send_iap_button.clicked.connect(self.send_iap_command)

        # 添加用于显示接收到的数据的 QTextEdit
        self.received_data_label = QLabel('Received Data:')
        self.received_data_display = QTextEdit()
        self.received_data_display.setReadOnly(True)  # 设置为只读

        layout.addWidget(self.port_label)
        layout.addWidget(self.port_input)
        layout.addWidget(self.baudrate_label)
        layout.addWidget(self.baudrate_input)
        layout.addWidget(self.file_label)
        layout.addWidget(self.file_input)
        layout.addWidget(self.browse_button)
        layout.addWidget(self.send_button)
        layout.addWidget(self.send_iap_button)  # 添加IAP升级命令按钮
        layout.addWidget(self.received_data_label)
        layout.addWidget(self.received_data_display)  # 添加文本显示框

        container = QWidget()
        container.setLayout(layout)

        self.setCentralWidget(container)

        # 并发接收数据的定时器
        self.timer = None

    def send_iap_command(self):
        port = self.port_input.currentText()  # 获取选中的串口
        baudrate = int(self.baudrate_input.currentText())  # 获取选中的波特率

        # 启动一个新的线程来发送命令
        threading.Thread(target=self.send_command, args=(port, baudrate)).start()

    def send_command(self, port, baudrate):
        try:
            with serial.Serial(port, baudrate, timeout=1) as ser:
                # 发送16进制数
                hex_data = bytes([0x60, 0xF1, 0x55, 0x55])
                ser.write(hex_data)
                print("发送16进制数: 0x60 0xF1 0x55 0x55")

        except Exception as e:
            print(f"发生错误: {e}")

    def send_enter_command(self, port, baudrate):
        try:
            with serial.Serial(port, baudrate, timeout=1) as ser:
                # 发送字符 '1'
                ser.write(b'1')
                print("发送字符: 1")
        except Exception as e:
            print(f"发生错误: {e}")

    def populate_ports(self):
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_input.addItem(port.device)  # 将可用串口添加到下拉框

    def browse_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, 'Select File', '', 'All Files (*)')
        if file_name:
            self.file_input.setText(file_name)

    def send_file(self):
        port = self.port_input.currentText()  # 获取选中的串口
        file_path = self.file_input.text()
        baudrate = int(self.baudrate_input.currentText())  # 获取选中的波特率

        if not file_path:
            print('Please select a file to send.')
            return

        y_mode = YModem()
        try:
            y_mode.open(port, baudrate)  # 使用选择的波特率
            y_mode.send(file_path)
            self.receive_data(y_mode)  # 开始接收数据
        finally:
            y_mode.close()
            print('File sent successfully!')

    def receive_data(self):
        # 伪代码 - 实际上你需要在这里实现接收数据的逻辑
        # 实际的接收逻辑可能涉及串口读取，应该在单独的线程中执行
        
        while True:
            if self.serial.in_waiting > 0:
                data = self.serial.read(self.serial.in_waiting)  # 读取接收到的数据
                self.update_received_data(data.decode('utf-8', errors='ignore'))  # 更新接收到的数据文本框

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = YModemUI()
    main_window.show()
    sys.exit(app.exec_())
