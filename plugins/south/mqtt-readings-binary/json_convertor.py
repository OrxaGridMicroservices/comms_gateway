import json

# Define your data structure
struct_format = (
                '<'     # Little-endian specifier
                '8B'    # 8 bytes for digital data (DigitalData)
                'B B B B B B H'  # Timestamp components: seconds, minutes, hours, weekday, date, month, year
                '?'     # Boolean for IsNlf
            )

field_names = [
    "DigitalData1", "DigitalData2", "DigitalData3", "DigitalData4",
    "DigitalData5", "DigitalData6", "DigitalData7", "DigitalData8",
    "seconds", "minutes", "hours", "weekday", "date", "month", "year",
    "IsNlf"
]

# Combine the format and field names into a dictionary
data = {
    "struct_format": struct_format,
    "field_names": field_names
}

# Write the dictionary to a JSON file
with open('dds.json', 'w') as json_file:
    json.dump(data, json_file, indent=4)
