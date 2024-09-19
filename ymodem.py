import os
from serial import Serial


class YModem:
    def __init__(self):
        self.ser = None
        self.EOT = b'\x04'
        self.ACK = b'\x06'
        self.NAK = b'\x15'
        self.CAN = b'\x18'
        self.CRC = b'\x43'
        self.ACK_FLAG = False

    @staticmethod
    def crc16(x, invert):
        crc_in = 0x0000
        poly = 0x1021
        for b in x:
            if type(b) is str:  # 这里做了个判断可以直接传入字符串，但存在意义不大
                crc_in ^= (ord(b) << 8)
            else:
                crc_in ^= (b << 8)
            for i in range(8):
                if crc_in & 0x8000:
                    crc_in = (crc_in << 1) ^ poly
                else:
                    crc_in = (crc_in << 1)
        s = hex(crc_in).upper()
        # return (s[-2:], s[-4:-2]) if invert else (s[-4:-2], s[-2:])
        return (s[-2:], s[-4:-2]) if invert else (s[-4:-2], s[-2:])

    @staticmethod
    def str2hex(s):
        i_data = 0
        su = s.upper()
        for c in su:
            tmp = ord(c)
            if tmp <= ord('9'):
                i_data = i_data << 4
                i_data += tmp - ord('0')
            elif ord('A') <= tmp <= ord('F'):
                i_data = i_data << 4
                i_data += tmp - ord('A') + 10
        return i_data

    def open(self, port, baud):
        try:
            self.ser = Serial(port, baud, timeout=1.2)
            print(f'port {port} open ...')
            return True
        except Exception as e:
            print(f'serial {port} is not open {str(e)}')
            return False

    def send_first(self, mode, file_name, file_size):
        if mode == 128:
            x = 1
        else:
            x = 2
        print('start send YModem first package')
        space = bytearray()
        header = bytearray([x, 0, 255])
        file_byte = bytearray([ord(i) for i in file_name])
        size = bytearray([ord(i) for i in str(file_size)])
        for i in range(mode - len(file_byte) - 1 - len(size)):
            space.append(0)
        a1, b1 = self.crc16(file_byte + bytearray([0]) + size + space, False)
        hex_a1 = self.str2hex(a1)
        hex_b1 = self.str2hex(b1)
        last = bytearray([hex_a1, hex_b1])
        data = header + file_byte + bytearray([0]) + size + space + last
        self.ser.write(data)
        print('send first package success')

    def send_data(self, file_data, mode, package_count):
        print('start send file data')
        if mode == 128:
            x = 1
        else:
            x = 2
        for i in range(1, package_count + 1):
            header = bytearray()
            header.append(x)
            header.append(i % 256)
            header.append(255 - (i % 256))
            if i == package_count:
                data = bytearray(file_data[(i - 1) * mode:])
                for j in range(mode - len(data)):
                    data.append(26)
            else:
                data = file_data[(i - 1) * mode: i * mode]
            a1, b1 = self.crc16(data, False)
            hex_a1 = self.str2hex(a1)
            hex_b1 = self.str2hex(b1)
            last = bytearray([hex_a1, hex_b1])
            self.ser.write(header + data + last)
            # 判断ack
            for j in range(10):
                char = self.ser.read(1)
                if char == self.ACK:
                    break
                elif char == self.NAK or j == 9:
                    print('error')
                    return False
                else:
                    continue

        self.ser.write(self.EOT)
        is_ack = self.ser.read(1)
        if is_ack == self.ACK:
            return True
        print('send file data end')

    def send_last(self, mode):
        print('send last data')
        if mode == 128:
            x = 1
        else:
            x = 2
        last_package = bytearray([x, 0, 255])
        for i in range(mode):
            last_package.append(0)
        self.ser.write(last_package)
        self.ser.write(bytearray([0, 0]))
        for i in range(10):
            is_ack = self.ser.read(1)
            if is_ack == self.ACK:
                print('send last ok')
                return True
        print('send last error')
        return False

    def send(self, file_path, mode=128):
        if not os.path.exists(file_path):
            print('file is not found')
            return False
        data_byte = bytes()
        with open(file_path, 'rb') as f:
            for i in f.readlines():
                data_byte += i
        name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        if file_size % mode >= 1:
            package_count = int(file_size / mode) + 1
        else:
            package_count = int(file_size / mode)
        count = 0
        while True:
            count += 1
            if count == 50:
                print('recv char is not crc')
                return False
            char = self.ser.read(1)
            if char == self.CRC:
                print('recv char is crc')
                self.send_first(mode, name, file_size)
                for i in range(30):
                    is_ack = self.ser.read(1)
                    if is_ack == self.ACK:
                        self.ACK_FLAG = True
                        break
                if self.ACK_FLAG:
                    self.send_data(data_byte, mode, package_count)
                    if self.send_last(mode):
                        return True
                    else:
                        print('send data ok but not start app')
            continue

    def close(self):
        self.ser.close()
        self.ser = None


if __name__ == '__main__':
    y_mode = YModem()
    y_mode.open('COM16', 420000)
    y_mode.send(r'.\keil_app.bin')
    y_mode.close()

