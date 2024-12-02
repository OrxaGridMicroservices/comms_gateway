
import struct
def binary_debugger(readings):
    decoded_readings = []
    for element in readings:
        decoded_value = struct.unpack('<6bH', element.encode())  
        decoded_readings.append(decoded_value)
    return decoded_readings

def main():
    print(binary_debugger(["\x19\x3A\x0B\x05\x1A\x09\x07\x00"])) 

if __name__ == "__main__":
    main()
# \x19\x3A\x0B\x05\x1A\x09\x07\x00