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

    def debug_step(self):
        try:
            opcode = self.opcodes[self.memory.read(self.pc)]

            self.timer.time += opcode.cycles

            if 1:
                print("PC:", hex(self.pc), opcode.function.__name__)
                # print(opcode.function.__name__[:3].upper(), end=" ")
                # if opcode.__class__ is AddressedInstruction:
                #     print(hex(self.memory.read(self.pc + 1)), hex(self.memory.read(self.pc + 2)), end="")
                # print()

            if opcode.addressed:
                opcode.function(opcode.get_address())
            else:
                opcode.function()

            self.pc += 1
        except KeyError:
            raise Exception
            print(f"unknown opcode ({hex(self.memory.read(self.pc))}) at: {hex(self.pc)}")
            print("stepping over...")
            self.pc += 1
            return

    def step(self):
        opcode = self.opcodes[self.memory.read(self.pc)]

        self.timer.time += opcode.cycles

        if opcode.addressed:
            opcode.function(opcode.get_address())
        else:
            opcode.function()

        self.pc += 1

    # helper functions
    def set_n_and_z(self, value):  # n and z are always set together
        self.z = not value
        self.n = value >> 7

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

    def branch(self, address):
        value = self.memory.read(address)
        if value & 0x80:
            new = self.pc + (value - 0x100)
        else:
            new = self.pc + value

        if (self.pc & 0xF00) != (new & 0xF00):
            self.timer.time += 6
        else:
            self.timer.time += 3
        self.pc = new

    # address functions
    def immediate(self):
        self.pc += 1
        return self.pc

    def zero_page(self):
        self.pc += 1
        return self.memory.read(self.pc)

    def zero_page_x(self):
        self.pc += 1
        return (self.memory.read(self.pc) + self.x) & 0xFF

    def zero_page_y(self):
        self.pc += 1
        return (self.memory.read(self.pc) + self.y) & 0xFF

    def absolute(self):
        self.pc += 2
        return self.memory.read2(self.pc - 1)

    def absolute_x(self):
        self.pc += 2
        return (self.memory.read2(self.pc - 1) + self.x) & 0xFFFF

    def delayed_absolute_x(self):
        self.pc += 2
        tmp = self.memory.read2(self.pc - 1)
        tmp2 = (tmp + self.x) & 0xFFFF
        if (tmp & 0xF00) != (tmp2 & 0xF00):
            self.timer.time += 3
        return tmp2

    def absolute_y(self):
        self.pc += 2
        return (self.memory.read2(self.pc - 1) + self.y) & 0xFFFF

    def delayed_absolute_y(self):
        self.pc += 2
        tmp = self.memory.read2(self.pc - 1)
        tmp2 = (tmp + self.y) & 0xFFFF
        if (tmp & 0xF00) != (tmp2 & 0xF00):
            self.timer.time += 3
        return tmp2

    def indirect(self):
        self.pc += 2
        return self.memory.read2(self.memory.read2(self.pc - 1))

    def indirect_x(self):
        self.pc += 1
        return self.memory.read2((self.memory.read(self.pc) + self.x) & 0xFF)

    def indirect_y(self):
        self.pc += 1
        return (self.memory.read2(self.memory.read(self.pc)) + self.y) & 0xFFFF

    def delayed_indirect_y(self):
        self.pc += 1
        tmp = self.memory.read2(self.memory.read(self.pc))
        tmp2 = (tmp + self.y) & 0xFFFF
        if (tmp & 0xF00) != (tmp2 & 0xF00):
            self.timer.time += 3
        return tmp2

    # Instructions
    def adc(self, address):
        value = self.memory.read(address)
        if not self.d:
            r = value + self.a + self.c
            self.v = ~(self.a ^ value) & (self.a ^ r) & 0x80 != 0  # overflow
            self.c = r & 0x100 == 0x100  # carry
            self.a = r & 0xFF
            self.set_n_and_z(self.a)
        else:
            lo = (self.a & 0x0F) + (value & 0x0F) + self.c
            hi = (self.a & 0xF0) + (value & 0xF0)
            self.z = not ((lo + hi) & 0xFF)
            if lo > 0x09:
                hi += 0x10
                lo += 0x06
            self.n = hi & 0x80
            self.v = ~(self.a ^ value) & (self.a ^ hi) & 0x80 != 0
            if hi > 0x90:
                hi += 0x60
            self.c = hi & 0x100 == 0x100

            self.a = (lo & 0x0F) + (hi & 0xF0)

    def and_(self, address):  # has underscore so it doesn't conflict with python built-in "and"
        self.a &= self.memory.read(address)
        self.set_n_and_z(self.a)

    def asl_acc(self):
        self.a <<= 1
        self.c = self.a >> 8
        self.a &= 0xFF
        self.set_n_and_z(self.a)

    def asl(self, address):
        value = self.memory.read(address) << 1
        self.c = value >> 8
        value &= 0xFF
        self.memory.write(address, value)
        self.set_n_and_z(value)

    def bit(self, address):
        value = self.memory.read(address)
        self.n = (value & 0x80) == 0x80
        self.v = (value & 0x40) == 0x40
        self.z = not (self.a & value)

    def bcc(self, address):
        if not self.c:
            self.branch(address)

    def bcs(self, address):
        if self.c:
            self.branch(address)

    def beq(self, address):
        if self.z:
            self.branch(address)

    def bmi(self, address):
        if self.n:
            self.branch(address)

    def bne(self, address):
        if not self.z:
            self.branch(address)

    def bpl(self, address):
        if not self.n:
            self.branch(address)

    def bvc(self, address):
        if not self.v:
            self.branch(address)

    def bvs(self, address):
        if self.v:
            self.branch(address)

    def brk(self):
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
        self.c = 0

    def cld(self):
        self.d = 0

    def cli(self):
        self.i = 0

    def clv(self):
        self.v = 0

    def cmp(self, address):
        value = self.a - self.memory.read(address)
        self.c = value >= 0
        self.set_n_and_z(value & 0xFF)

    def cpx(self, address):
        value = self.x - self.memory.read(address)
        self.c = value >= 0
        self.set_n_and_z(value & 0xFF)

    def cpy(self, address):
        value = self.y - self.memory.read(address)
        self.c = value >= 0
        self.set_n_and_z(value & 0xFF)

    def dec(self, address):
        value = (self.memory.read(address) - 1) & 0xFF
        self.memory.write(address, value)
        self.set_n_and_z(value)

    def dex(self):
        self.x = (self.x - 1) & 0xFF
        self.set_n_and_z(self.x)

    def dey(self):
        self.y = (self.y - 1) & 0xFF
        self.set_n_and_z(self.y)

    def eor(self, address):
        self.a ^= self.memory.read(address)
        self.set_n_and_z(self.a)

    def inc(self, address):
        value = (self.memory.read(address) + 1) & 0xFF
        self.memory.write(address, value)
        self.set_n_and_z(value)

    def inx(self):
        self.x = (self.x + 1) & 0xFF
        self.set_n_and_z(self.x)

    def iny(self):
        self.y = (self.y + 1) & 0xFF
        self.set_n_and_z(self.y)

    def jmp(self, address):
        self.pc = address - 1

    def jsr(self, address):
        self.memory.write(self.s, (self.pc >> 8) & 0xFF)
        self.s = (self.s - 1) & 0xFF
        self.memory.write(self.s, self.pc & 0xFF)
        self.s = (self.s - 1) & 0xFF
        self.pc = address - 1

    def lda(self, address):
        self.a = self.memory.read(address)
        self.set_n_and_z(self.a)

    def ldx(self, address):
        self.x = self.memory.read(address)
        self.set_n_and_z(self.x)

    def ldy(self, address):
        self.y = self.memory.read(address)
        self.set_n_and_z(self.y)

    def lsr_acc(self):
        self.c = self.a & 0x1
        self.a >>= 1
        self.set_n_and_z(self.a)

    def lsr(self, address):
        value = self.memory.read(address)
        self.c = value & 0x1
        value >>= 1
        self.memory.write(address, value)
        self.set_n_and_z(value)

    def nop(self):
        pass

    def ora(self, address):
        self.a |= self.memory.read(address)
        self.set_n_and_z(self.a)

    def pha(self):
        self.memory.write(self.s, self.a)
        self.s = (self.s - 1) & 0xFF

    def php(self):
        self.memory.write(self.s, self.status_to_int())
        self.s = (self.s - 1) & 0xFF

    def pla(self):
        self.s = (self.s + 1) & 0xFF
        self.a = self.memory.read(self.s)

    def plp(self):
        self.s = (self.s + 1) & 0xFF
        self.set_status(self.memory.read(self.s))

    def rol_acc(self):
        tmp = (self.a & 0x80) >> 7
        self.a = (self.a << 1 | self.c) & 0xFF
        self.c = tmp
        self.set_n_and_z(self.a)

    def rol(self, address):
        value = self.memory.read(address)
        tmp = (value & 0x80) >> 7
        value = (value << 1 | self.c) & 0xFF
        self.memory.write(address, value)
        self.c = tmp
        self.set_n_and_z(value)

    def ror_acc(self):
        tmp = self.a & 0x1
        self.a = (self.c << 7) | self.a >> 1
        self.c = tmp
        self.set_n_and_z(self.a)

    def ror(self, address):
        value = self.memory.read(address)
        tmp = value & 0x1
        value = (self.c << 7) | value >> 1
        self.memory.write(address, value)
        self.c = tmp
        self.set_n_and_z(value)

    def rti(self):
        self.s = (self.s + 1) & 0xFF
        self.set_status(self.memory.read(self.s))

        self.pc = self.memory.read2(self.s + 1) - 1
        self.s = (self.s + 2) & 0xFF

    def rts(self):
        self.pc = self.memory.read2(self.s + 1)
        self.s = (self.s + 2) & 0xFF

    def sbc(self, address):
        value = self.memory.read(address)
        r = self.a - value - (not self.c)
        self.v = (self.a ^ value) & (self.a ^ r) & 0x80 != 0
        self.c = not (r & 0x100)

        if not self.d:
            self.a = r & 0xFF
            self.set_n_and_z(self.a)
        else:
            self.set_n_and_z(r & 0xFF)

            lo = (self.a & 0x0F) - (value & 0x0F) - (not self.c)
            hi = (self.a & 0xF0) - (value & 0xF0)
            if lo & 0x10:
                lo -= 6
                hi -= 1

            if hi & 0x0100:
                hi -= 0x60
            self.a = (lo & 0x0F) | (hi & 0xF0)

    def sec(self):
        self.c = 1

    def sed(self):
        self.d = 1

    def sei(self):
        self.i = 1

    def sta(self, address):
        self.memory.write(address, self.a)

    def stx(self, address):
        self.memory.write(address, self.x)

    def sty(self, address):
        self.memory.write(address, self.y)

    def tax(self):
        self.x = self.a
        self.set_n_and_z(self.a)

    def tay(self):
        self.y = self.a
        self.set_n_and_z(self.a)

    def tsx(self):
        self.x = self.s

    def txa(self):
        self.a = self.x
        self.set_n_and_z(self.x)

    def txs(self):
        self.s = self.x

    def tya(self):
        self.a = self.y
        self.set_n_and_z(self.y)

    # undocumented opcodes
    """
    def dcp(self, address):
        print("dcp")
        self.dec(address)
        self.cmp(address)

    def isc(self, address):
        print("isc")
        print(self.pc)
        self.inc(address)
        self.sbc(address)

    def slo(self, address):
        print("slo")
        self.asl(address)
        self.ora(address)

    def rra(self, address):
        print("rra")
        self.ror(address)
        self.adc(address)

    def dop(self):
        print("dop")
        self.nop()
    """

    def get_opcodes(self):
        return {
            0x69: AddressedInstruction(self.adc, 2, self.immediate),
            0x65: AddressedInstruction(self.adc, 3, self.zero_page),
            0x75: AddressedInstruction(self.adc, 4, self.zero_page_x),
            0x6D: AddressedInstruction(self.adc, 4, self.absolute),
            0x7D: AddressedInstruction(self.adc, 4, self.delayed_absolute_x),
            0x79: AddressedInstruction(self.adc, 4, self.delayed_absolute_y),
            0x61: AddressedInstruction(self.adc, 6, self.indirect_x),
            0x71: AddressedInstruction(self.adc, 5, self.delayed_indirect_y),

            0x29: AddressedInstruction(self.and_, 2, self.immediate),
            0x25: AddressedInstruction(self.and_, 3, self.zero_page),
            0x35: AddressedInstruction(self.and_, 4, self.zero_page_x),
            0x2D: AddressedInstruction(self.and_, 4, self.absolute),
            0x3D: AddressedInstruction(self.and_, 4, self.delayed_absolute_x),
            0x39: AddressedInstruction(self.and_, 4, self.delayed_absolute_y),
            0x21: AddressedInstruction(self.and_, 6, self.indirect_x),
            0x31: AddressedInstruction(self.and_, 5, self.delayed_indirect_y),

            0x0A: Instruction(self.asl_acc, 2),  # uses accumulator instead of address
            0x06: AddressedInstruction(self.asl, 5, self.zero_page),
            0x16: AddressedInstruction(self.asl, 6, self.zero_page_x),
            0x0E: AddressedInstruction(self.asl, 6, self.absolute),
            0x1E: AddressedInstruction(self.asl, 7, self.absolute_x),

            0x24: AddressedInstruction(self.bit, 3, self.zero_page),
            0x2C: AddressedInstruction(self.bit, 4, self.absolute),

            0x10: AddressedInstruction(self.bpl, 2, self.immediate),
            0x30: AddressedInstruction(self.bmi, 2, self.immediate),
            0x50: AddressedInstruction(self.bvc, 2, self.immediate),
            0x70: AddressedInstruction(self.bvs, 2, self.immediate),
            0x90: AddressedInstruction(self.bcc, 2, self.immediate),
            0xB0: AddressedInstruction(self.bcs, 2, self.immediate),
            0xD0: AddressedInstruction(self.bne, 2, self.immediate),
            0xF0: AddressedInstruction(self.beq, 2, self.immediate),

            0x00: Instruction(self.brk, 7),

            0xC9: AddressedInstruction(self.cmp, 2, self.immediate),
            0xC5: AddressedInstruction(self.cmp, 3, self.zero_page),
            0xD5: AddressedInstruction(self.cmp, 4, self.zero_page_x),
            0xCD: AddressedInstruction(self.cmp, 4, self.absolute),
            0xDD: AddressedInstruction(self.cmp, 4, self.delayed_absolute_x),
            0xD9: AddressedInstruction(self.cmp, 4, self.delayed_absolute_y),
            0xC1: AddressedInstruction(self.cmp, 6, self.indirect_x),
            0xD1: AddressedInstruction(self.cmp, 5, self.delayed_indirect_y),

            0xE0: AddressedInstruction(self.cpx, 2, self.immediate),
            0xE4: AddressedInstruction(self.cpx, 3, self.zero_page),
            0xEC: AddressedInstruction(self.cpx, 4, self.absolute),

            0xC0: AddressedInstruction(self.cpy, 2, self.immediate),
            0xC4: AddressedInstruction(self.cpy, 3, self.zero_page),
            0xCC: AddressedInstruction(self.cpy, 4, self.absolute),

            0xC6: AddressedInstruction(self.dec, 5, self.zero_page),
            0xD6: AddressedInstruction(self.dec, 6, self.zero_page_x),
            0xCE: AddressedInstruction(self.dec, 6, self.absolute),
            0xDE: AddressedInstruction(self.dec, 7, self.absolute_x),

            0x49: AddressedInstruction(self.eor, 2, self.immediate),
            0x45: AddressedInstruction(self.eor, 3, self.zero_page),
            0x55: AddressedInstruction(self.eor, 4, self.zero_page_x),
            0x4D: AddressedInstruction(self.eor, 4, self.absolute),
            0x5D: AddressedInstruction(self.eor, 4, self.delayed_absolute_x),
            0x59: AddressedInstruction(self.eor, 4, self.delayed_absolute_y),
            0x41: AddressedInstruction(self.eor, 6, self.indirect_x),
            0x51: AddressedInstruction(self.eor, 5, self.delayed_indirect_y),

            0x18: Instruction(self.clc, 2),
            0xD8: Instruction(self.cld, 2),
            0x58: Instruction(self.cli, 2),
            0xB8: Instruction(self.clv, 2),
            0x38: Instruction(self.sec, 2),
            0x78: Instruction(self.sei, 2),
            0xF8: Instruction(self.sed, 2),

            0xE6: AddressedInstruction(self.inc, 5, self.zero_page),
            0xF6: AddressedInstruction(self.inc, 6, self.zero_page_x),
            0xEE: AddressedInstruction(self.inc, 6, self.absolute),
            0xFE: AddressedInstruction(self.inc, 7, self.absolute_x),

            0x4C: AddressedInstruction(self.jmp, 3, self.absolute),
            0x6C: AddressedInstruction(self.jmp, 5, self.indirect),

            0x20: AddressedInstruction(self.jsr, 6, self.absolute),

            0xA9: AddressedInstruction(self.lda, 2, self.immediate),
            0xA5: AddressedInstruction(self.lda, 3, self.zero_page),
            0xB5: AddressedInstruction(self.lda, 4, self.zero_page_x),
            0xAD: AddressedInstruction(self.lda, 4, self.absolute),
            0xBD: AddressedInstruction(self.lda, 4, self.delayed_absolute_x),
            0xB9: AddressedInstruction(self.lda, 4, self.delayed_absolute_y),
            0xA1: AddressedInstruction(self.lda, 6, self.indirect_x),
            0xB1: AddressedInstruction(self.lda, 5, self.delayed_indirect_y),

            0xA2: AddressedInstruction(self.ldx, 2, self.immediate),
            0xA6: AddressedInstruction(self.ldx, 3, self.zero_page),
            0xB6: AddressedInstruction(self.ldx, 4, self.zero_page_y),
            0xAE: AddressedInstruction(self.ldx, 4, self.absolute),
            0xBE: AddressedInstruction(self.ldx, 4, self.delayed_absolute_y),

            0xA0: AddressedInstruction(self.ldy, 2, self.immediate),
            0xA4: AddressedInstruction(self.ldy, 3, self.zero_page),
            0xB4: AddressedInstruction(self.ldy, 4, self.zero_page_x),
            0xAC: AddressedInstruction(self.ldy, 4, self.absolute),
            0xBC: AddressedInstruction(self.ldy, 4, self.delayed_absolute_x),

            0x4a: Instruction(self.lsr_acc, 2),  # uses accumulator instead of address
            0x46: AddressedInstruction(self.lsr, 5, self.zero_page),
            0x56: AddressedInstruction(self.lsr, 6, self.zero_page_x),
            0x4E: AddressedInstruction(self.lsr, 6, self.absolute),
            0x5E: AddressedInstruction(self.lsr, 7, self.absolute_x),

            0xEA: Instruction(self.nop, 2),

            0x09: AddressedInstruction(self.ora, 2, self.immediate),
            0x05: AddressedInstruction(self.ora, 3, self.zero_page),
            0x15: AddressedInstruction(self.ora, 4, self.zero_page_x),
            0x0D: AddressedInstruction(self.ora, 4, self.absolute),
            0x1D: AddressedInstruction(self.ora, 4, self.delayed_absolute_x),
            0x19: AddressedInstruction(self.ora, 4, self.delayed_absolute_y),
            0x01: AddressedInstruction(self.ora, 6, self.indirect_x),
            0x11: AddressedInstruction(self.ora, 5, self.delayed_indirect_y),

            0xAA: Instruction(self.tax, 2),
            0x8A: Instruction(self.txa, 2),
            0xCA: Instruction(self.dex, 2),
            0xE8: Instruction(self.inx, 2),
            0xA8: Instruction(self.tay, 2),
            0x98: Instruction(self.tya, 2),
            0x88: Instruction(self.dey, 2),
            0xC8: Instruction(self.iny, 2),

            0x2A: Instruction(self.rol_acc, 2),  # uses accumulator instead of address
            0x26: AddressedInstruction(self.rol, 5, self.zero_page),
            0x36: AddressedInstruction(self.rol, 6, self.zero_page_x),
            0x2E: AddressedInstruction(self.rol, 6, self.absolute),
            0x3E: AddressedInstruction(self.rol, 7, self.absolute_x),

            0x6A: Instruction(self.ror_acc, 2),  # uses accumulator instead of address
            0x66: AddressedInstruction(self.ror, 5, self.zero_page),
            0x76: AddressedInstruction(self.ror, 6, self.zero_page_x),
            0x6E: AddressedInstruction(self.ror, 6, self.absolute),
            0x7E: AddressedInstruction(self.ror, 7, self.absolute_x),

            0x40: Instruction(self.rti, 6),

            0x60: Instruction(self.rts, 6),

            0xE9: AddressedInstruction(self.sbc, 2, self.immediate),
            0xE5: AddressedInstruction(self.sbc, 3, self.zero_page),
            0xF5: AddressedInstruction(self.sbc, 4, self.zero_page_x),
            0xED: AddressedInstruction(self.sbc, 4, self.absolute),
            0xFD: AddressedInstruction(self.sbc, 4, self.delayed_absolute_x),
            0xF9: AddressedInstruction(self.sbc, 4, self.delayed_absolute_y),
            0xE1: AddressedInstruction(self.sbc, 6, self.indirect_x),
            0xF1: AddressedInstruction(self.sbc, 5, self.delayed_indirect_y),

            0x85: AddressedInstruction(self.sta, 3, self.zero_page),
            0x95: AddressedInstruction(self.sta, 4, self.zero_page_x),
            0x8D: AddressedInstruction(self.sta, 4, self.absolute),
            0x9D: AddressedInstruction(self.sta, 5, self.absolute_x),
            0x99: AddressedInstruction(self.sta, 5, self.absolute_y),
            0x81: AddressedInstruction(self.sta, 6, self.indirect_x),
            0x91: AddressedInstruction(self.sta, 6, self.indirect_y),

            0x9A: Instruction(self.txs, 2),
            0xBA: Instruction(self.tsx, 2),
            0x48: Instruction(self.pha, 3),
            0x68: Instruction(self.pla, 4),
            0x08: Instruction(self.php, 3),
            0x28: Instruction(self.plp, 4),

            0x86: AddressedInstruction(self.stx, 3, self.zero_page),
            0x96: AddressedInstruction(self.stx, 4, self.zero_page_y),
            0x8E: AddressedInstruction(self.stx, 4, self.absolute),

            0x84: AddressedInstruction(self.sty, 3, self.zero_page),
            0x94: AddressedInstruction(self.sty, 4, self.zero_page_x),
            0x8C: AddressedInstruction(self.sty, 4, self.absolute),
        }


class Instruction:
    def __init__(self, function, cycles):
        self.function = function
        self.cycles = cycles * 3  # pre-convert to color clocks
        self.addressed = 0


class AddressedInstruction:
    def __init__(self, function, cycles, addressing_mode):
        self.function = function
        self.cycles = cycles * 3  # pre-convert to color clocks
        self.get_address = addressing_mode
        self.addressed = 1
