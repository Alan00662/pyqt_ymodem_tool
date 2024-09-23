import sys
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import *
from ymodem import YModem
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal, QObject
import os
import tkinter as tk
import time
import threading
import sys
import io

# 重定向标准输出
class TextRedirector(io.StringIO):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def write(self, message):
        self.text_widget.append(message)  # 将输出追加到文本框

    def flush(self):  # 避免警告
        pass

class Worker(QObject):
    # 定义信号用于传递文本
    print_signal = pyqtSignal(str)

class YModemUI(QMainWindow):


    def __init__(self):
        super().__init__()

        self.setWindowTitle("YModem 串口升级工具")
        self.setWindowIcon(QIcon('logo.ico'))  # 设置窗口图标不是打包生成的图标，确保文件名正确
        self.resize(400, 400)

        self.initUI()
    def initUI(self):
            # 线程锁
        self.lock = threading.Lock()

        layout = QVBoxLayout()

        form_layout = QFormLayout()

        self.port_label = QLabel('选择串口号:')
        self.port_input = QComboBox()  # 使用 QComboBox 替换 QLineEdit
        self.populate_ports()  # 填充可用串口

        self.baudrate_label = QLabel('选择设备:')
        self.baudrate_input = QComboBox()  # 创建波特率下拉框
        self.baudrate_input.addItems(['GPS_Sensor', 'GX12_Hall'])  # 添加可选波特率


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
        self.received_data_label = QLabel('调试信息:')
        self.received_data_display = QTextEdit()
        self.received_data_display.setReadOnly(True)  # 设置为只读

        port_layout = QHBoxLayout()
        port_layout.addWidget(self.port_input)
        form_layout.addRow(self.port_label, port_layout)

        layout.addLayout(form_layout)

        baudrate_layout = QHBoxLayout()
        baudrate_layout.addWidget(self.baudrate_input)
        form_layout.addRow(self.baudrate_label, baudrate_layout)

        layout.addWidget(self.send_iap_button)  # 添加IAP升级命令按钮

        # 添加文件选择框
        file_layout = QHBoxLayout()
        file_layout.addWidget(self.file_input)
        file_layout.addWidget(self.browse_button)

        form_layout.addRow(self.file_label, file_layout)

        layout.addWidget(self.send_enter_button)  # 确认升级

        layout.addWidget(self.received_data_label)
        layout.addWidget(self.received_data_display)  # 添加文本显示框

        # 重定向标准输出
        sys.stdout = TextRedirector(self.received_data_display)
        # 创建工作线程
        self.worker = Worker()
        self.worker.print_signal.connect(self.update_text)  # 连接信号到槽

        container = QWidget()
        container.setLayout(layout)

        self.setCentralWidget(container)

        # 并发接收数据的定时器
        self.timer = None
        self.serial = None  # 保存串口对象

    def update_text(self, message):
        # 更新文本框
        self.received_data_display.append(message)

    def send_iap_command(self):
        port = self.port_input.currentText()  # 获取选中的串口
        switch = self.baudrate_input.currentText()  # 获取选中的波特率
        if switch == 'GPS_Sensor':
            baudrate = 420000
        elif switch == 'GX12_Hall':
            baudrate = 921600
        else:
            baudrate = 115200

        # 启动一个新的线程来发送命令
        threading.Thread(target=self.send_command, args=(port, baudrate)).start()

    def send_command(self, port, baudrate):
        with self.lock:  # 确保在一个时刻只有一个线程使用串口
            try:
                with serial.Serial(port, baudrate, timeout=1) as ser:
                    if baudrate == 921600:  # GX12_Hall需要先发送 'serialpassthrough gimbals 921600' 指令        
                        if self.stop_pulses(ser):  # 发送 'set pulses 0' 指令到串口，直到成功接收到 'set: pulses stop'
                            if self.passthrough(ser):  # 发送 'serialpassthrough gimbals 921600' 指令到串口，直到成功接收到相同的回应
                                # 发送 'iap upgrade' 指令到串口
                                hex_data = bytes([0x60, 0xF1, 0x55, 0x55])
                                ser.write(hex_data)
                                print("The IAP upgrade command was sent successfully!")
                            else:
                                print("Failed to execute passthrough command.")
                        else:
                            print("Failed to stop pulses.")
                    else:
                            # 发送 'iap upgrade' 指令到串口
                            # 发送16进制数
                            hex_data = bytes([0x60, 0xF1, 0x55, 0x55])
                            ser.write(hex_data)
                            print("The IAP upgrade command was sent successfully!")
            except Exception as e:
                print(f"发生错误: {e}")

    def send_enter_command(self):
        port = self.port_input.currentText()  # 获取选中的串口
        # baudrate = int(self.baudrate_input.currentText())  # 获取选中的波特率
        switch = self.baudrate_input.currentText()  # 获取选中的波特率
        if switch == 'GPS_Sensor':
            baudrate = 420000
        elif switch == 'GX12_Hall':
            baudrate = 921600
        else:
            baudrate = 115200

        # 启动一个新的线程来发送确认升级命令
        threading.Thread(target=self.send_enter_iap_command, args=(port, baudrate)).start()


    def send_enter_iap_command(self, port, baudrate):
        try:
            with serial.Serial(port, baudrate, timeout=1) as ser:
                # 发送字符 '1'
                ser.write(b'1')
                print("starting upgrade...")
        except Exception as e:
            print(f"发生错误: {e}")

        threading.Thread(target=self.send_file, args=(port, baudrate)).start()

    def populate_ports(self):
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_input.addItem(port.device)  # 将可用串口添加到下拉框

    def browse_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, 'Select File', '', 'All Files (*)')
        if file_name:
            self.file_input.setText(file_name)

    def send_file(self,port, baudrate):

        file_path = self.file_input.text()

        print(f"baudrate is {baudrate}")

        if not file_path:
            print('Please select a file to send.')
            return

        y_mode = YModem()
        try:
            y_mode.open(port, baudrate)  # 使用选择的波特
            y_mode.send(file_path)

        finally:
            y_mode.close()
            print('File sent successfully!')

    # stop_pulses 模块
    def stop_pulses(self, ser):
        '''发送 'set pulses 0' 指令到串口，直到成功接收到 'set: pulses stop'，最多重试 100 次'''
        command = "set pulses 0\r\n"
        expected_response = "set: pulses stop"
        for attempt in range(25):
            # self.connection.write(command.encode())

            ser.write(command.encode())
            print(command)
            time.sleep(0.2)  # 等待回应
            response = self.read_serial_response(ser, expected_response)  # 使用封装的方法读取响应
            if response:
                return True
            print(f"Retry {attempt + 1}: Did not receive expected response, retrying...")
        print("Can not stop pulses.")

        return False  # 失败

    # passthrough 模块
    def passthrough(self, ser):
        '''发送 'serialpassthrough gimbals 921600' 指令到串口，直到成功接收到相同的回应，最多重试 100 次'''
        command = "serialpassthrough gimbals 921600\r\n"
        expected_response = "> serialpassthrough gimbals 921600"
    
        for attempt in range(25):
            # self.connection.write(command.encode())

            ser.write(command.encode())
            print(command)
            time.sleep(0.2)  # 等待回应
            response = self.read_serial_response(ser, expected_response)  # 使用封装的方法读取响应
            if response:
                return True
            print(f"Retry {attempt + 1}: Did not receive expected response, retrying...")
        print("Can not into passthrough mode.")

        return False  
            

    def read_serial_response(self,ser, expected_response, timeout=1):
        """读取串口数据直到得到预期回复或超时。"""
        start_time = time.time()
        response = ""

        while True:
            if ( time.time() - start_time ) > timeout:
                print("读取超时！")
                return None  # 超时处理
            
            if ser.in_waiting > 0:
                response = ser.readline().decode().strip()
                print(response)  # 打印串口收到的数据
                if response == expected_response:
                    return response  # 返回预期的回复
                else:
                    print("is not expected_response")
        return None  # 返回None表示没有收到预期回复

    def passthrough_test(self, port, baudrate):
        with serial.Serial(port, baudrate, timeout=1) as ser:
            command1 = "set pulses 0\r\n"
            command2 = "serialpassthrough gimbals 921600\r\n"
            ser.write(command1.encode())
            print(command1)
            time.sleep(0.5)  # 等待回应
            ser.write(command2.encode())
            print(command2)
            time.sleep(0.5)  # 等待回应
            hex_data = bytes([0x60, 0xF1, 0x55, 0x55])
            ser.write(hex_data)
            print("The IAP upgrade command was sent successfully!")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = YModemUI()
    main_window.show()
    sys.exit(app.exec_())
