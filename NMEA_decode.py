import os
from collections import defaultdict
from pynmeagps import NMEAReader

def Run(filename='20260612-09-44-32.nmea', path_to_file='../gps_data'):
    """
    Reads an NMEA file and groups message attributes into arrays over time.
    
    :param filename: The name of the NMEA file to parse.
    :type filename: str
    :param path_to_file: The path to the directory containing the file.
    :type path_to_file: str
    :return: A dictionary where keys are msgIDs, and values are dictionaries of attribute time-series arrays.
    :rtype: dict
    """
    file_path = os.path.join(path_to_file, filename)
    output = defaultdict(lambda: defaultdict(list))# Nested defaultdict: e.g., output['GGA']['lat'] = []
    try:
        with open(file_path, 'rb') as stream:
            nmr = NMEAReader(stream, nmeaonly=True)
            for (raw_data, msg) in nmr:
                if msg is not None and hasattr(msg, 'msgID'):
                    for key in dir(msg):# Iterate through all public attributes of the message
                        if not key.startswith('_') and not callable(getattr(msg, key)):
                            value = getattr(msg, key)
                            output[msg.msgID][key].append(value)# Append the value to the list for this specific attribute
                            
    except FileNotFoundError:
        return {}

    return {msg_id: dict(attributes) for msg_id, attributes in output.items()}# Convert the nested defaultdicts back to standard dictionaries for the output

if __name__ == "__main__":
    Run()