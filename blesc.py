import asyncio
import sys
from bleak import BleakScanner, BleakClient
from bleak.backends.scanner import AdvertisementData
from bleak.backends.device import BLEDevice

import logging
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

from utils import bytes_to_str
from messages import make_selective_req, unpack, make_current_req
from fields import COMM_GET_VALUES_SETUP



UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
UART_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
UART_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

    # mServiceUuid = "6e400001-b5a3-f393-e0a9-e50e24dcca9e";
    # mRxUuid = "6e400002-b5a3-f393-e0a9-e50e24dcca9e";
    # mTxUuid = "6e400003-b5a3-f393-e0a9-e50e24dcca9e";

# All BLE devices have MTU of at least 23. Subtracting 3 bytes overhead, we can
# safely send 20 bytes at a time to any device supporting this service.
UART_SAFE_SIZE = 70



all_data = bytearray()


def match_nus_uuid(device: BLEDevice, adv: AdvertisementData):
    if UART_SERVICE_UUID.lower() in adv.service_uuids:
        print(device)
        return True
    return False


def handle_disconnect(_: BleakClient):
    print("Device was disconnected, goodbye.")
    # cancelling all tasks effectively ends the program
    for task in asyncio.all_tasks():
        task.cancel()


def handle_rx(_: int, data: bytearray):
    print("received:", data)
    print("type len:", type(data), len(data))
    global all_data
    all_data += data
    print(len(all_data))
    if len(all_data) > 70:
        logging.info("==ALL data=====")
        logging.info(bytes_to_str(all_data))
        logging.info("===============")
        result = unpack(all_data, COMM_GET_VALUES_SETUP)
        logging.info("Result:", result)
        # (response, consumed) = pyvesc.decode(all_data)
        # logging.info(dir(response))
        # for t in response.fields:
        #     logging.info(t[0], getattr(response, t[0]))
        # logging.info()

async def uart_terminal():
    """

    vb.vbAppendInt8(COMM_SET_CURRENT);
    vb.vbAppendDouble32(current, 1e3);

    l_current_max
    ***This function and whole file was built using this example***
    https://github.com/hbldh/bleak/blob/be97338d2b84968620985f3b401a48dfd7682125/examples/uart_service.py
    """


    device = await BleakScanner.find_device_by_filter(match_nus_uuid)


    async with BleakClient(device, disconnected_callback=handle_disconnect) as client:
        await client.start_notify(UART_TX_CHAR_UUID, handle_rx)
        print("Connected, start typing and press ENTER...")
        loop = asyncio.get_running_loop()
        while True:
            data = await loop.run_in_executor(None, sys.stdin.buffer.readline)
            if not data:
                break
            # some devices, like devices running MicroPython, expect Windows
            # line endings (uncomment line below if needed)
            # data = data.replace(b"\n", b"\r\n")
            # vesc_data = pyvesc.encode(SetRotorPositionMode(SetRotorPositionMode.DISP_POS_MODE_ENCODER))
            # COMM_SET_CURRENT == 6
            # data =  make_selective_req(num=51, extra = [0x00,0x00,0x01,0x00])
            data =  make_current_req(25)
            logging.info("reqdata")
            logging.info(data)
            print()
            await client.write_gatt_char(UART_RX_CHAR_UUID, data)
            str_data = ' '.join(['0x{:02x}'.format(k) for k in data])
            print("sent:", str_data)


if __name__ == "__main__":
    try:
        asyncio.run(uart_terminal())
    except asyncio.CancelledError:
        # task is cancelled on disconnect, so we ignore this error
        pass
