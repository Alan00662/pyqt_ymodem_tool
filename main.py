import sys
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import *
from ymodem import YModem
import os
import tkinter as tk
import time
import threading



class YModemUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("YModem 串口升级工具")
        self.resize(400, 450)

        self.initUI()
    def initUI(self):
        layout = QVBoxLayout()

        form_layout = QFormLayout()

        self.port_label = QLabel('选择串口号:')
        self.port_input = QComboBox()  # 使用 QComboBox 替换 QLineEdit
        self.populate_ports()  # 填充可用串口

        self.baudrate_label = QLabel('选择波特率:')
        self.baudrate_input = QComboBox()  # 创建波特率下拉框
        self.baudrate_input.addItems(['115200', '420000', '921600'])  # 添加可选波特率

        self.open_button = QPushButton("打开串口")  # 默认文本为打开串口
        self.open_button.clicked.connect(self.toggle_port)  # 按钮点击事件

        self.file_label = QLabel('bin文件:')
        self.file_input = QLineEdit()
        self.browse_button = QPushButton('浏览')
        self.browse_button.clicked.connect(self.browse_file)

        # 添加发送IAP升级命令的按钮
        self.send_iap_button = QPushButton('发送IAP升级命令')
        self.send_iap_button.clicked.connect(self.send_iap_command)

        # 添加发送IAP升级命令的按钮
        self.send_enter_button = QPushButton('确认升级')
        self.send_enter_button.clicked.connect(self.send_enter_command)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)

        # 添加用于显示接收到的数据的 QTextEdit
        self.received_data_label = QLabel('Received Data:')
        self.received_data_display = QTextEdit()
        self.received_data_display.setReadOnly(True)  # 设置为只读

        layout.addWidget(self.port_label)
        layout.addWidget(self.port_input)
        layout.addWidget(self.baudrate_label)
        layout.addWidget(self.baudrate_input)
        layout.addWidget(self.open_button)  
        layout.addWidget(self.send_iap_button)  # 添加IAP升级命令按钮

        # 添加波特率选择框和打开按钮
        file_layout = QHBoxLayout()
        file_layout.addWidget(self.file_input)
        file_layout.addWidget(self.browse_button)

        form_layout.addRow(self.file_label, file_layout)

        layout.addLayout(form_layout)

        layout.addWidget(self.send_enter_button)  # 确认升级

        layout.addWidget(self.progress_bar)  # 新增进度条

        layout.addWidget(self.received_data_label)
        layout.addWidget(self.received_data_display)  # 添加文本显示框

        container = QWidget()
        container.setLayout(layout)

        self.setCentralWidget(container)

        # 并发接收数据的定时器
        self.timer = None
        self.serial = None  # 保存串口对象

    def toggle_port(self):
        # 开启一个新线程来接收串口数据

        if self.serial and self.serial.is_open:  # 检查串口是否已打开
            self.serial.close()  # 关闭串口
            self.open_button.setText("打开串口")  # 修改按钮文本为"打开串口"
            QMessageBox.information(self, "信息", "串口已关闭")
        else:
            selected_port = self.port_input.currentText()
            selected_baudrate = self.baudrate_input.currentText()
            
            if not selected_port:
                QMessageBox.warning(self, "错误", "请先选择一个串口")
                return

            if not selected_baudrate:
                QMessageBox.warning(self, "错误", "请先选择一个波特率")
                return

            try:
                self.serial = serial.Serial(selected_port, selected_baudrate, timeout=1.2)
                self.open_button.setText("关闭串口")  # 修改按钮文本为"关闭串口"
                QMessageBox.information(self, "信息", f"成功打开串口 {selected_port}，波特率 {selected_baudrate}")
                # 开启一个新线程来接收串口数据
                threading.Thread(target=self.receive_data, daemon=True).start()
            except Exception as e:
                QMessageBox.critical(self, "错误", str(e))

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_received_data(self, data):
        # 在文本框中显示接收到的数据
        self.received_data_display.append(data)  # 在文本框中追加数据

    def send_iap_command(self):
        port = self.port_input.currentText()  # 获取选中的串口
        baudrate = int(self.baudrate_input.currentText())  # 获取选中的波特率

        # 启动一个新的线程来发送命令
        threading.Thread(target=self.send_command, args=(port, baudrate)).start()
        #         # 开启一个新线程来接收串口数据
        # threading.Thread(target=self.receive_data, daemon=True).start()

    def send_command(self, port, baudrate):
        if self.serial and self.serial.is_open:  # 检查串口是否已打开
            # 发送特定的16进制命令
            command = bytearray([0x60, 0xF1, 0x55, 0x55])
            self.serial.write(command)
        # try:
        #     with serial.Serial(port, baudrate, timeout=1) as ser:
        #         # 发送16进制数
        #         hex_data = bytes([0x60, 0xF1, 0x55, 0x55])
        #         ser.write(hex_data)
        #         print("发送16进制数: 0x60 0xF1 0x55 0x55")
        # except Exception as e:
        #     print(f"发生错误: {e}")

    def send_enter_command(self):
        port = self.port_input.currentText()  # 获取选中的串口
        baudrate = int(self.baudrate_input.currentText())  # 获取选中的波特率

        # 启动一个新的线程来发送命令
        threading.Thread(target=self.send_enter_iap_command, args=(port, baudrate)).start()


    def send_enter_iap_command(self, port, baudrate):
        if self.serial and self.serial.is_open:  # 检查串口是否已打开
            self.serial.write(b'1')
            print("发送字符: 1")
        # try:
        #     with serial.Serial(port, baudrate, timeout=1) as ser:
        #         # 发送字符 '1'
        #         ser.write(b'1')
        #         print("发送字符: 1")
        # except Exception as e:
        #     print(f"发生错误: {e}")
        self.send_file()

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
            if self.serial and self.serial.is_open:  # 检查串口是否已打开
                print('port is open!')
            else:
            # y_mode.send(file_path)
                y_mode.open(port, baudrate)  # 使用选择的波特
            # # 计算文件大小
            # total_size = os.path.getsize(file_path)
            # sent_size = 0
            # Progress = 50

            self.update_progress(10)  # 开始发送文件数据
            # print("get_progress=%d",get_progress())
            # sent_size += 10
            # progress = int((sent_size / total_size) * 100)
            # self.update_progress(progress)
            y_mode.send(file_path)


        finally:
            self.update_progress(100)  # 传输完成，更新进度条到100%
            y_mode.close()
            print('File sent successfully!')



    def receive_data(self):
        while True:
            if self.serial.in_waiting > 0:
                data = self.serial.read(self.serial.in_waiting)  # 读取接收到的数据
                self.update_received_data(data.decode('utf-8', errors='ignore'))  # 更新接收到的数据文本框



if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = YModemUI()
    main_window.show()
    sys.exit(app.exec_())
