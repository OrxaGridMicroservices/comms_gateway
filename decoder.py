import struct


def binary_debugger(readings: list):
    decoded_readings = []
    parameter_names = [
        "Voltage_PN1", "Voltage_PN2", "Voltage_PN3", "Voltage_PP1", "Voltage_PP2", "Voltage_PP3",
        "Current1", "Current2", "Current3", "NeutralCurrent",
        "Frequency1", "Frequency2", "Frequency3",
        "PowerFactor1", "PowerFactor2", "PowerFactor3", "AveragePF",
        "ActivePower1", "ActivePower2", "ActivePower3",
        "ReactivePower1", "ReactivePower2", "ReactivePower3",
        "ApparentPower1", "ApparentPower2", "ApparentPower3",
        "TotalActivePower", "TotalReactivePower", "TotalApparentPower",
        "AngleVA_VB", "AngleVB_VC", "AngleVA_VC",
        "AngleVA_IA", "AngleVB_IB", "AngleVC_IC", 
        "AngleIA_IB", "AngleIB_IC", "AngleIA_IC",
        "ActiveEnergy1", "ActiveEnergy2", "ActiveEnergy3",
        "ReactiveEnergy1", "ReactiveEnergy2", "ReactiveEnergy3",
        "ApparentEnergy1", "ApparentEnergy2", "ApparentEnergy3",
        "Accum_ActEnergy1", "Accum_ActEnergy2", "Accum_ActEnergy3",
        "Accum_ReactEnergy1", "Accum_ReactEnergy2", "Accum_ReactEnergy3",
        "Accum_ApprntEnergy1", "Accum_ApprntEnergy2", "Accum_ApprntEnergy3",
        "Total_ActEnergy", "Total_ReactEnergy", "Total_ApprntEnergy",
        "Seconds", "Minutes", "Hours", "Weekday", "Date", "Month", "Year", "IsNlf"
    ]
    
    for element in readings:
        # Check the length of the binary data
        print(f"Binary Data Length: {len(element)} bytes")
        
        try:
            decoded_value = struct.unpack('<103f6bH?', element)  
            # Append the decoded values to the list
            decoded_readings.append(dict(zip(parameter_names, decoded_value)))
        except struct.error as e:
            print(f"Error unpacking data: {e}")
    
    return decoded_readings

def main():
    readings = [b'\x93\xe6P?\xd4\x03\x8a=\xa1d)?\xc9(K?\xb1\x9b\x0b?o\x82j>m\xff;?w<\xf0>\x12\x074=M\xcbH?/\xb8H>\xa7D\r=\x0e\xef6?\xad\xa9\x7f>\xc6l:?\x1e\x9fS?\xa0X\xe8>\xc3\x8c\x99>t;\xb4>\xf9do?\x99\x82\xa0>\x9a\xb2\x8b>\x9bj\x96>~\x9eV?Ot\xfb>C\x809?\x8a$\xcb?\xe7Oa?:v\x03@)7\x97C[\x17\x1cC\x81\x91\xbaB\x1fp\x07C\x8cJ$C\xe2\xb1\xaaC\xd2\x05<C\xed\xba+Co3AC\xdc\xa1\xb7>\xbc\xc5~>6\xc4`?>\xfa~?\x84nm?\xb5\xc8a?#iC?\x16\xc3\xf8>=\xf8J>\xd3\xdc\xf2>\x89\x1dU?\xaf\\\xa1>\xf6Hx?\x0b\xb7\xdf>\x87[\xee=-\x81x?\xa2f\n>\xeb\x01\x8c>%\x9d\xcf?\xf6\xf7\xc2?\xe5\x8d\xb0?\xc4\x1da=>K\x96>\xcct\xa2>\x80\xcf\xd6>\x10\xda\x9a=\xe2\x15\xd5>&\xbe1?o\xd5\xd5=f+I?\\\xd6\x1e=<\x06S?\xca5\x84=]\x91+?\xff\xda\x16>lK1>\x19Zn>L\xd3\x12?B\x90\xc7>+\x13I?b\xf1`=\x85\xa0\xbb=\x86\r\x18;g\xa9\x08?\xcc\x8c\x93=3\xa1\x06?\x8c.\xd4>\xf9\x9cN?\x96\x114>i\x00@?\x90\xed\xde>\xc4\xc6+?q\xefg?gb\xc1>\xee\xf7m>\x94\xec"?\xb2$Y?\xae;\xc7>\xc8\xcf\xdf>\x1ejL?\x0c\xb3\xf0>\x8f\x85I>\x96\x02\xcc=[`\xc2>\xe0\xe18?:\x02\x06\x03\x03\x0c\xe8\x07\x00' ,b'\x93\xe6P?\xd4\x03\x8a=\xa1d)?\xc9(K?\xb1\x9b\x0b?o\x82j>m\xff;?w<\xf0>\x12\x074=M\xcbH?/\xb8H>\xa7D\r=\x0e\xef6?\xad\xa9\x7f>\xc6l:?\x1e\x9fS?\xa0X\xe8>\xc3\x8c\x99>t;\xb4>\xf9do?\x99\x82\xa0>\x9a\xb2\x8b>\x9bj\x96>~\x9eV?Ot\xfb>C\x809?\x8a$\xcb?\xe7Oa?:v\x03@)7\x97C[\x17\x1cC\x81\x91\xbaB\x1fp\x07C\x8cJ$C\xe2\xb1\xaaC\xd2\x05<C\xed\xba+Co3AC\xdc\xa1\xb7>\xbc\xc5~>6\xc4`?>\xfa~?\x84nm?\xb5\xc8a?#iC?\x16\xc3\xf8>=\xf8J>\xd3\xdc\xf2>\x89\x1dU?\xaf\\\xa1>\xf6Hx?\x0b\xb7\xdf>\x87[\xee=-\x81x?\xa2f\n>\xeb\x01\x8c>%\x9d\xcf?\xf6\xf7\xc2?\xe5\x8d\xb0?\xc4\x1da=>K\x96>\xcct\xa2>\x80\xcf\xd6>\x10\xda\x9a=\xe2\x15\xd5>&\xbe1?o\xd5\xd5=f+I?\\\xd6\x1e=<\x06S?\xca5\x84=]\x91+?\xff\xda\x16>lK1>\x19Zn>L\xd3\x12?B\x90\xc7>+\x13I?b\xf1`=\x85\xa0\xbb=\x86\r\x18;g\xa9\x08?\xcc\x8c\x93=3\xa1\x06?\x8c.\xd4>\xf9\x9cN?\x96\x114>i\x00@?\x90\xed\xde>\xc4\xc6+?q\xefg?gb\xc1>\xee\xf7m>\x94\xec"?\xb2$Y?\xae;\xc7>\xc8\xcf\xdf>\x1ejL?\x0c\xb3\xf0>\x8f\x85I>\x96\x02\xcc=[`\xc2>\xe0\xe18?:\x02\x06\x03\x03\x0c\xe8\x07\x00']

    decoded_readings = binary_debugger(readings)
    
    print("Decoded Readings:", decoded_readings)

if __name__ == "__main__":
    main()
