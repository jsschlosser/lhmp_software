from pynmeagps import NMEAReader
from pynmeagps import latlon2dms, latlon2dmm

with open('GPS.nmea', 'rb') as stream:
    nmr = NMEAReader(stream, nmeaonly=True)
    for (raw_data, msg) in nmr:
        #print(msg)
        #print(msg.msgID)
        if (msg.msgID=="GGA"):
            print(msg.time)
            print(latlon2dms(msg.lat, msg.lon))