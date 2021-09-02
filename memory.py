class Memory:
    """
    supported bank-switching methods:
    # 8k
    F8
    E0
    FE -- TODO

    # 12k
    FA

    # 16k
    F6
    E7 -- TODO

    # 32k
    F4

    # 64k
    EF -- TODO
    """

    def __init__(self, timer, controller, tia, settings):
        self.controller = controller
        self.timer = timer
        with open(settings.rom_filepath, "rb") as file:
            self.rom = file.read()

        self.rom_size = len(self.rom)

        if settings.rom_super_chip == "yes":
            self.super_chip = True
        elif settings.rom_super_chip == "no":
            self.super_chip = False
        else:
            self.super_chip = False

        self.banks = []
        self.cur_bank = self.rom
        self.read = self.read_4k
        self.write = self.write_other
        self.get_bank_switching_method(settings.rom_bank_switching)

        if self.super_chip:
            print(f"BANKSWITCHING METHOD: {self.read.__name__[-2:]} -- SUPERCHIP ENABLED")
        else:
            print(f"BANKSWITCHING METHOD: {self.read.__name__[-2:]}")

        if self.super_chip:
            self.sc_ram = [0] * 128
        elif self.rom_size == 12288:  # fa method
            self.sc_ram = [0] * 256

        self.rom_reset_vector = self.read2(0xFFFC)
        self.rom_break_vector = self.read2(0xFFFE)

        self.ram = [0] * 128
        self.tia = tia

        self.time_multiple = 1

        self.input_a_mask = 0x0
        self.input_b_mask = 0x0

    def get_bank_switching_method(self, settings_value):
        # sets the rom type based on size and config
        # functions are (read/write)_(file size)_(bank-switching scheme)
        if settings_value != "":
            # 2k
            if settings_value == "2k":
                self.read = self.read_2k
            # 4k
            elif settings_value == "4k":
                pass  # default
            # 8k
            elif settings_value == "f8":
                self.set_banks(self.read_8k_f8, self.write_8k_f8)
            elif settings_value == "e0":
                self.set_banks(self.read_8k_e0, self.write_8k_e0, bank_size=1024)
                self.rom = self.banks[0] + self.banks[0] + self.banks[0] + self.banks[7]
            # 12k
            elif settings_value == "fa":
                self.set_banks(self.read_12k_fa, self.write_12k_fa)
            # 16k
            elif settings_value == "f6":
                self.set_banks(self.read_16k_f6, self.write_16k_f6)
            # 32k
            elif settings_value == "f4":
                self.set_banks(self.read_32k_f4, self.write_32k_f4)
            # 64k
            elif settings_value == "ef":
                self.set_banks(self.read_64k_ef, self.write_64k_ef)
            # unknown
            else:
                print("unknown bank-switching method set in settings, defaulting to guessing")
                self.get_bank_switching_method("")
        else:
            # unknown method, guess based on size
            if self.rom_size == 2048:
                self.read = self.read_2k
            elif self.rom_size == 4096:
                pass  # default
            elif self.rom_size == 8192:
                self.set_banks(self.read_8k_f8, self.write_8k_f8)
            elif self.rom_size == 12288:
                self.set_banks(self.read_12k_fa, self.write_12k_fa)
            elif self.rom_size == 16384:
                self.set_banks(self.read_16k_f6, self.write_16k_f6)
            elif self.rom_size == 32768:
                self.set_banks(self.read_32k_f4, self.write_32k_f4)
            elif self.rom_size == 65536:
                self.set_banks(self.read_64k_ef, self.write_64k_ef)
            else:
                print("unsupported rom size - probably not going to work")

    def set_banks(self, read_func, write_func, bank_size=4096):
        for i in range(self.rom_size // bank_size):
            self.banks.append(self.rom[i * bank_size: (i + 1) * bank_size])
        self.cur_bank = self.banks[0]
        self.read = read_func
        self.write = write_func

    def swap_slice(self, old, new, size):
        self.rom = self.rom[:(old - 0) * size] + self.banks[new] + self.rom[(old + 1) * size:]

    def read_other(self, address):
        if address & 0x200:  # RIOT registers
            address &= 0x7F
            if address == 0x0:  # input_a
                return self.controller.input_a & ~self.input_a_mask
            elif address == 0x1:
                return self.input_a_mask
            elif address == 0x2:  # input_b
                return self.controller.input_b & ~self.input_b_mask
            elif address == 0x3:
                return self.input_b_mask
            elif address == 0x4 or address == 0x6:  # timer output
                self.timer.update_riot_timer()
                self.timer.riot_status &= ~0x80
                return self.timer.riot_timer
            elif address == 0x5 or address == 0x7:  # timer interrupt
                self.timer.update_riot_timer()
                tmp = self.timer.riot_status
                self.timer.riot_status &= ~0x40
                return tmp
            return 0
        elif address & 0x80:  # RAM
            return self.ram[address & 0x7F]
        else:  # TIA registers
            return self.tia.read(address)

    def write_other(self, address, value):
        if address & 0x200:  # RIOT registers
            address &= 0x7f
            if address == 0x0:  # write to input_a
                print(value)
            elif address == 0x1:  # input_a DDR
                self.input_a_mask = value
            elif address == 0x14:  # Tim1t
                self.timer.update_riot_timer()
                self.timer.set_riot_timer(value, 1)
            elif address == 0x15:  # Tim8t
                self.timer.update_riot_timer()
                self.timer.set_riot_timer(value, 8)
            elif address == 0x16:  # Tim64t
                self.timer.update_riot_timer()
                self.timer.set_riot_timer(value, 64)
            elif address == 0x17:  # T1024t
                self.timer.update_riot_timer()
                self.timer.set_riot_timer(value, 1024)
        elif address & 0x80:  # RAM
            self.ram[address & 0x7F] = value
        else:  # TIA registers
            try:
                self.tia.write_table[address](value)
            except KeyError:
                pass

    def read2(self, address):
        return self.read(address) + (self.read(address + 1) << 8)

    def read_2k(self, address):
        if address & 0x1000:
            return self.cur_bank[address & 0x7FF]
        else:
            return self.read_other(address)

    def read_4k(self, address):
        if address & 0x1000:
            return self.cur_bank[address & 0xFFF]
        else:
            return self.read_other(address)

    def read_8k_f8(self, address):
        if address & 0x1000:
            address &= 0xFFF
            if address == 0xFF8:
                self.cur_bank = self.banks[0]
            elif address == 0xFF9:
                self.cur_bank = self.banks[1]
            return self.cur_bank[address]
        else:
            return self.read_other(address)

    def write_8k_f8(self, address, value):
        if address & 0x1000:
            address &= 0xFFF
            if address == 0xFF8:
                self.cur_bank = self.banks[0]
            elif address == 0xFF9:
                self.cur_bank = self.banks[1]
        else:
            self.write_other(address, value)

    def read_8k_e0(self, address):
        if address & 0x1000:
            address &= 0xFFF
            if address & 0xFF8 == 0xFE0:
                self.swap_slice(0, address & 0x7, 1024)
            elif address & 0xFF8 == 0xFE8:
                self.swap_slice(1, address & 0x7, 1024)
            elif address & 0xFF8 == 0xFF0:
                self.swap_slice(2, address & 0x7, 1024)
            return self.rom[address]
        else:
            return self.read_other(address)

    def write_8k_e0(self, address, value):
        if address & 0x1000:
            address &= 0xFFF
            if address & 0xFF8 == 0xFE0:
                self.swap_slice(0, address & 0x7, 1024)
            elif address & 0xFF8 == 0xFE8:
                self.swap_slice(1, address & 0x7, 1024)
            elif address & 0xFF8 == 0xFF0:
                self.swap_slice(2, address & 0x7, 1024)
        else:
            self.write_other(address, value)

    def read_12k_fa(self, address):
        if address & 0x1000:
            address &= 0xFFF
            if address & 0xF00 == 0x100:
                return self.sc_ram[address & 0xFF]
            if address == 0xFF8:
                self.cur_bank = self.banks[0]
            elif address == 0xFF9:
                self.cur_bank = self.banks[1]
            elif address == 0xFFA:
                self.cur_bank = self.banks[2]
            return self.cur_bank[address]
        else:
            return self.read_other(address)

    def write_12k_fa(self, address, value):
        if address & 0x1000:
            address &= 0xFFF
            if address & 0xF00 == 0:
                self.sc_ram[address & 0xFF] = value
            if address == 0xFF8:
                self.cur_bank = self.banks[0]
            elif address == 0xFF9:
                self.cur_bank = self.banks[1]
            elif address == 0xFFA:
                self.cur_bank = self.banks[2]
        else:
            self.write_other(address, value)

    def read_16k_f6(self, address):
        if address & 0x1000:
            address &= 0xFFF
            if self.super_chip:
                if address & 0xF80 == 0x80:
                    return self.sc_ram[address & 0x7F]
            if address == 0xFF6:
                self.cur_bank = self.banks[0]
            elif address == 0xFF7:
                self.cur_bank = self.banks[1]
            elif address == 0xFF8:
                self.cur_bank = self.banks[2]
            elif address == 0xFF9:
                self.cur_bank = self.banks[3]
            return self.cur_bank[address]
        else:
            return self.read_other(address)

    def write_16k_f6(self, address, value):
        if address & 0x1000:
            address &= 0xFFF
            if self.super_chip:
                if address & 0xF80 == 0:
                    self.sc_ram[address & 0x7F] = value
            if address == 0xFF6:
                self.cur_bank = self.banks[0]
            elif address == 0xFF7:
                self.cur_bank = self.banks[1]
            elif address == 0xFF8:
                self.cur_bank = self.banks[2]
            elif address == 0xFF9:
                self.cur_bank = self.banks[3]
        else:
            self.write_other(address, value)

    def read_32k_f4(self, address):
        if address & 0x1000:
            address &= 0xFFF
            if self.super_chip:
                if address & 0xF80 == 0x80:
                    return self.sc_ram[address & 0x7F]
            if address == 0xFF4:
                self.cur_bank = self.banks[0]
            elif address == 0xFF5:
                self.cur_bank = self.banks[1]
            elif address == 0xFF6:
                self.cur_bank = self.banks[2]
            elif address == 0xFF7:
                self.cur_bank = self.banks[3]
            elif address == 0xFF8:
                self.cur_bank = self.banks[4]
            elif address == 0xFF9:
                self.cur_bank = self.banks[5]
            elif address == 0xFFA:
                self.cur_bank = self.banks[6]
            elif address == 0xFFB:
                self.cur_bank = self.banks[7]
            return self.cur_bank[address]
        else:
            return self.read_other(address)

    def write_32k_f4(self, address, value):
        if address & 0x1000:
            address &= 0xFFF
            if self.super_chip:
                if address & 0xF80 == 0:
                    self.sc_ram[address & 0x7F] = value
            if address == 0xFF4:
                self.cur_bank = self.banks[0]
            elif address == 0xFF5:
                self.cur_bank = self.banks[1]
            elif address == 0xFF6:
                self.cur_bank = self.banks[2]
            elif address == 0xFF7:
                self.cur_bank = self.banks[3]
            elif address == 0xFF8:
                self.cur_bank = self.banks[4]
            elif address == 0xFF9:
                self.cur_bank = self.banks[5]
            elif address == 0xFFA:
                self.cur_bank = self.banks[6]
            elif address == 0xFFB:
                self.cur_bank = self.banks[7]
        else:
            self.write_other(address, value)

    def read_64k_ef(self, address):
        if address & 0x1000:
            address &= 0xFFF
            if self.super_chip:
                if address & 0xF80 == 0x80:
                    return self.sc_ram[address & 0x7F]
            if 0xFE0 <= address <= 0xFEF:
                self.cur_bank = self.banks[address - 0xFE0]
            return self.cur_bank[address]
        else:
            return self.read_other(address)

    def write_64k_ef(self, address, value):
        if address & 0x1000:
            address &= 0xFFF
            if self.super_chip:
                if address & 0xF80 == 0:
                    self.sc_ram[address & 0x7F] = value
            if 0xFE0 >= address <= 0xFEF:
                self.cur_bank = self.banks[address - 0xFE0]
        else:
            self.write_other(address, value)
