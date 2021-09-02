class Core:
    def __init__(self, timer, memory):
        self.timer = timer
        self.memory = memory
        self.a = 0  # a Register (8-bit)
        self.x = 0  # x Register (8-bit)
        self.y = 0  # y Register (8-bit)
        self.pc = self.memory.rom_reset_vector  # Program Counter (16-bit)
        self.s = 0xFF  # Stack Pointer (8-bit)

        # processor status (8-bit)
        self.c = 0  # carry
        self.z = 0  # zero
        self.i = 0  # interrupt
        self.d = 0  # decimal
        self.b = 0  # break
        # unused bit here
        self.v = 0  # overflow
        self.n = 0  # negative

        self.opcodes = self.get_opcodes()

    def step(self):
        while not self.timer.frame_done:
            self.opcodes[self.memory.read(self.pc)]()
            self.pc += 1

    # helper functions
    def status_to_int(self):
        out = 0
        status_array = (self.c, self.z, self.i, self.d, self.b, 1, self.v, self.n)
        for i in range(8):
            out += (status_array[i] & 0x1) << i
        return out

    def set_status(self, value):
        self.c = value & 0x1
        self.z = (value >> 1) & 0x1
        self.i = (value >> 2) & 0x1
        self.d = (value >> 3) & 0x1
        self.b = (value >> 4) & 0x1
        # unused bit here
        self.v = (value >> 6) & 0x1
        self.n = (value >> 7) & 0x1

    # Instructions
    def adc_im(self):
        self.timer.time += 6
        self.pc += 1
        value = self.memory.read(self.pc)
        if not self.d:
            r = value + self.a + self.c
            self.v = ~(self.a ^ value) & (self.a ^ r) & 0x80 != 0  # overflow
            self.c = r & 0x100 == 0x100  # carry
            r &= 0xFF
            self.a = r
            self.z = not r
            self.n = r >> 7
        else:
            lo = (self.a & 0x0F) + (value & 0x0F) + self.c
            hi = (self.a & 0xF0) + (value & 0xF0)
            self.z = not ((lo + hi) & 0xFF)
            if lo > 0x09:
                hi += 0x10
                lo += 0x06
            self.n = hi >> 7
            self.v = ~(self.a ^ value) & (self.a ^ hi) & 0x80 != 0
            if hi > 0x90:
                hi += 0x60
            self.c = hi & 0x100 == 0x100

            self.a = (lo & 0x0F) + (hi & 0xF0)

    def adc_zp(self):
        self.timer.time += 9
        self.pc += 1
        value = self.memory.read(self.memory.read(self.pc))
        if not self.d:
            r = value + self.a + self.c
            self.v = ~(self.a ^ value) & (self.a ^ r) & 0x80 != 0  # overflow
            self.c = r & 0x100 == 0x100  # carry
            r &= 0xFF
            self.a = r
            self.z = not r
            self.n = r >> 7
        else:
            lo = (self.a & 0x0F) + (value & 0x0F) + self.c
            hi = (self.a & 0xF0) + (value & 0xF0)
            self.z = not ((lo + hi) & 0xFF)
            if lo > 0x09:
                hi += 0x10
                lo += 0x06
            self.n = hi >> 7
            self.v = ~(self.a ^ value) & (self.a ^ hi) & 0x80 != 0
            if hi > 0x90:
                hi += 0x60
            self.c = hi & 0x100 == 0x100

            self.a = (lo & 0x0F) + (hi & 0xF0)

    def adc_zpx(self):
        self.timer.time += 12
        self.pc += 1
        value = self.memory.read((self.memory.read(self.pc) + self.x) & 0xFF)
        if not self.d:
            r = value + self.a + self.c
            self.v = ~(self.a ^ value) & (self.a ^ r) & 0x80 != 0  # overflow
            self.c = r & 0x100 == 0x100  # carry
            r &= 0xFF
            self.a = r
            self.z = not r
            self.n = r >> 7
        else:
            lo = (self.a & 0x0F) + (value & 0x0F) + self.c
            hi = (self.a & 0xF0) + (value & 0xF0)
            self.z = not ((lo + hi) & 0xFF)
            if lo > 0x09:
                hi += 0x10
                lo += 0x06
            self.n = hi >> 7
            self.v = ~(self.a ^ value) & (self.a ^ hi) & 0x80 != 0
            if hi > 0x90:
                hi += 0x60
            self.c = hi & 0x100 == 0x100

            self.a = (lo & 0x0F) + (hi & 0xF0)

    def adc_ab(self):
        self.timer.time += 12
        self.pc += 2
        value = self.memory.read(self.memory.read2(self.pc - 1))
        if not self.d:
            r = value + self.a + self.c
            self.v = ~(self.a ^ value) & (self.a ^ r) & 0x80 != 0  # overflow
            self.c = r & 0x100 == 0x100  # carry
            r &= 0xFF
            self.a = r
            self.z = not r
            self.n = r >> 7
        else:
            lo = (self.a & 0x0F) + (value & 0x0F) + self.c
            hi = (self.a & 0xF0) + (value & 0xF0)
            self.z = not ((lo + hi) & 0xFF)
            if lo > 0x09:
                hi += 0x10
                lo += 0x06
            self.n = hi >> 7
            self.v = ~(self.a ^ value) & (self.a ^ hi) & 0x80 != 0
            if hi > 0x90:
                hi += 0x60
            self.c = hi & 0x100 == 0x100

            self.a = (lo & 0x0F) + (hi & 0xF0)

    def adc_abx(self):
        self.timer.time += 12
        self.pc += 2
        tmp = self.memory.read2(self.pc - 1)
        tmp2 = (tmp + self.x) & 0xFFFF
        if (tmp & 0xF00) != (tmp2 & 0xF00):
            self.timer.time += 3
        value = self.memory.read(tmp2)
        if not self.d:
            r = value + self.a + self.c
            self.v = ~(self.a ^ value) & (self.a ^ r) & 0x80 != 0  # overflow
            self.c = r & 0x100 == 0x100  # carry
            r &= 0xFF
            self.a = r
            self.z = not r
            self.n = r >> 7
        else:
            lo = (self.a & 0x0F) + (value & 0x0F) + self.c
            hi = (self.a & 0xF0) + (value & 0xF0)
            self.z = not ((lo + hi) & 0xFF)
            if lo > 0x09:
                hi += 0x10
                lo += 0x06
            self.n = hi >> 7
            self.v = ~(self.a ^ value) & (self.a ^ hi) & 0x80 != 0
            if hi > 0x90:
                hi += 0x60
            self.c = hi & 0x100 == 0x100

            self.a = (lo & 0x0F) + (hi & 0xF0)

    def adc_aby(self):
        self.timer.time += 12
        self.pc += 2
        tmp = self.memory.read2(self.pc - 1)
        tmp2 = (tmp + self.y) & 0xFFFF
        if (tmp & 0xF00) != (tmp2 & 0xF00):
            self.timer.time += 3
        value = self.memory.read(tmp2)
        if not self.d:
            r = value + self.a + self.c
            self.v = ~(self.a ^ value) & (self.a ^ r) & 0x80 != 0  # overflow
            self.c = r & 0x100 == 0x100  # carry
            r &= 0xFF
            self.a = r
            self.z = not r
            self.n = r >> 7
        else:
            lo = (self.a & 0x0F) + (value & 0x0F) + self.c
            hi = (self.a & 0xF0) + (value & 0xF0)
            self.z = not ((lo + hi) & 0xFF)
            if lo > 0x09:
                hi += 0x10
                lo += 0x06
            self.n = hi >> 7
            self.v = ~(self.a ^ value) & (self.a ^ hi) & 0x80 != 0
            if hi > 0x90:
                hi += 0x60
            self.c = hi & 0x100 == 0x100

            self.a = (lo & 0x0F) + (hi & 0xF0)

    def adc_inx(self):
        self.timer.time += 18
        self.pc += 1
        value = self.memory.read(self.memory.read2((self.memory.read(self.pc) + self.x) & 0xFF))
        if not self.d:
            r = value + self.a + self.c
            self.v = ~(self.a ^ value) & (self.a ^ r) & 0x80 != 0  # overflow
            self.c = r & 0x100 == 0x100  # carry
            r &= 0xFF
            self.a = r
            self.z = not r
            self.n = r >> 7
        else:
            lo = (self.a & 0x0F) + (value & 0x0F) + self.c
            hi = (self.a & 0xF0) + (value & 0xF0)
            self.z = not ((lo + hi) & 0xFF)
            if lo > 0x09:
                hi += 0x10
                lo += 0x06
            self.n = hi >> 7
            self.v = ~(self.a ^ value) & (self.a ^ hi) & 0x80 != 0
            if hi > 0x90:
                hi += 0x60
            self.c = hi & 0x100 == 0x100

            self.a = (lo & 0x0F) + (hi & 0xF0)

    def adc_iny(self):
        self.timer.time += 15
        self.pc += 1
        tmp = self.memory.read2(self.memory.read(self.pc))
        tmp2 = (tmp + self.y) & 0xFFFF
        if (tmp & 0xF00) != (tmp2 & 0xF00):
            self.timer.time += 3
        value = self.memory.read(tmp2)
        if not self.d:
            r = value + self.a + self.c
            self.v = ~(self.a ^ value) & (self.a ^ r) & 0x80 != 0  # overflow
            self.c = r & 0x100 == 0x100  # carry
            r &= 0xFF
            self.a = r
            self.z = not r
            self.n = r >> 7
        else:
            lo = (self.a & 0x0F) + (value & 0x0F) + self.c
            hi = (self.a & 0xF0) + (value & 0xF0)
            self.z = not ((lo + hi) & 0xFF)
            if lo > 0x09:
                hi += 0x10
                lo += 0x06
            self.n = hi >> 7
            self.v = ~(self.a ^ value) & (self.a ^ hi) & 0x80 != 0
            if hi > 0x90:
                hi += 0x60
            self.c = hi & 0x100 == 0x100

            self.a = (lo & 0x0F) + (hi & 0xF0)

    def and_im(self):
        self.timer.time += 6
        self.pc += 1
        self.a &= self.memory.read(self.pc)
        self.z = not self.a
        self.n = self.a >> 7

    def and_zp(self):
        self.timer.time += 9
        self.pc += 1
        self.a &= self.memory.read(self.memory.read(self.pc))
        self.z = not self.a
        self.n = self.a >> 7

    def and_zpx(self):
        self.timer.time += 12
        self.pc += 1
        self.a &= self.memory.read((self.memory.read(self.pc) + self.x) & 0xFF)
        self.z = not self.a
        self.n = self.a >> 7

    def and_ab(self):
        self.timer.time += 12
        self.pc += 2
        self.a &= self.memory.read(self.memory.read2(self.pc - 1))
        self.z = not self.a
        self.n = self.a >> 7

    def and_abx(self):
        self.timer.time += 12
        self.pc += 2
        tmp = self.memory.read2(self.pc - 1)
        tmp2 = (tmp + self.x) & 0xFFFF
        if (tmp & 0xF00) != (tmp2 & 0xF00):
            self.timer.time += 3
        self.a &= self.memory.read(tmp2)
        self.z = not self.a
        self.n = self.a >> 7

    def and_aby(self):
        self.timer.time += 12
        self.pc += 2
        tmp = self.memory.read2(self.pc - 1)
        tmp2 = (tmp + self.y) & 0xFFFF
        if (tmp & 0xF00) != (tmp2 & 0xF00):
            self.timer.time += 3
        self.a &= self.memory.read(tmp2)
        self.z = not self.a
        self.n = self.a >> 7

    def and_inx(self):
        self.timer.time += 18
        self.pc += 1
        self.a &= self.memory.read(self.memory.read2((self.memory.read(self.pc) + self.x) & 0xFF))
        self.z = not self.a
        self.n = self.a >> 7

    def and_iny(self):
        self.timer.time += 15
        self.pc += 1
        tmp = self.memory.read2(self.memory.read(self.pc))
        tmp2 = (tmp + self.y) & 0xFFFF
        if (tmp & 0xF00) != (tmp2 & 0xF00):
            self.timer.time += 3
        self.a &= self.memory.read(tmp2)
        self.z = not self.a
        self.n = self.a >> 7

    def asl_acc(self):
        self.timer.time += 6
        self.a <<= 1
        self.c = self.a >> 8
        self.a &= 0xFF
        self.z = not self.a
        self.n = self.a >> 7

    def asl_zp(self):
        self.timer.time += 15
        self.pc += 1
        address = self.memory.read(self.pc)
        value = self.memory.read(address) << 1
        self.c = value >> 8
        value &= 0xFF
        self.memory.write(address, value)
        self.z = not value
        self.n = value >> 7

    def asl_zpx(self):
        self.timer.time += 18
        self.pc += 1
        address = (self.memory.read(self.pc) + self.x) & 0xFF
        value = self.memory.read(address) << 1
        self.c = value >> 8
        value &= 0xFF
        self.memory.write(address, value)
        self.z = not value
        self.n = value >> 7

    def asl_ab(self):
        self.timer.time += 18
        self.pc += 2
        address = self.memory.read2(self.pc - 1)
        value = self.memory.read(address) << 1
        self.c = value >> 8
        value &= 0xFF
        self.memory.write(address, value)
        self.z = not value
        self.n = value >> 7

    def asl_abx(self):
        self.timer.time += 21
        self.pc += 2
        address = (self.memory.read2(self.pc - 1) + self.x) & 0xFFFF
        value = self.memory.read(address) << 1
        self.c = value >> 8
        value &= 0xFF
        self.memory.write(address, value)
        self.z = not value
        self.n = value >> 7

    def bit_zp(self):
        self.timer.time += 9
        self.pc += 1
        value = self.memory.read(self.memory.read(self.pc))
        self.n = (value & 0x80) == 0x80
        self.v = (value & 0x40) == 0x40
        self.z = not (self.a & value)

    def bit_ab(self):
        self.timer.time += 12
        self.pc += 2
        value = self.memory.read(self.memory.read2(self.pc - 1))
        self.n = (value & 0x80) == 0x80
        self.v = (value & 0x40) == 0x40
        self.z = not (self.a & value)

    def bcc(self):
        self.timer.time += 6
        self.pc += 1
        if not self.c:
            value = self.memory.read(self.pc)
            if value & 0x80:
                new = self.pc + (value - 0x100)
            else:
                new = self.pc + value

            if (self.pc & 0xF00) != (new & 0xF00):
                self.timer.time += 6
            else:
                self.timer.time += 3
            self.pc = new

    def bcs(self):
        self.timer.time += 6
        self.pc += 1
        if self.c:
            value = self.memory.read(self.pc)
            if value & 0x80:
                new = self.pc + (value - 0x100)
            else:
                new = self.pc + value

            if (self.pc & 0xF00) != (new & 0xF00):
                self.timer.time += 6
            else:
                self.timer.time += 3
            self.pc = new

    def beq(self):
        self.timer.time += 6
        self.pc += 1
        if self.z:
            value = self.memory.read(self.pc)
            if value & 0x80:
                new = self.pc + (value - 0x100)
            else:
                new = self.pc + value

            if (self.pc & 0xF00) != (new & 0xF00):
                self.timer.time += 6
            else:
                self.timer.time += 3
            self.pc = new

    def bmi(self):
        self.timer.time += 6
        self.pc += 1
        if self.n:
            value = self.memory.read(self.pc)
            if value & 0x80:
                new = self.pc + (value - 0x100)
            else:
                new = self.pc + value

            if (self.pc & 0xF00) != (new & 0xF00):
                self.timer.time += 6
            else:
                self.timer.time += 3
            self.pc = new

    def bne(self):
        self.timer.time += 6
        self.pc += 1
        if not self.z:
            value = self.memory.read(self.pc)
            if value & 0x80:
                new = self.pc + (value - 0x100)
            else:
                new = self.pc + value

            if (self.pc & 0xF00) != (new & 0xF00):
                self.timer.time += 6
            else:
                self.timer.time += 3
            self.pc = new

    def bpl(self):
        self.timer.time += 6
        self.pc += 1
        if not self.n:
            value = self.memory.read(self.pc)
            if value & 0x80:
                new = self.pc + (value - 0x100)
            else:
                new = self.pc + value

            if (self.pc & 0xF00) != (new & 0xF00):
                self.timer.time += 6
            else:
                self.timer.time += 3
            self.pc = new

    def bvc(self):
        self.timer.time += 6
        self.pc += 1
        if not self.v:
            value = self.memory.read(self.pc)
            if value & 0x80:
                new = self.pc + (value - 0x100)
            else:
                new = self.pc + value

            if (self.pc & 0xF00) != (new & 0xF00):
                self.timer.time += 6
            else:
                self.timer.time += 3
            self.pc = new

    def bvs(self):
        self.timer.time += 6
        self.pc += 1
        if self.v:
            value = self.memory.read(self.pc)
            if value & 0x80:
                new = self.pc + (value - 0x100)
            else:
                new = self.pc + value

            if (self.pc & 0xF00) != (new & 0xF00):
                self.timer.time += 6
            else:
                self.timer.time += 3
            self.pc = new

    def brk(self):
        self.timer.time += 21
        self.pc += 2
        self.memory.write(self.s, (self.pc >> 8) & 0xFF)
        self.s = (self.s - 1) & 0xFF
        self.memory.write(self.s, self.pc & 0xFF)
        self.s = (self.s - 1) & 0xFF

        self.b = 1
        self.memory.write(self.s, self.status_to_int())
        self.s = (self.s - 1) & 0xFF

        self.i = 1

        self.pc = self.memory.rom_break_vector - 1

    def clc(self):
        self.timer.time += 6
        self.c = 0

    def cld(self):
        self.timer.time += 6
        self.d = 0

    def cli(self):
        self.timer.time += 6
        self.i = 0

    def clv(self):
        self.timer.time += 6
        self.v = 0

    def cmp_im(self):
        self.timer.time += 6
        self.pc += 1
        value = self.a - self.memory.read(self.pc)
        self.c = value >= 0
        value &= 0xFF
        self.z = not value
        self.n = value >> 7

    def cmp_zp(self):
        self.timer.time += 9
        self.pc += 1
        value = self.a - self.memory.read(self.memory.read(self.pc))
        self.c = value >= 0
        value &= 0xFF
        self.z = not value
        self.n = value >> 7

    def cmp_zpx(self):
        self.timer.time += 12
        self.pc += 1
        value = self.a - self.memory.read((self.memory.read(self.pc) + self.x) & 0xFF)
        self.c = value >= 0
        value &= 0xFF
        self.z = not value
        self.n = value >> 7

    def cmp_ab(self):
        self.timer.time += 12
        self.pc += 2
        value = self.a - self.memory.read(self.memory.read2(self.pc - 1))
        self.c = value >= 0
        value &= 0xFF
        self.z = not value
        self.n = value >> 7

    def cmp_abx(self):
        self.timer.time += 12
        self.pc += 2
        tmp = self.memory.read2(self.pc - 1)
        tmp2 = (tmp + self.x) & 0xFFFF
        if (tmp & 0xF00) != (tmp2 & 0xF00):
            self.timer.time += 3
        value = self.a - self.memory.read(tmp2)
        self.c = value >= 0
        value &= 0xFF
        self.z = not value
        self.n = value >> 7

    def cmp_aby(self):
        self.timer.time += 12
        self.pc += 2
        tmp = self.memory.read2(self.pc - 1)
        tmp2 = (tmp + self.y) & 0xFFFF
        if (tmp & 0xF00) != (tmp2 & 0xF00):
            self.timer.time += 3
        value = self.a - self.memory.read(tmp2)
        self.c = value >= 0
        value &= 0xFF
        self.z = not value
        self.n = value >> 7

    def cmp_inx(self):
        self.timer.time += 18
        self.pc += 1
        value = self.a - self.memory.read(self.memory.read2((self.memory.read(self.pc) + self.x) & 0xFF))
        self.c = value >= 0
        value &= 0xFF
        self.z = not value
        self.n = value >> 7

    def cmp_iny(self):
        self.timer.time += 15
        self.pc += 1
        tmp = self.memory.read2(self.memory.read(self.pc))
        tmp2 = (tmp + self.y) & 0xFFFF
        if (tmp & 0xF00) != (tmp2 & 0xF00):
            self.timer.time += 3
        value = self.a - self.memory.read(tmp2)
        self.c = value >= 0
        value &= 0xFF
        self.z = not value
        self.n = value >> 7

    def cpx_im(self):
        self.timer.time += 6
        self.pc += 1
        value = self.x - self.memory.read(self.pc)
        self.c = value >= 0
        value &= 0xFF
        self.z = not value
        self.n = value >> 7

    def cpx_zp(self):
        self.timer.time += 9
        self.pc += 1
        value = self.x - self.memory.read(self.memory.read(self.pc))
        self.c = value >= 0
        value &= 0xFF
        self.z = not value
        self.n = value >> 7

    def cpx_ab(self):
        self.timer.time += 12
        self.pc += 2
        value = self.x - self.memory.read(self.memory.read2(self.pc - 1))
        self.c = value >= 0
        value &= 0xFF
        self.z = not value
        self.n = value >> 7

    def cpy_im(self):
        self.timer.time += 6
        self.pc += 1
        value = self.y - self.memory.read(self.pc)
        self.c = value >= 0
        value &= 0xFF
        self.z = not value
        self.n = value >> 7

    def cpy_zp(self):
        self.timer.time += 9
        self.pc += 1
        value = self.y - self.memory.read(self.memory.read(self.pc))
        self.c = value >= 0
        value &= 0xFF
        self.z = not value
        self.n = value >> 7

    def cpy_ab(self):
        self.timer.time += 12
        self.pc += 2
        value = self.y - self.memory.read(self.memory.read2(self.pc - 1))
        self.c = value >= 0
        value &= 0xFF
        self.z = not value
        self.n = value >> 7

    def dec_zp(self):
        self.timer.time += 15
        self.pc += 1
        address = self.memory.read(self.pc)
        value = (self.memory.read(address) - 1) & 0xFF
        self.memory.write(address, value)
        self.z = not value
        self.n = value >> 7

    def dec_zpx(self):
        self.timer.time += 18
        self.pc += 1
        address = (self.memory.read(self.pc) + self.x) & 0xFF
        value = (self.memory.read(address) - 1) & 0xFF
        self.memory.write(address, value)
        self.z = not value
        self.n = value >> 7

    def dec_ab(self):
        self.timer.time += 18
        self.pc += 2
        address = self.memory.read2(self.pc - 1)
        value = (self.memory.read(address) - 1) & 0xFF
        self.memory.write(address, value)
        self.z = not value
        self.n = value >> 7

    def dec_abx(self):
        self.timer.time += 21
        self.pc += 2
        address = (self.memory.read2(self.pc - 1) + self.x) & 0xFFFF
        value = (self.memory.read(address) - 1) & 0xFF
        self.memory.write(address, value)
        self.z = not value
        self.n = value >> 7

    def dex(self):
        self.timer.time += 6
        self.x = (self.x - 1) & 0xFF
        self.z = not self.x
        self.n = self.x >> 7

    def dey(self):
        self.timer.time += 6
        self.y = (self.y - 1) & 0xFF
        self.z = not self.y
        self.n = self.y >> 7

    def eor_im(self):
        self.timer.time += 6
        self.pc += 1
        self.a ^= self.memory.read(self.pc)
        self.z = not self.a
        self.n = self.a >> 7

    def eor_zp(self):
        self.timer.time += 9
        self.pc += 1
        self.a ^= self.memory.read(self.memory.read(self.pc))
        self.z = not self.a
        self.n = self.a >> 7

    def eor_zpx(self):
        self.timer.time += 12
        self.pc += 1
        self.a ^= self.memory.read((self.memory.read(self.pc) + self.x) & 0xFF)
        self.z = not self.a
        self.n = self.a >> 7

    def eor_ab(self):
        self.timer.time += 12
        self.pc += 2
        self.a ^= self.memory.read(self.memory.read2(self.pc - 1))
        self.z = not self.a
        self.n = self.a >> 7

    def eor_abx(self):
        self.timer.time += 12
        self.pc += 2
        tmp = self.memory.read2(self.pc - 1)
        tmp2 = (tmp + self.x) & 0xFFFF
        if (tmp & 0xF00) != (tmp2 & 0xF00):
            self.timer.time += 3
        self.a ^= self.memory.read(tmp2)
        self.z = not self.a
        self.n = self.a >> 7

    def eor_aby(self):
        self.timer.time += 12
        self.pc += 2
        tmp = self.memory.read2(self.pc - 1)
        tmp2 = (tmp + self.y) & 0xFFFF
        if (tmp & 0xF00) != (tmp2 & 0xF00):
            self.timer.time += 3
        self.a ^= self.memory.read(tmp2)
        self.z = not self.a
        self.n = self.a >> 7

    def eor_inx(self):
        self.timer.time += 18
        self.pc += 1
        self.a ^= self.memory.read(self.memory.read2((self.memory.read(self.pc) + self.x) & 0xFF))
        self.z = not self.a
        self.n = self.a >> 7

    def eor_iny(self):
        self.timer.time += 15
        self.pc += 1
        tmp = self.memory.read2(self.memory.read(self.pc))
        tmp2 = (tmp + self.y) & 0xFFFF
        if (tmp & 0xF00) != (tmp2 & 0xF00):
            self.timer.time += 3
        self.a ^= self.memory.read(tmp2)
        self.z = not self.a
        self.n = self.a >> 7

    def inc_zp(self):
        self.timer.time += 15
        self.pc += 1
        address = self.memory.read(self.pc)
        value = (self.memory.read(address) + 1) & 0xFF
        self.memory.write(address, value)
        self.z = not value
        self.n = value >> 7

    def inc_zpx(self):
        self.timer.time += 18
        self.pc += 1
        address = (self.memory.read(self.pc) + self.x) & 0xFF
        value = (self.memory.read(address) + 1) & 0xFF
        self.memory.write(address, value)
        self.z = not value
        self.n = value >> 7

    def inc_ab(self):
        self.timer.time += 18
        self.pc += 2
        address = self.memory.read2(self.pc - 1)
        value = (self.memory.read(address) + 1) & 0xFF
        self.memory.write(address, value)
        self.z = not value
        self.n = value >> 7

    def inc_abx(self):
        self.timer.time += 21
        self.pc += 2
        address = (self.memory.read2(self.pc - 1) + self.x) & 0xFFFF
        value = (self.memory.read(address) + 1) & 0xFF
        self.memory.write(address, value)
        self.z = not value
        self.n = value >> 7

    def inx(self):
        self.timer.time += 6
        self.x = (self.x + 1) & 0xFF
        self.z = not self.x
        self.n = self.x >> 7

    def iny(self):
        self.timer.time += 6
        self.y = (self.y + 1) & 0xFF
        self.z = not self.y
        self.n = self.y >> 7

    def jmp_ab(self):
        self.timer.time += 9
        self.pc = self.memory.read2(self.pc + 1) - 1

    def jmp_in(self):
        self.timer.time += 15
        self.pc = self.memory.read2(self.memory.read2(self.pc + 1)) - 1

    def jsr(self):
        self.timer.time += 18
        self.pc += 2
        self.memory.write(self.s, (self.pc >> 8) & 0xFF)
        self.s = (self.s - 1) & 0xFF
        self.memory.write(self.s, self.pc & 0xFF)
        self.s = (self.s - 1) & 0xFF
        self.pc = self.memory.read2(self.pc - 1) - 1

    def lda_im(self):
        self.timer.time += 6
        self.pc += 1
        self.a = self.memory.read(self.pc)
        self.z = not self.a
        self.n = self.a >> 7

    def lda_zp(self):
        self.timer.time += 9
        self.pc += 1
        self.a = self.memory.read(self.memory.read(self.pc))
        self.z = not self.a
        self.n = self.a >> 7

    def lda_zpx(self):
        self.timer.time += 12
        self.pc += 1
        self.a = self.memory.read((self.memory.read(self.pc) + self.x) & 0xFF)
        self.z = not self.a
        self.n = self.a >> 7

    def lda_ab(self):
        self.timer.time += 12
        self.pc += 2
        self.a = self.memory.read(self.memory.read2(self.pc - 1))
        self.z = not self.a
        self.n = self.a >> 7

    def lda_abx(self):
        self.timer.time += 12
        self.pc += 2
        tmp = self.memory.read2(self.pc - 1)
        tmp2 = (tmp + self.x) & 0xFFFF
        if (tmp & 0xF00) != (tmp2 & 0xF00):
            self.timer.time += 3
        self.a = self.memory.read(tmp2)
        self.z = not self.a
        self.n = self.a >> 7

    def lda_aby(self):
        self.timer.time += 12
        self.pc += 2
        tmp = self.memory.read2(self.pc - 1)
        tmp2 = (tmp + self.y) & 0xFFFF
        if (tmp & 0xF00) != (tmp2 & 0xF00):
            self.timer.time += 3
        self.a = self.memory.read(tmp2)
        self.z = not self.a
        self.n = self.a >> 7

    def lda_inx(self):
        self.timer.time += 18
        self.pc += 1
        self.a = self.memory.read(self.memory.read2((self.memory.read(self.pc) + self.x) & 0xFF))
        self.z = not self.a
        self.n = self.a >> 7

    def lda_iny(self):
        self.timer.time += 15
        self.pc += 1
        tmp = self.memory.read2(self.memory.read(self.pc))
        tmp2 = (tmp + self.y) & 0xFFFF
        if (tmp & 0xF00) != (tmp2 & 0xF00):
            self.timer.time += 3
        self.a = self.memory.read(tmp2)
        self.z = not self.a
        self.n = self.a >> 7

    def ldx_im(self):
        self.timer.time += 6
        self.pc += 1
        self.x = self.memory.read(self.pc)
        self.z = not self.x
        self.n = self.x >> 7

    def ldx_zp(self):
        self.timer.time += 9
        self.pc += 1
        self.x = self.memory.read(self.memory.read(self.pc))
        self.z = not self.x
        self.n = self.x >> 7

    def ldx_zpy(self):
        self.timer.time += 12
        self.pc += 1
        self.x = self.memory.read((self.memory.read(self.pc) + self.y) & 0xFF)
        self.z = not self.x
        self.n = self.x >> 7

    def ldx_ab(self):
        self.timer.time += 12
        self.pc += 2
        self.x = self.memory.read(self.memory.read2(self.pc - 1))
        self.z = not self.x
        self.n = self.x >> 7

    def ldx_aby(self):
        self.timer.time += 12
        self.pc += 2
        tmp = self.memory.read2(self.pc - 1)
        tmp2 = (tmp + self.y) & 0xFFFF
        if (tmp & 0xF00) != (tmp2 & 0xF00):
            self.timer.time += 3
        self.x = self.memory.read(tmp2)
        self.z = not self.x
        self.n = self.x >> 7

    def ldy_im(self):
        self.timer.time += 6
        self.pc += 1
        self.y = self.memory.read(self.pc)
        self.z = not self.y
        self.n = self.y >> 7

    def ldy_zp(self):
        self.timer.time += 9
        self.pc += 1
        self.y = self.memory.read(self.memory.read(self.pc))
        self.z = not self.y
        self.n = self.y >> 7

    def ldy_zpx(self):
        self.timer.time += 12
        self.pc += 1
        self.y = self.memory.read((self.memory.read(self.pc) + self.x) & 0xFF)
        self.z = not self.y
        self.n = self.y >> 7

    def ldy_ab(self):
        self.timer.time += 12
        self.pc += 2
        self.y = self.memory.read(self.memory.read2(self.pc - 1))
        self.z = not self.y
        self.n = self.y >> 7

    def ldy_abx(self):
        self.timer.time += 12
        self.pc += 2
        tmp = self.memory.read2(self.pc - 1)
        tmp2 = (tmp + self.x) & 0xFFFF
        if (tmp & 0xF00) != (tmp2 & 0xF00):
            self.timer.time += 3
        self.y = self.memory.read(tmp2)
        self.z = not self.y
        self.n = self.y >> 7

    def lsr_acc(self):
        self.timer.time += 6
        self.c = self.a & 0x1
        self.a >>= 1
        self.z = not self.a
        self.n = self.a >> 7

    def lsr_zp(self):
        self.timer.time += 15
        self.pc += 1
        address = self.memory.read(self.pc)
        value = self.memory.read(address)
        self.c = value & 0x1
        value >>= 1
        self.memory.write(address, value)
        self.z = not value
        self.n = value >> 7

    def lsr_zpx(self):
        self.timer.time += 18
        self.pc += 1
        address = (self.memory.read(self.pc) + self.x) & 0xFF
        value = self.memory.read(address)
        self.c = value & 0x1
        value >>= 1
        self.memory.write(address, value)
        self.z = not value
        self.n = value >> 7

    def lsr_ab(self):
        self.timer.time += 18
        self.pc += 2
        address = self.memory.read2(self.pc - 1)
        value = self.memory.read(address)
        self.c = value & 0x1
        value >>= 1
        self.memory.write(address, value)
        self.z = not value
        self.n = value >> 7

    def lsr_abx(self):
        self.timer.time += 21
        self.pc += 2
        address = (self.memory.read2(self.pc - 1) + self.x) & 0xFFFF
        value = self.memory.read(address)
        self.c = value & 0x1
        value >>= 1
        self.memory.write(address, value)
        self.z = not value
        self.n = value >> 7

    def nop(self):
        self.timer.time += 6

    def ora_im(self):
        self.timer.time += 6
        self.pc += 1
        self.a |= self.memory.read(self.pc)
        self.z = not self.a
        self.n = self.a >> 7

    def ora_zp(self):
        self.timer.time += 9
        self.pc += 1
        self.a |= self.memory.read(self.memory.read(self.pc))
        self.z = not self.a
        self.n = self.a >> 7

    def ora_zpx(self):
        self.timer.time += 12
        self.pc += 1
        self.a |= self.memory.read((self.memory.read(self.pc) + self.x) & 0xFF)
        self.z = not self.a
        self.n = self.a >> 7

    def ora_ab(self):
        self.timer.time += 12
        self.pc += 2
        self.a |= self.memory.read(self.memory.read2(self.pc - 1))
        self.z = not self.a
        self.n = self.a >> 7

    def ora_abx(self):
        self.timer.time += 12
        self.pc += 2
        tmp = self.memory.read2(self.pc - 1)
        tmp2 = (tmp + self.x) & 0xFFFF
        if (tmp & 0xF00) != (tmp2 & 0xF00):
            self.timer.time += 3
        self.a |= self.memory.read(tmp2)
        self.z = not self.a
        self.n = self.a >> 7

    def ora_aby(self):
        self.timer.time += 12
        self.pc += 2
        tmp = self.memory.read2(self.pc - 1)
        tmp2 = (tmp + self.y) & 0xFFFF
        if (tmp & 0xF00) != (tmp2 & 0xF00):
            self.timer.time += 3
        self.a |= self.memory.read(tmp2)
        self.z = not self.a
        self.n = self.a >> 7

    def ora_inx(self):
        self.timer.time += 18
        self.pc += 1
        self.a |= self.memory.read(self.memory.read2((self.memory.read(self.pc) + self.x) & 0xFF))
        self.z = not self.a
        self.n = self.a >> 7

    def ora_iny(self):
        self.timer.time += 15
        self.pc += 1
        tmp = self.memory.read2(self.memory.read(self.pc))
        tmp2 = (tmp + self.y) & 0xFFFF
        if (tmp & 0xF00) != (tmp2 & 0xF00):
            self.timer.time += 3
        self.a |= self.memory.read(tmp2)
        self.z = not self.a
        self.n = self.a >> 7

    def pha(self):
        self.timer.time += 9
        self.memory.write(self.s, self.a)
        self.s = (self.s - 1) & 0xFF

    def php(self):
        self.timer.time += 9
        self.memory.write(self.s, self.status_to_int())
        self.s = (self.s - 1) & 0xFF

    def pla(self):
        self.timer.time += 12
        self.s = (self.s + 1) & 0xFF
        self.a = self.memory.read(self.s)

    def plp(self):
        self.timer.time += 12
        self.s = (self.s + 1) & 0xFF
        self.set_status(self.memory.read(self.s))

    def rol_acc(self):
        self.timer.time += 6
        tmp = (self.a & 0x80) >> 7
        self.a = (self.a << 1 | self.c) & 0xFF
        self.c = tmp
        self.z = not self.a
        self.n = self.a >> 7

    def rol_zp(self):
        self.timer.time += 15
        self.pc += 1
        address = self.memory.read(self.pc)
        value = self.memory.read(address)
        tmp = (value & 0x80) >> 7
        value = (value << 1 | self.c) & 0xFF
        self.memory.write(address, value)
        self.c = tmp
        self.z = not value
        self.n = value >> 7

    def rol_zpx(self):
        self.timer.time += 18
        self.pc += 1
        address = (self.memory.read(self.pc) + self.x) & 0xFF
        value = self.memory.read(address)
        tmp = (value & 0x80) >> 7
        value = (value << 1 | self.c) & 0xFF
        self.memory.write(address, value)
        self.c = tmp
        self.z = not value
        self.n = value >> 7

    def rol_ab(self):
        self.timer.time += 18
        self.pc += 2
        address = self.memory.read2(self.pc - 1)
        value = self.memory.read(address)
        tmp = (value & 0x80) >> 7
        value = (value << 1 | self.c) & 0xFF
        self.memory.write(address, value)
        self.c = tmp
        self.z = not value
        self.n = value >> 7

    def rol_abx(self):
        self.timer.time += 21
        self.pc += 2
        address = (self.memory.read2(self.pc - 1) + self.x) & 0xFFFF
        value = self.memory.read(address)
        tmp = (value & 0x80) >> 7
        value = (value << 1 | self.c) & 0xFF
        self.memory.write(address, value)
        self.c = tmp
        self.z = not value
        self.n = value >> 7

    def ror_acc(self):
        self.timer.time += 6
        tmp = self.a & 0x1
        self.a = (self.c << 7) | self.a >> 1
        self.c = tmp
        self.z = not self.a
        self.n = self.a >> 7

    def ror_zp(self):
        self.timer.time += 15
        self.pc += 1
        address = self.memory.read(self.pc)
        value = self.memory.read(address)
        tmp = value & 0x1
        value = (self.c << 7) | value >> 1
        self.memory.write(address, value)
        self.c = tmp
        self.z = not value
        self.n = value >> 7

    def ror_zpx(self):
        self.timer.time += 18
        self.pc += 1
        address = (self.memory.read(self.pc) + self.x) & 0xFF
        value = self.memory.read(address)
        tmp = value & 0x1
        value = (self.c << 7) | value >> 1
        self.memory.write(address, value)
        self.c = tmp
        self.z = not value
        self.n = value >> 7

    def ror_ab(self):
        self.timer.time += 18
        self.pc += 2
        address = self.memory.read2(self.pc - 1)
        value = self.memory.read(address)
        tmp = value & 0x1
        value = (self.c << 7) | value >> 1
        self.memory.write(address, value)
        self.c = tmp
        self.z = not value
        self.n = value >> 7

    def ror_abx(self):
        self.timer.time += 21
        self.pc += 2
        address = (self.memory.read2(self.pc - 1) + self.x) & 0xFFFF
        value = self.memory.read(address)
        tmp = value & 0x1
        value = (self.c << 7) | value >> 1
        self.memory.write(address, value)
        self.c = tmp
        self.z = not value
        self.n = value >> 7

    def rti(self):
        self.timer.time += 18
        self.s = (self.s + 1) & 0xFF
        self.set_status(self.memory.read(self.s))

        self.pc = self.memory.read2(self.s + 1) - 1
        self.s = (self.s + 2) & 0xFF

    def rts(self):
        self.timer.time += 18
        self.pc = self.memory.read2(self.s + 1)
        self.s = (self.s + 2) & 0xFF

    def sbc_im(self):
        self.timer.time += 6
        self.pc += 1
        value = self.memory.read(self.pc)
        r = self.a - value - (not self.c)
        self.v = (self.a ^ value) & (self.a ^ r) & 0x80 != 0
        self.c = not (r & 0x100)
        r &= 0xFF

        if not self.d:
            self.a = r
            self.z = not r
            self.n = r >> 7
        else:
            self.z = not r
            self.n = r >> 7

            lo = (self.a & 0x0F) - (value & 0x0F) - (not self.c)
            hi = (self.a & 0xF0) - (value & 0xF0)
            if lo & 0x10:
                lo -= 6
                hi -= 1

            if hi & 0x0100:
                hi -= 0x60
            self.a = (lo & 0x0F) | (hi & 0xF0)

    def sbc_zp(self):
        self.timer.time += 9
        self.pc += 1
        value = self.memory.read(self.memory.read(self.pc))
        r = self.a - value - (not self.c)
        self.v = (self.a ^ value) & (self.a ^ r) & 0x80 != 0
        self.c = not (r & 0x100)
        r &= 0xFF

        if not self.d:
            self.a = r
            self.z = not r
            self.n = r >> 7
        else:
            self.z = not r
            self.n = r >> 7

            lo = (self.a & 0x0F) - (value & 0x0F) - (not self.c)
            hi = (self.a & 0xF0) - (value & 0xF0)
            if lo & 0x10:
                lo -= 6
                hi -= 1

            if hi & 0x0100:
                hi -= 0x60
            self.a = (lo & 0x0F) | (hi & 0xF0)

    def sbc_zpx(self):
        self.timer.time += 12
        self.pc += 1
        value = self.memory.read((self.memory.read(self.pc) + self.x) & 0xFF)
        r = self.a - value - (not self.c)
        self.v = (self.a ^ value) & (self.a ^ r) & 0x80 != 0
        self.c = not (r & 0x100)
        r &= 0xFF

        if not self.d:
            self.a = r
            self.z = not r
            self.n = r >> 7
        else:
            self.z = not r
            self.n = r >> 7

            lo = (self.a & 0x0F) - (value & 0x0F) - (not self.c)
            hi = (self.a & 0xF0) - (value & 0xF0)
            if lo & 0x10:
                lo -= 6
                hi -= 1

            if hi & 0x0100:
                hi -= 0x60
            self.a = (lo & 0x0F) | (hi & 0xF0)

    def sbc_ab(self):
        self.timer.time += 12
        self.pc += 2
        value = self.memory.read(self.memory.read2(self.pc - 1))
        r = self.a - value - (not self.c)
        self.v = (self.a ^ value) & (self.a ^ r) & 0x80 != 0
        self.c = not (r & 0x100)
        r &= 0xFF

        if not self.d:
            self.a = r
            self.z = not r
            self.n = r >> 7
        else:
            self.z = not r
            self.n = r >> 7

            lo = (self.a & 0x0F) - (value & 0x0F) - (not self.c)
            hi = (self.a & 0xF0) - (value & 0xF0)
            if lo & 0x10:
                lo -= 6
                hi -= 1

            if hi & 0x0100:
                hi -= 0x60
            self.a = (lo & 0x0F) | (hi & 0xF0)

    def sbc_abx(self):
        self.timer.time += 12
        self.pc += 2
        tmp = self.memory.read2(self.pc - 1)
        tmp2 = (tmp + self.x) & 0xFFFF
        if (tmp & 0xF00) != (tmp2 & 0xF00):
            self.timer.time += 3
        value = self.memory.read(tmp2)
        r = self.a - value - (not self.c)
        self.v = (self.a ^ value) & (self.a ^ r) & 0x80 != 0
        self.c = not (r & 0x100)
        r &= 0xFF

        if not self.d:
            self.a = r
            self.z = not r
            self.n = r >> 7
        else:
            self.z = not r
            self.n = r >> 7

            lo = (self.a & 0x0F) - (value & 0x0F) - (not self.c)
            hi = (self.a & 0xF0) - (value & 0xF0)
            if lo & 0x10:
                lo -= 6
                hi -= 1

            if hi & 0x0100:
                hi -= 0x60
            self.a = (lo & 0x0F) | (hi & 0xF0)

    def sbc_aby(self):
        self.timer.time += 12
        self.pc += 2
        tmp = self.memory.read2(self.pc - 1)
        tmp2 = (tmp + self.y) & 0xFFFF
        if (tmp & 0xF00) != (tmp2 & 0xF00):
            self.timer.time += 3
        value = self.memory.read(tmp2)
        r = self.a - value - (not self.c)
        self.v = (self.a ^ value) & (self.a ^ r) & 0x80 != 0
        self.c = not (r & 0x100)
        r &= 0xFF

        if not self.d:
            self.a = r
            self.z = not r
            self.n = r >> 7
        else:
            self.z = not r
            self.n = r >> 7

            lo = (self.a & 0x0F) - (value & 0x0F) - (not self.c)
            hi = (self.a & 0xF0) - (value & 0xF0)
            if lo & 0x10:
                lo -= 6
                hi -= 1

            if hi & 0x0100:
                hi -= 0x60
            self.a = (lo & 0x0F) | (hi & 0xF0)

    def sbc_inx(self):
        self.timer.time += 18
        self.pc += 1
        value = self.memory.read(self.memory.read2((self.memory.read(self.pc) + self.x) & 0xFF))
        r = self.a - value - (not self.c)
        self.v = (self.a ^ value) & (self.a ^ r) & 0x80 != 0
        self.c = not (r & 0x100)
        r &= 0xFF

        if not self.d:
            self.a = r
            self.z = not r
            self.n = r >> 7
        else:
            self.z = not r
            self.n = r >> 7

            lo = (self.a & 0x0F) - (value & 0x0F) - (not self.c)
            hi = (self.a & 0xF0) - (value & 0xF0)
            if lo & 0x10:
                lo -= 6
                hi -= 1

            if hi & 0x0100:
                hi -= 0x60
            self.a = (lo & 0x0F) | (hi & 0xF0)

    def sbc_iny(self):
        self.timer.time += 15
        self.pc += 1
        tmp = self.memory.read2(self.memory.read(self.pc))
        tmp2 = (tmp + self.y) & 0xFFFF
        if (tmp & 0xF00) != (tmp2 & 0xF00):
            self.timer.time += 3
        value = self.memory.read(tmp2)
        r = self.a - value - (not self.c)
        self.v = (self.a ^ value) & (self.a ^ r) & 0x80 != 0
        self.c = not (r & 0x100)
        r &= 0xFF

        if not self.d:
            self.a = r
            self.z = not r
            self.n = r >> 7
        else:
            self.z = not r
            self.n = r >> 7

            lo = (self.a & 0x0F) - (value & 0x0F) - (not self.c)
            hi = (self.a & 0xF0) - (value & 0xF0)
            if lo & 0x10:
                lo -= 6
                hi -= 1

            if hi & 0x0100:
                hi -= 0x60
            self.a = (lo & 0x0F) | (hi & 0xF0)

    def sec(self):
        self.timer.time += 6
        self.c = 1

    def sed(self):
        self.timer.time += 6
        self.d = 1

    def sei(self):
        self.timer.time += 6
        self.i = 1

    def sta_zp(self):
        self.timer.time += 9
        self.pc += 1
        self.memory.write(self.memory.read(self.pc), self.a)

    def sta_zpx(self):
        self.timer.time += 12
        self.pc += 1
        self.memory.write((self.memory.read(self.pc) + self.x) & 0xFF, self.a)

    def sta_ab(self):
        self.timer.time += 12
        self.pc += 2
        self.memory.write(self.memory.read2(self.pc - 1), self.a)

    def sta_abx(self):
        self.timer.time += 15
        self.pc += 2
        self.memory.write((self.memory.read2(self.pc - 1) + self.x) & 0xFFFF, self.a)

    def sta_aby(self):
        self.timer.time += 15
        self.pc += 2
        self.memory.write((self.memory.read2(self.pc - 1) + self.y) & 0xFFFF, self.a)

    def sta_inx(self):
        self.timer.time += 18
        self.pc += 1
        self.memory.write(self.memory.read2((self.memory.read(self.pc) + self.x) & 0xFF), self.a)

    def sta_iny(self):
        self.timer.time += 18
        self.pc += 1
        self.memory.write((self.memory.read2(self.memory.read(self.pc)) + self.y) & 0xFFFF, self.a)

    def stx_zp(self):
        self.timer.time += 9
        self.pc += 1
        self.memory.write(self.memory.read(self.pc), self.x)

    def stx_zpy(self):
        self.timer.time += 12
        self.pc += 1
        self.memory.write((self.memory.read(self.pc) + self.y) & 0xFF, self.x)

    def stx_ab(self):
        self.timer.time += 12
        self.pc += 2
        self.memory.write(self.memory.read2(self.pc - 1), self.x)

    def sty_zp(self):
        self.timer.time += 9
        self.pc += 1
        self.memory.write(self.memory.read(self.pc), self.y)

    def sty_zpx(self):
        self.timer.time += 12
        self.pc += 1
        self.memory.write((self.memory.read(self.pc) + self.x) & 0xFF, self.y)

    def sty_ab(self):
        self.timer.time += 12
        self.pc += 2
        self.memory.write(self.memory.read2(self.pc - 1), self.y)

    def tax(self):
        self.timer.time += 6
        self.x = self.a
        self.z = not self.a
        self.n = self.a >> 7

    def tay(self):
        self.timer.time += 6
        self.y = self.a
        self.z = not self.a
        self.n = self.a >> 7

    def tsx(self):
        self.timer.time += 6
        self.x = self.s

    def txa(self):
        self.timer.time += 6
        self.a = self.x
        self.z = not self.a
        self.n = self.a >> 7

    def txs(self):
        self.timer.time += 6
        self.s = self.x

    def tya(self):
        self.timer.time += 6
        self.a = self.y
        self.z = not self.a
        self.n = self.a >> 7

    # undocumented opcodes
    """
    def dcp(self):
        print("dcp")
        self.dec(address)
        self.cmp(address)

    def isc(self):
        print("isc")
        print(self.pc)
        self.inc(address)
        self.sbc(address)

    def slo(self):
        print("slo")
        self.asl(address)
        self.ora(address)

    def rra(self):
        print("rra")
        self.ror(address)
        self.adc(address)

    def dop(self):
        print("dop")
        self.nop()
    """

    def get_opcodes(self):
        return {
            0x69: self.adc_im,
            0x65: self.adc_zp,
            0x75: self.adc_zpx,
            0x6D: self.adc_ab,
            0x7D: self.adc_abx,
            0x79: self.adc_aby,
            0x61: self.adc_inx,
            0x71: self.adc_iny,

            0x29: self.and_im,
            0x25: self.and_zp,
            0x35: self.and_zpx,
            0x2D: self.and_ab,
            0x3D: self.and_abx,
            0x39: self.and_aby,
            0x21: self.and_inx,
            0x31: self.and_iny,

            0x0A: self.asl_acc,
            0x06: self.asl_zp,
            0x16: self.asl_zpx,
            0x0E: self.asl_ab,
            0x1E: self.asl_abx,

            0x24: self.bit_zp,
            0x2C: self.bit_ab,

            0x10: self.bpl,
            0x30: self.bmi,
            0x50: self.bvc,
            0x70: self.bvs,
            0x90: self.bcc,
            0xB0: self.bcs,
            0xD0: self.bne,
            0xF0: self.beq,

            0x00: self.brk,

            0xC9: self.cmp_im,
            0xC5: self.cmp_zp,
            0xD5: self.cmp_zpx,
            0xCD: self.cmp_ab,
            0xDD: self.cmp_abx,
            0xD9: self.cmp_aby,
            0xC1: self.cmp_inx,
            0xD1: self.cmp_iny,

            0xE0: self.cpx_im,
            0xE4: self.cpx_zp,
            0xEC: self.cpx_ab,

            0xC0: self.cpy_im,
            0xC4: self.cpy_zp,
            0xCC: self.cpy_ab,

            0xC6: self.dec_zp,
            0xD6: self.dec_zpx,
            0xCE: self.dec_ab,
            0xDE: self.dec_abx,

            0x49: self.eor_im,
            0x45: self.eor_zp,
            0x55: self.eor_zpx,
            0x4D: self.eor_ab,
            0x5D: self.eor_abx,
            0x59: self.eor_aby,
            0x41: self.eor_inx,
            0x51: self.eor_iny,

            0x18: self.clc,
            0xD8: self.cld,
            0x58: self.cli,
            0xB8: self.clv,
            0x38: self.sec,
            0x78: self.sei,
            0xF8: self.sed,

            0xE6: self.inc_zp,
            0xF6: self.inc_zpx,
            0xEE: self.inc_ab,
            0xFE: self.inc_abx,

            0x4C: self.jmp_ab,
            0x6C: self.jmp_in,

            0x20: self.jsr,

            0xA9: self.lda_im,
            0xA5: self.lda_zp,
            0xB5: self.lda_zpx,
            0xAD: self.lda_ab,
            0xBD: self.lda_abx,
            0xB9: self.lda_aby,
            0xA1: self.lda_inx,
            0xB1: self.lda_iny,

            0xA2: self.ldx_im,
            0xA6: self.ldx_zp,
            0xB6: self.ldx_zpy,
            0xAE: self.ldx_ab,
            0xBE: self.ldx_aby,

            0xA0: self.ldy_im,
            0xA4: self.ldy_zp,
            0xB4: self.ldy_zpx,
            0xAC: self.ldy_ab,
            0xBC: self.ldy_abx,

            0x4a: self.lsr_acc,
            0x46: self.lsr_zp,
            0x56: self.lsr_zpx,
            0x4E: self.lsr_ab,
            0x5E: self.lsr_abx,

            0xEA: self.nop,

            0x09: self.ora_im,
            0x05: self.ora_zp,
            0x15: self.ora_zpx,
            0x0D: self.ora_ab,
            0x1D: self.ora_abx,
            0x19: self.ora_aby,
            0x01: self.ora_inx,
            0x11: self.ora_iny,

            0xAA: self.tax,
            0x8A: self.txa,
            0xCA: self.dex,
            0xE8: self.inx,
            0xA8: self.tay,
            0x98: self.tya,
            0x88: self.dey,
            0xC8: self.iny,

            0x2A: self.rol_acc,
            0x26: self.rol_zp,
            0x36: self.rol_zpx,
            0x2E: self.rol_ab,
            0x3E: self.rol_abx,

            0x6A: self.ror_acc,
            0x66: self.ror_zp,
            0x76: self.ror_zpx,
            0x6E: self.ror_ab,
            0x7E: self.ror_abx,

            0x40: self.rti,

            0x60: self.rts,

            0xE9: self.sbc_im,
            0xE5: self.sbc_zp,
            0xF5: self.sbc_zpx,
            0xED: self.sbc_ab,
            0xFD: self.sbc_abx,
            0xF9: self.sbc_aby,
            0xE1: self.sbc_inx,
            0xF1: self.sbc_iny,

            0x85: self.sta_zp,
            0x95: self.sta_zpx,
            0x8D: self.sta_ab,
            0x9D: self.sta_abx,
            0x99: self.sta_aby,
            0x81: self.sta_inx,
            0x91: self.sta_iny,

            0x9A: self.txs,
            0xBA: self.tsx,
            0x48: self.pha,
            0x68: self.pla,
            0x08: self.php,
            0x28: self.plp,

            0x86: self.stx_zp,
            0x96: self.stx_zpy,
            0x8E: self.stx_ab,

            0x84: self.sty_zp,
            0x94: self.sty_zpx,
            0x8C: self.sty_ab
        }
