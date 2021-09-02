from pygame.locals import *


class Controller:
    def __init__(self, settings):
        self.settings = settings

        # riot input registers
        self.input_a = 0xFF
        self.input_b = 0x3F  # easy difficulty
        # self.input_b = 0xFF  # hard difficulty

        # tia input registers
        self.input0 = 0
        self.input1 = 0
        self.input2 = 0
        self.input3 = 0
        self.input4 = 0x80
        self.input5 = 0x80

    def process_events(self, events):
        self.process_console_switches(events)

    def process_console_switches(self, events):
        for event in events:
            if event.type == QUIT:
                exit()
            if event.type == KEYDOWN:
                # button switches
                if event.key == self.settings.reset_key:
                    self.input_b &= ~0x1
                elif event.key == self.settings.select_key:
                    self.input_b &= ~0x2
                # toggle switches
                elif event.key == self.settings.color_key:
                    self.input_b ^= 0x8
                    if self.input_b & 0x8:
                        print("Color Mode")
                    else:
                        print("Black and White Mode")
                elif event.key == self.settings.diff1_key:  # P0 difficulty switch
                    self.input_b ^= 0x40
                    if self.input_b & 0x40:
                        print("Left Difficulty Switch: (A)dvanced")
                    else:
                        print("Left Difficulty Switch: (B)eginner")
                elif event.key == self.settings.diff2_key:  # P1 difficulty switch
                    self.input_b ^= 0x80
                    if self.input_b & 0x80:
                        print("Right Difficulty Switch: (A)dvanced")
                    else:
                        print("Right Difficulty Switch: (B)eginner")

            elif event.type == KEYUP:
                # switches
                if event.key == self.settings.reset_key:
                    self.input_b |= 0x1
                elif event.key == self.settings.select_key:
                    self.input_b |= 0x2


class Joystick(Controller):
    def __init__(self, settings):
        super().__init__(settings)

    def process_events(self, events):
        self.process_console_switches(events)
        for event in events:
            if event.type == KEYDOWN:
                if event.key == self.settings.up_key:
                    self.input_a &= ~0x10
                elif event.key == self.settings.down_key:
                    self.input_a &= ~0x20
                elif event.key == self.settings.left_key:
                    self.input_a &= ~0x40
                elif event.key == self.settings.right_key:
                    self.input_a &= ~0x80
                elif event.key == self.settings.fire_key:
                    self.input4 &= ~0x80

            elif event.type == KEYUP:
                if event.key == self.settings.up_key:
                    self.input_a |= 0x10
                elif event.key == self.settings.down_key:
                    self.input_a |= 0x20
                elif event.key == self.settings.left_key:
                    self.input_a |= 0x40
                elif event.key == self.settings.right_key:
                    self.input_a |= 0x80
                elif event.key == self.settings.fire_key:
                    self.input4 |= 0x80


class Paddles(Controller):
    def __init__(self, settings):
        super().__init__(settings)

    def process_events(self, events):
        self.process_console_switches(events)
        for event in events:
            if event.type == KEYDOWN:
                if event.key == self.settings.left_key:
                    self.input0 = (self.input0 - 5) & 0xFF
                    print(self.input0)
                elif event.key == self.settings.right_key:
                    self.input0 = (self.input0 + 5) & 0xFF
                    print(self.input0)
                elif event.key == self.settings.up_key:
                    self.input0 = 0
                    print(self.input0)
                elif event.key == self.settings.fire_key:
                    self.input_a &= ~0x80

            elif event.type == KEYUP:
                if event.key == self.settings.fire_key:
                    self.input_a |= 0x80


class Keypad(Controller):
    def __init__(self, settings):
        super().__init__(settings)

    def process_events(self, events):
        self.process_console_switches(events)
        for event in events:
            if event.type == KEYDOWN:
                pass
            elif event.type == KEYUP:
                pass
