import asyncio

import usb_cdc

from doge_macro import MessageManager

DEBUG = True

async def usb_client():
    serial = usb_cdc.data
    serial.timeout = 0
    serial.reset_input_buffer()
    stream = asyncio.StreamReader(serial)

    message_manager = MessageManager()
    message_size = message_manager.calcsize()
 
    while True:
        try:
            message = await stream.read(message_size)
            message_manager.read_raw_message(message)
        except Exception as e:
            print("Error: ", e)
            serial.reset_input_buffer()

async def main():
    clients = [asyncio.create_task(usb_client())]
    await asyncio.gather(*clients)

asyncio.run(main())