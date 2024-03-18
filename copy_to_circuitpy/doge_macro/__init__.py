import struct

import usb_hid

from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.mouse import Mouse

keyboard = Keyboard(usb_hid.devices)
layout = KeyboardLayoutUS(keyboard)
mouse = Mouse(usb_hid.devices)

MAX_PAGE_COUNT = 100

class Device:
    KEYBOARD = 250
    MOUSE = 224
    CONSUMER_CONTROL = 188

class KeyboardAction:
    TYPE = 0
    PRESS = 1
    RELEASE = 2
    RELEASE_ALL = 3
    SEND = 4

class MouseAction:
    CLICK = 0
    MOVE = 1
    PRESS = 2
    RELEASE = 3
    RELEASE_ALL = 4

class MessageManager:
    format = ">BBBBBBBB"
    
    command_mode = True

    page_count = 0
    buffer_queued = []

    paged_messages = [
        (Device.KEYBOARD, KeyboardAction.TYPE)
    ]

    def calcsize(self):
        return struct.calcsize(self.format)

    def read_raw_message(self, message):
        payload = struct.unpack(self.format, message)

        if not self.command_mode:
            current_page = payload[0]
            
            if current_page < MAX_PAGE_COUNT:
                self.buffer_queued.append(message)

                # Process if any of the following is True:
                # - size of buffer_queue is already equal to the page_count + 1 (header)
                # - current_page is equal to page_count - 1
                if (len(self.buffer_queued) == self.page_count + 1) or (current_page == self.page_count - 1):
                    self.process_message(messages=self.buffer_queued)
                    self.command_mode = True
                    self.page_count = 0
                    self.buffer_queued = []

                return

            # If the message is too long, consider the message as corrupted. Move on
            self.command_mode = True
            self.page_count = 0
            self.buffer_queued = []
            return

        device = payload[0]
        action = payload[1]
    
        if (device, action) in self.paged_messages and payload[2] > 0:
            self.buffer_queued.append(message)
            self.page_count = payload[2]
            self.command_mode = False
            return

        if device in (Device.KEYBOARD, Device.MOUSE, Device.CONSUMER_CONTROL):
            self.process_message(messages=[message], device=device, action=action)

    def process_message(self, messages, device=None, action=None):
        header_message = messages[0]
        tail_message = messages[1:]
        print(messages)

        if device == None or action == None:
            payload = struct.unpack(self.format, header_message)
            device = payload[0]
            action = payload[1]

        if device == Device.KEYBOARD:
            if action == KeyboardAction.TYPE:
                KeyboardManager.type(header_message=header_message, tail_message=tail_message)
            elif action == KeyboardAction.PRESS:
                KeyboardManager.send(message=header_message)
            elif action == KeyboardAction.RELEASE:
                KeyboardManager.release(message=header_message)
            elif action == KeyboardAction.RELEASE_ALL:
                KeyboardManager.release_all()
            elif action == KeyboardAction.SEND:
                KeyboardManager.send(message=header_message)

        elif device == Device.MOUSE:
            if action == MouseAction.CLICK:
                MouseManager.click(message=header_message)
            elif action == MouseAction.MOVE:
                MouseManager.move(message=header_message)
            elif action == MouseAction.PRESS:
                MouseManager.press(message=header_message)
            elif action == MouseAction.RELEASE:
                MouseManager.release(message=header_message)
            elif action == MouseAction.RELEASE_ALL:
                MouseManager.release_all()
            pass

        elif device == Device.CONSUMER_CONTROL:
            pass

        return

class KeyboardManager:
    @staticmethod
    def type(header_message, tail_message = None):
        header_payload_format = ">BBB5s"
        tail_payload_format = ">B7s"

        header_payload = struct.unpack(header_payload_format, header_message)
        message_to_type = str(header_payload[3], "utf-8").rstrip('\x00')

        tail_payload = list()
        if tail_message:
            for msg in tail_message:
                tail_payload.append(struct.unpack(tail_payload_format, msg))

        for _, msg in sorted(tail_payload, key=lambda i: i[0]):
            message_to_type += str(msg, "utf-8").rstrip('\x00')

        try:
            layout.write(message_to_type)
        except Exception:
            pass
        
        return

    @staticmethod
    def press(message):
        format = ">BBBBBBBB"

        payload = struct.unpack(format, message)
        keys_to_send = payload[2:]

        try:
            keyboard.press(*keys_to_send)
        except Exception:
            pass
        
        return

    @staticmethod
    def release(message):
        format = ">BBBBBBBB"

        payload = struct.unpack(format, message)
        keys_to_send = payload[2:]

        try:
            keyboard.release(*keys_to_send)
        except Exception:
            pass
        
        return

    @staticmethod
    def release_all():
        try:
            keyboard.release_all()
        except Exception:
            pass
        
        return

    @staticmethod
    def send(message):
        format = ">BBBBBBBB"

        payload = struct.unpack(format, message)
        keys_to_send = payload[2:]

        try:
            keyboard.send(*keys_to_send)
        except Exception:
            pass
        
        return

class MouseManager:
    @staticmethod
    def click(message):
        format = ">BBBBBBBB"
        payload = struct.unpack(format, message)

        try:
            mouse.click(buttons=payload[2])
        except Exception:
            pass
        
        return
        
    @staticmethod
    def move(message):
        format = ">BBhhh"
        payload = struct.unpack(format, message)

        try:
            mouse.move(x=payload[2], y=payload[3], wheel=payload[4])
        except Exception:
            pass
        
        return

    @staticmethod
    def press(message):
        format = ">BBBBBBBB"
        payload = struct.unpack(format, message)

        try:
            mouse.press(buttons=payload[2])
        except Exception:
            pass
        
        return
        
    @staticmethod
    def release(message):
        format = ">BBBBBBBB"
        payload = struct.unpack(format, message)

        try:
            mouse.release(buttons=payload[2])
        except Exception:
            pass
        
        return
        
    @staticmethod
    def release_all():
        try:
            mouse.release_all()
        except Exception:
            pass
        
        return