from pygame.time import Clock
import json

from graphics import Tia
# from cpu import Core
from optimized_cpu import Core
from memory import Memory
import controllers


class Settings:
    def __init__(self):
        from os.path import dirname, isfile, exists

        self.path = dirname(__file__) + "/"
        if not isfile(self.path + "settings.json"):
            with open(self.path + "settings.json", "w") as f:
                data = {
                    "key-binds": {
                        "joystick up":              "K_UP",
                        "joystick down":            "K_DOWN",
                        "joystick left":            "K_LEFT",
                        "joystick right":           "K_RIGHT",
                        "controller fire":          "K_a",
                        "select":                   "K_s",
                        "reset":                    "K_r",
                        "difficulty 1 toggle":      "K_1",
                        "difficulty 2 toggle":      "K_2",
                        "black and white toggle":   "K_b"
                    },
                    "roms": []
                }
                json.dump(data, f, indent=4)
        self.file = json.load(open(self.path + "settings.json"))
        roms = self.file["roms"]

        self.rom_super_chip = ""
        self.rom_bank_switching = ""

        if len(roms) == 0:
            print("No ROM files found...")
            while 1:
                self.rom_filepath = input("Input rom filepath: ").strip()
                if exists(self.rom_filepath):
                    self.add_new_rom()
                    break
                else:
                    print("Invalid path")
        else:
            for i in range(len(roms)):
                print(f"{i + 1}. {roms[i]['file']}")
            while 1:
                x = input("Select number or input rom filepath: ").strip()
                try:
                    if int(x) in range(1, len(roms) + 1):
                        rom = roms[int(x) - 1]
                        self.rom_filepath = rom["file"]
                        self.rom_super_chip = rom["super-chip"]
                        self.rom_bank_switching = rom["bank-switching"]
                        break
                    else:
                        print("Number out of range")
                except ValueError:
                    if exists(x):
                        self.rom_filepath = x
                        self.add_new_rom()
                        break
                    else:
                        print("Invalid number or path")

        keys = self.file["key-binds"]
        import pygame.locals as pygame_locals
        self.up_key = pygame_locals.__dict__[keys["joystick up"]]
        self.down_key = pygame_locals.__dict__[keys["joystick down"]]
        self.left_key = pygame_locals.__dict__[keys["joystick left"]]
        self.right_key = pygame_locals.__dict__[keys["joystick right"]]
        self.fire_key = pygame_locals.__dict__[keys["controller fire"]]

        self.select_key = pygame_locals.__dict__[keys["select"]]
        self.reset_key = pygame_locals.__dict__[keys["reset"]]
        self.diff1_key = pygame_locals.__dict__[keys["difficulty 1 toggle"]]
        self.diff2_key = pygame_locals.__dict__[keys["difficulty 2 toggle"]]
        self.color_key = pygame_locals.__dict__[keys["black and white toggle"]]

    def add_new_rom(self):
        for rom in self.file["roms"]:
            if self.rom_filepath == rom["file"]:
                return
        while 1:
            x = input("would you like to add this new rom to your list? (y/n): ")
            if x == "y":
                self.file["roms"].append(
                    {
                        "file": self.rom_filepath,
                        "bank-switching": "",
                        "super-chip": ""
                    }
                )
                with open(self.path + "settings.json", "w") as f:
                    json.dump(self.file, f, indent=4)
                return
            elif x == "n":
                return


class Timer:
    def __init__(self):
        # time is cycles of TIA
        # 3 TIA cycles = 1 CPU cycle
        self.time = 0
        self.tia_last_update = 0
        self.riot_last_update = 0

        self.riot_timer = 0
        self.riot_interval_timer = 0
        self.riot_interval = 1024
        self.riot_status = 0

        self.frame_done = False

    # def add_tia_cycles(self, value):
    #     self.time += value

    def w_sync(self):
        t = 228 - (self.time % 228)
        if t >= 228:
            return
        self.time += t

    def update_riot_timer(self):
        t = (self.time - self.riot_last_update) // 3

        if self.riot_interval == 1:
            self.riot_timer -= t
            if self.riot_timer < 0:
                self.riot_status = 0xc0
                self.riot_timer &= 0xFF
        else:
            self.riot_interval_timer += t
            if self.riot_interval_timer >= self.riot_interval:
                self.riot_timer -= self.riot_interval_timer // self.riot_interval
                self.riot_interval_timer %= self.riot_interval
                if self.riot_timer < 0:
                    self.riot_interval = 1
                    self.riot_status = 0xc0
                    self.riot_timer &= 0xFF

        self.riot_last_update = self.time

    def r_sync(self):
        pass  # TODO

    def set_riot_timer(self, value, interval):
        self.riot_timer = value
        self.riot_interval = interval
        self.riot_interval_timer = interval - 1
        self.riot_status &= 0x40


class Atari2600:
    def __init__(self):
        self.settings = Settings()
        self.timer = Timer()
        self.controller = controllers.Joystick(self.settings)
        # self.controller = controllers.Paddles(self.settings)
        # self.controller = controllers.Keypad(self.settings)

        self.tia = Tia(self.timer, self.controller)
        self.memory = Memory(self.timer, self.controller, self.tia, self.settings)
        self.cpu = Core(self.timer, self.memory)

    def run_loop(self, cpu_func):
        self.tia.init()
        frames = 0
        clock = Clock()
        while clock.tick(60):
            cpu_func()
            self.timer.frame_done = False
            frames += 1
            if frames == 60:
                print(clock.get_fps())
                frames = 0

    def power_on(self):
        self.run_loop(self.cpu.step)

    def debug_power_on(self):
        self.run_loop(self.cpu.debug_step)

    def profile(self):
        from time import time

        # self.tia.init()
        t = time()
        for i in range(100_000_000):
            self.cpu.set_n_and_z(i & 0xFF)
        print(time() - t)


if __name__ == "__main__":
    atari = Atari2600()

    atari.power_on()
    # atari.debug_power_on()
    # atari.profile()
