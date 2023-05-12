import struct
from crc import crc16 as mycrc
from utils import bytes_to_str

def kind_to_bytes(kind):
    return struct.calcsize(kind)


def read_byte_array(arr, desc):
    name, kind, div = desc
    size = kind_to_bytes(kind)
    p = arr[:size]
    re = struct.unpack(kind, p)
    del arr[:size]
    val = re[0]
    assert len(re) == 1
    if div != 0:
        val = val/div
    return val

def make_selective_req(num=51, extra=None):
    # extra = [0xff, 0xff, 0xff, 0xff]
    if extra is not None:
        ba = [num] + extra
    else:
        ba = [num]
    package = bytearray(ba)
    crc = mycrc(package)
    crc_b = struct.pack('>H', crc)
    size = len(package)
    arr = bytearray([0x02, size])+ package + crc_b + bytearray([0x03])
    res = bytearray(arr)
    return res

def make_current_req(v):
    # extra = [0xff, 0xff, 0xff, 0xff]
    num = 6
    value = v * 1e3
    value_int = struct.pack('>i', int(value))
    package = bytearray([num]) + value_int
    crc = mycrc(package)
    crc_b = struct.pack('>H', crc)
    size = len(package)
    arr = bytearray([0x02, size])+ package + crc_b + bytearray([0x03])
    res = bytearray(arr)
    return res

def unpack(packet, fields):
    start_byte = packet.pop(0)
    #http://vedder.se/2015/10/communicating-with-the-vesc-using-uart/
    print("The start byte is:")
    print(start_byte)
    if start_byte == 0x2:
        packet_length = packet.pop(0)
    elif start_byte != 0x2:
        lenb = packet[:2]
        del packet[:2]
        packet_length = int.from_bytes(lenb,"big")

    print("Packet length is:", packet_length)
    packet_data = packet[:packet_length+3]
    del packet[:packet_length+3]
    print(bytes_to_str(packet_data))
    stopbyte = packet_data.pop(-1)
    crc = packet_data[-2:]
    # crc2 = crc_checker.calc(packet_data)
    del packet_data[-2:]
    crc2 = mycrc(packet_data)

    rec_crc = int.from_bytes(crc, "big")
    print("CRC CRC CRC", crc2)
    print("Rec CRC", rec_crc)
    print("STOPBYTE", stopbyte)
    print("Byte array length:", len(packet_data))
    result = {}
    fields2 = fields
    # fields2 = GetValues.fields
    usemask = False
    mask = 0

    packet_id = read_byte_array(packet_data, ('packet_id', 'B', 0))
    print("PACKET ID", packet_id)
    if packet_id != 51:
        return {}

    mask = read_byte_array(packet_data, ('mask', '>I', 0))
    print("MASK", bin(mask))
    for i, (name, kind, div) in enumerate(fields2):
        if (mask & (1 << i)):
            no_bytes = kind_to_bytes(kind)
            print("Dropping {} btyes".format(no_bytes), "bytes left", len(packet_data))
            data = read_byte_array(packet_data, (name, kind, div))
            result[name] = data

    if 'bat_lev' in result:
        print()
        print()
        print()
        print()
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print()
        print()
        print()
        print()
    print("BYTES LEFT TO READ:", len(packet_data))
    return result
