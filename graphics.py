import numpy as np
import pygame

from colors import color_table
from audio import Audio

# bit of a hack to avoid method lookups
np.where = np.core.umath.where
np.unpackbits = np.core.umath.unpackbits
np.packbits = np.core.umath.packbits
np.copyto = np.core.umath.copyto


class Tia:
    # frame dimensions (160 x 192)
    width = 160
    height = 220

    # emulated size
    line_width = 228

    # screen buffer sizes
    canvas_pixels = line_width * height  # size of emulated screen

    # aspect ratio (5:3)
    width_ratio = 5
    height_ratio = 3

    # final picture dimensions
    picture_dims = (width * width_ratio, height * height_ratio)
    scaling_dims = (line_width * width_ratio, height * height_ratio)
    cropping_dims = (68 * width_ratio, 0, width * width_ratio, height * height_ratio)

    def __init__(self, timer, controller):
        self.play_audio = True
        # self.play_audio = False
        self.audio = Audio()
        # control, frequency, volume
        self.sound0 = [0, 0, 0]
        self.sound1 = [0, 0, 0]

        self.timer = timer
        self.controller = controller
        self.screen = None
        self.background = None

        self.v_sync = False
        self.v_blank = False

        self.colors = []
        for color in color_table:
            self.colors.append(color[0] << 16 | color[1] << 8 | color[2])
        self.color_p0 = self.colors[0]
        self.color_p1 = self.colors[0]
        self.color_pf = self.colors[0]
        self.color_bk = self.colors[0]

        self.pf_reflected = False
        self.pf_score = False
        self.pf_priority = False

        self.p0_reflected = False
        self.p1_reflected = False

        self.canvas = np.zeros(self.canvas_pixels, dtype="int32")

        self.cur_line2 = np.zeros(self.line_width, dtype="int32")
        self.cur_line = np.split(self.cur_line2, [68])[1]

        self.combined_pf = np.zeros(40, dtype="int8")
        self.pf_tmp = np.zeros(3, dtype="uint8")

        self.p0_graphics = 0
        self.p1_graphics = 0
        self.m0_graphics = 0
        self.m1_graphics = 0
        self.bl_graphics = 0

        self.p0_draw_time = 0
        self.p1_draw_time = 0
        self.m0_draw_time = 0
        self.m1_draw_time = 0
        self.bl_draw_time = 0

        self.p0_hm = 0
        self.p1_hm = 0
        self.m0_hm = 0
        self.m1_hm = 0
        self.bl_hm = 0

        self.p0_size = 0
        self.p1_size = 0

        self.m0_enabled = False
        self.m1_enabled = False
        self.res_m_p0 = 0
        self.res_m_p1 = 0
        self.bl_enabled = False

        self.decoded_p0 = np.zeros(160, dtype="int8")
        self.decoded_p1 = np.zeros(160, dtype="int8")
        self.decoded_pf = np.zeros(160, dtype="int8")

        self.collision0 = 0  # M0 P1	M0 P0
        self.collision1 = 0  # M1 P0	M1 P1
        self.collision2 = 0  # P0 PF	P0 BL
        self.collision3 = 0  # P1 PF	P1 BL
        self.collision4 = 0  # M0 PF	M0 BL
        self.collision5 = 0  # M1 PF	M1 BL
        self.collision6 = 0  # BL PF	unused
        self.collision7 = 0  # P0 P1	M0 M1

        self.collision_pf = np.zeros(self.width, dtype="int8")
        self.collision_m0 = 0
        self.collision_m1 = 0
        self.collision_bl = 0

        self.current_pixel = 0

        self.write_table = {
            0: self.write_v_sync,
            1: self.write_v_blank,
            2: self.write_w_sync,
            3: self.write_r_sync,
            4: self.write_nu_siz0,
            5: self.write_nu_siz1,
            6: self.write_color_p0,
            7: self.write_color_p1,
            8: self.write_color_pf,
            9: self.write_color_bk,
            10: self.write_ctrl_pf,
            11: self.write_ref_p0,
            12: self.write_ref_p1,
            13: self.write_pf0,
            14: self.write_pf1,
            15: self.write_pf2,
            16: self.write_reset_p0,
            17: self.write_reset_p1,
            18: self.write_reset_m0,
            19: self.write_reset_m1,
            20: self.write_reset_bl,
            21: self.write_aud_c0,
            22: self.write_aud_c1,
            23: self.write_aud_f0,
            24: self.write_aud_f1,
            25: self.write_aud_v0,
            26: self.write_aud_v1,
            27: self.write_gr_p0,
            28: self.write_gr_p1,
            29: self.write_ena_m0,
            30: self.write_ena_m1,
            31: self.write_ena_bl,
            32: self.write_hm_p0,
            33: self.write_hm_p1,
            34: self.write_hm_m0,
            35: self.write_hm_m1,
            36: self.write_hm_bl,
            37: self.write_v_del_p0,
            38: self.write_v_del_p1,
            39: self.write_v_del_bl,
            40: self.write_res_m_p0,
            41: self.write_res_m_p1,
            42: self.write_h_move,
            43: self.write_h_move_clear,
            44: self.write_collisions_clear
        }

    def init(self):
        pygame.init()
        pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.KEYUP])
        self.screen = pygame.display.set_mode(self.picture_dims)
        pygame.display.set_caption("Atari 2600")
        self.background = pygame.Surface((self.line_width, self.height))
        self.background = self.background.convert()

    def write_v_sync(self, value):
        if value & 0x2 != self.v_sync:
            if value & 0x2:
                self.draw_frame()
            self.v_sync = value & 0x2

    def write_v_blank(self, value):
        if value & 0x2 != self.v_blank:
            self.update(1)
            self.current_pixel = (self.timer.time % 228) + 1
            self.v_blank = value & 0x2

    def write_w_sync(self, _):
        self.timer.w_sync()

    def write_r_sync(self, _):
        self.timer.r_sync()

    def write_nu_siz0(self, value):
        self.update(0)
        self.p0_size = value & 0x7
        self.m0_graphics = 2 ** ((value >> 4) & 0x3)
        self.collision_m0 = ((2 ** self.m0_graphics) - 1) << (8 - self.m0_graphics)
        self.draw_line()

    def write_nu_siz1(self, value):
        self.update(0)
        self.p1_size = value & 0x7
        self.m1_graphics = 2 ** ((value >> 4) & 0x3)
        self.collision_m1 = ((2 ** self.m1_graphics) - 1) << (8 - self.m1_graphics)
        self.draw_line()

    def write_color_p0(self, value):
        self.update(0)
        self.color_p0 = self.colors[value >> 1]
        self.draw_line()

    def write_color_p1(self, value):
        self.update(0)
        self.color_p1 = self.colors[value >> 1]
        self.draw_line()

    def write_color_pf(self, value):
        self.update(0)
        self.color_pf = self.colors[value >> 1]
        self.draw_line()

    def write_color_bk(self, value):
        self.update(0)
        self.color_bk = self.colors[value >> 1]
        self.draw_line()

    def write_ctrl_pf(self, value):
        self.update(0)

        self.pf_priority = value & 0x4
        self.pf_score = value & 0x2

        self.bl_graphics = 2 ** ((value >> 4) & 0x3)
        self.collision_bl = ((2 ** self.bl_graphics) - 1) << (8 - self.bl_graphics)

        if self.pf_reflected != value & 0x1:
            self.pf_reflected = value & 0x1
            self.decode_pf()
        else:
            self.draw_line()

    def write_ref_p0(self, value):
        self.update(1)
        self.p0_reflected = value & 0x8
        self.decode_player(self.decoded_p0, self.p0_graphics, self.p0_reflected, self.p0_size, self.p0_draw_time)
        self.draw_line()

    def write_ref_p1(self, value):
        self.update(1)
        self.p1_reflected = value & 0x8
        self.decode_player(self.decoded_p1, self.p1_graphics, self.p1_reflected, self.p1_size, self.p1_draw_time)
        self.draw_line()

    def write_pf0(self, value):
        if self.pf_tmp[0] != value:
            self.update(2)
            self.pf_tmp[0] = value
            self.decode_pf()

    def write_pf1(self, value):
        if self.pf_tmp[1] != value:
            self.update(2)
            self.pf_tmp[1] = value
            self.decode_pf()

    def write_pf2(self, value):
        if self.pf_tmp[2] != value:
            self.update(2)
            self.pf_tmp[2] = value
            self.decode_pf()

    def write_reset_p0(self, _):
        self.update(0)
        self.p0_draw_time = (self.timer.time % 228) - 63
        self.draw_line()

    def write_reset_p1(self, _):
        self.update(0)
        self.p1_draw_time = (self.timer.time % 228) - 63
        self.draw_line()

    def write_reset_m0(self, _):
        self.update(0)
        self.m0_draw_time = (self.timer.time % 228) - 64
        self.draw_line()

    def write_reset_m1(self, _):
        self.update(0)
        self.m1_draw_time = (self.timer.time % 228) - 64
        self.draw_line()

    def write_reset_bl(self, _):
        self.update(0)
        self.bl_draw_time = (self.timer.time % 228) - 64
        self.draw_line()

    def write_aud_c0(self, value):
        self.sound0[0] = value & 0xF

    def write_aud_c1(self, value):
        self.sound1[0] = value & 0xF

    def write_aud_f0(self, value):
        self.sound0[1] = value & 0x1F

    def write_aud_f1(self, value):
        self.sound1[1] = value & 0x1F

    def write_aud_v0(self, value):
        self.sound0[2] = value & 0xF

    def write_aud_v1(self, value):
        self.sound1[2] = value & 0xF

    def write_gr_p0(self, value):
        if self.p0_graphics != value:
            self.update(1)
            self.p0_graphics = value
            self.decode_player(self.decoded_p0, self.p0_graphics, self.p0_reflected, self.p0_size, self.p0_draw_time)
            self.draw_line()

    def write_gr_p1(self, value):
        if self.p1_graphics != value:
            self.update(1)
            self.p1_graphics = value
            self.decode_player(self.decoded_p1, self.p1_graphics, self.p1_reflected, self.p1_size, self.p1_draw_time)
            self.draw_line()

    def write_ena_m0(self, value):
        self.update(1)
        self.m0_enabled = value & 0x2
        self.draw_line()

    def write_ena_m1(self, value):
        self.update(1)
        self.m1_enabled = value & 0x2
        self.draw_line()

    def write_ena_bl(self, value):
        self.update(1)
        self.bl_enabled = value & 0x2
        self.draw_line()

    def write_hm_p0(self, value):
        self.p0_hm = self.convert_hm(value)

    def write_hm_p1(self, value):
        self.p1_hm = self.convert_hm(value)

    def write_hm_m0(self, value):
        self.m0_hm = self.convert_hm(value)

    def write_hm_m1(self, value):
        self.m1_hm = self.convert_hm(value)

    def write_hm_bl(self, value):
        self.bl_hm = self.convert_hm(value)

    def write_v_del_p0(self, _):
        self.update(0)  # TODO
        # print("AAA")
        self.draw_line()

    def write_v_del_p1(self, _):
        self.update(0)  # TODO
        # print("BBB")
        self.draw_line()

    def write_v_del_bl(self, _):
        self.update(0)  # TODO
        # print("CCC")
        self.draw_line()

    def write_res_m_p0(self, value):
        self.update(0)
        self.res_m_p0 = value & 0x2

        # once this is turned off, set the missile to p0's position
        if not self.res_m_p0:
            self.m0_draw_time = (self.p0_draw_time + 223) % 228  # not correct but good enough for testing
        self.draw_line()

    def write_res_m_p1(self, value):
        self.update(0)
        self.res_m_p1 = value & 0x2

        # once this is turned off, set the missile to p1's position
        if not self.res_m_p1:
            self.m1_draw_time = (self.p1_draw_time + 223) % 228  # not correct but good enough for testing
        self.draw_line()

    def write_h_move(self, _):
        self.update(6)
        self.p0_draw_time -= self.p0_hm
        self.p1_draw_time -= self.p1_hm
        self.m0_draw_time -= self.m0_hm
        self.m1_draw_time -= self.m1_hm
        self.bl_draw_time -= self.bl_hm

        self.decode_player(self.decoded_p0, self.p0_graphics, self.p0_reflected, self.p0_size, self.p0_draw_time)
        self.decode_player(self.decoded_p1, self.p1_graphics, self.p1_reflected, self.p1_size, self.p1_draw_time)
        self.draw_line()

    def write_h_move_clear(self, _):
        self.p0_hm = 0
        self.p1_hm = 0
        self.m0_hm = 0
        self.m1_hm = 0
        self.bl_hm = 0

    def write_collisions_clear(self, _):
        self.collision0 = 0
        self.collision1 = 0
        self.collision2 = 0
        self.collision3 = 0
        self.collision4 = 0
        self.collision5 = 0
        self.collision6 = 0
        self.collision7 = 0

    def read(self, address):
        address &= 0xf
        if address == 0x0:
            return self.collision0
        elif address == 0x1:
            return self.collision1
        elif address == 0x2:
            return self.collision2
        elif address == 0x3:
            return self.collision3
        elif address == 0x4:
            return self.collision4
        elif address == 0x5:
            return self.collision5
        elif address == 0x6:
            return self.collision6
        elif address == 0x7:
            return self.collision7
        elif address == 0x8:
            return self.controller.input0
        elif address == 0x9:
            return self.controller.input1
        elif address == 0xa:
            return self.controller.input2
        elif address == 0xb:
            return self.controller.input3
        elif address == 0xc:
            return self.controller.input4
        elif address == 0xd:
            return self.controller.input5
        else:
            return 0

    @staticmethod
    def convert_hm(value):
        if value & 0x80:
            return ((value >> 4) & 0x7) - 8
        else:
            return (value >> 4) & 0x7

    def draw_frame(self):
        if self.play_audio:
            self.audio.play_audio(
                self.sound0,
                self.sound1
            )
        self.controller.process_events(pygame.event.get())

        pygame.surfarray.blit_array(self.background, self.canvas.reshape((self.line_width, self.height), order="F"))
        self.screen.blit(pygame.transform.scale(self.background, self.scaling_dims), (0, 0), self.cropping_dims)
        pygame.display.flip()

        self.canvas.fill(0)

        self.timer.frame_done = True

    def draw_line(self):
        if self.pf_priority:
            self.cur_line.fill(self.color_bk)
            self.draw_p1()
            self.draw_m1()
            self.draw_p0()
            self.draw_m0()
            self.draw_bl()
            self.draw_pf()
        else:
            self.draw_pf2()
            self.draw_bl()
            self.draw_p1()
            self.draw_m1()
            self.draw_p0()
            self.draw_m0()

        self.calculate_collisions()

    def update(self, delay):
        pixels = self.timer.time - self.timer.tia_last_update + delay
        if not self.v_blank and self.current_pixel + pixels < self.canvas_pixels:
            tmp = self.current_pixel % self.line_width

            if tmp + pixels > 228:
                self.canvas[self.current_pixel: self.current_pixel + (228 - tmp)] = self.cur_line2[tmp:]
                self.current_pixel += 228 - tmp
                pixels -= 228 - tmp
                while pixels > 228:
                    self.canvas[self.current_pixel: self.current_pixel + 228] = self.cur_line2
                    self.current_pixel += 228
                    pixels -= 228
                self.canvas[self.current_pixel: self.current_pixel + pixels] = self.cur_line2[: pixels]
            else:
                self.canvas[self.current_pixel: self.current_pixel + pixels] = self.cur_line2[tmp: tmp + pixels]

        self.timer.tia_last_update = self.timer.time + delay
        self.current_pixel += pixels

    def decode_pf(self):
        self.combined_pf[:20] = np.unpackbits(self.pf_tmp, bitorder="little")[4:]

        # pf1 flipped
        self.combined_pf[4:12] = self.combined_pf[11:3:-1]

        if self.pf_reflected:
            self.combined_pf[20:] = self.combined_pf[19::-1]
        else:
            self.combined_pf[20:] = self.combined_pf[:20]

        self.decoded_pf = self.combined_pf.repeat(4)

        self.draw_line()

    def decode_player(self, out, graphics, is_reflected, size, draw_time):
        tmp = np.unpackbits(np.array(graphics, dtype="uint8"))
        if is_reflected:
            tmp = tmp[::-1]
        out.fill(0)
        if not size:  # one copy
            self.decode_player2(out, tmp, draw_time)
        elif size == 1:  # two copies - close
            self.decode_player2(out, tmp, draw_time)
            self.decode_player2(out, tmp, draw_time + 0x10)
        elif size == 2:  # two copies - med
            self.decode_player2(out, tmp, draw_time)
            self.decode_player2(out, tmp, draw_time + 0x20)
        elif size == 3:  # three copies - close
            self.decode_player2(out, tmp, draw_time)
            self.decode_player2(out, tmp, draw_time + 0x10)
            self.decode_player2(out, tmp, draw_time + 0x20)
        elif size == 4:  # two copies - wide
            self.decode_player2(out, tmp, draw_time)
            self.decode_player2(out, tmp, draw_time + 0x40)
        elif size == 5:  # double size player
            self.decode_player2(out, tmp.repeat(2), draw_time + 0x1)
        elif size == 6:  # 3 copies medium
            self.decode_player2(out, tmp, draw_time)
            self.decode_player2(out, tmp, draw_time + 0x20)
            self.decode_player2(out, tmp, draw_time + 0x40)
        elif size == 7:  # quad sized player
            self.decode_player2(out, tmp.repeat(4), draw_time + 0x1)

    def draw_pf(self):
        if self.pf_score:
            self.cur_line[:80] = np.where(self.decoded_pf[:80], self.color_p0, self.cur_line[:80])
            self.cur_line[80:] = np.where(self.decoded_pf[80:], self.color_p1, self.cur_line[80:])
        else:
            np.copyto(self.cur_line, np.where(self.decoded_pf, self.color_pf, self.cur_line))

    def draw_pf2(self):
        if self.pf_score:
            self.cur_line[:80] = np.where(self.decoded_pf[:80], self.color_p0, self.color_bk)
            self.cur_line[80:] = np.where(self.decoded_pf[80:], self.color_p1, self.color_bk)
        else:
            np.copyto(self.cur_line, np.where(self.decoded_pf, self.color_pf, self.color_bk))

    def draw_p0(self):
        if self.p0_graphics:
            np.copyto(self.cur_line, np.where(self.decoded_p0, self.color_p0, self.cur_line))

    def draw_p1(self):
        if self.p1_graphics:
            np.copyto(self.cur_line, np.where(self.decoded_p1, self.color_p1, self.cur_line))

    def draw_m0(self):
        if self.m0_enabled and not self.res_m_p0:
            self.draw_sprite_simple(self.m0_graphics, self.m0_draw_time, self.color_p0)

    def draw_m1(self):
        if self.m1_enabled and not self.res_m_p1:
            self.draw_sprite_simple(self.m1_graphics, self.m1_draw_time, self.color_p1)

    def draw_bl(self):
        if self.bl_enabled:
            self.draw_sprite_simple(self.bl_graphics, self.bl_draw_time, self.color_pf)

    @staticmethod
    def decode_player2(out, graphics, time):
        time = max(time, 0)

        for i in range(len(graphics)):
            if graphics[i]:
                out[(time + i) % 160] = 1

    def draw_sprite_simple(self, graphics, time, color):
        time = max(time, 0)
        if 160 - (time + graphics) >= 0:
            self.cur_line[time:time + graphics] = [color] * graphics

    def calculate_collisions(self):  # a mess
        p0 = not not self.p0_graphics
        p1 = not not self.p1_graphics
        m0 = not not self.m0_enabled
        m1 = not not self.m1_enabled
        bl = not not self.bl_enabled

        if p0:
            if p1:
                if (self.decoded_p0 & self.decoded_p1).any():
                    self.collision7 |= 0x80  # P0 P1
            if m0:
                if self.collision_with_pf(self.decoded_p0, self.collision_m0, self.m0_draw_time):
                    self.collision0 |= 0x40  # M0 P0
            if m1:
                if self.collision_with_pf(self.decoded_p0, self.collision_m1, self.m1_draw_time):
                    self.collision1 |= 0x80  # M1 P0
            if bl:
                if self.collision_with_pf(self.decoded_p0, self.collision_bl, self.bl_draw_time):
                    self.collision2 |= 0x40  # P0 BL
            if (self.decoded_p0 & self.decoded_pf).any():
                self.collision2 |= 0x80  # P0 PF

        if p1:
            if m0:
                if self.collision_with_pf(self.decoded_p1, self.collision_m0, self.m0_draw_time):
                    self.collision0 |= 0x80  # M0 P1
            if m1:
                if self.collision_with_pf(self.decoded_p1, self.collision_m1, self.m1_draw_time):
                    self.collision1 |= 0x40  # M1 P1
            if bl:
                if self.collision_with_pf(self.decoded_p1, self.collision_bl, self.bl_draw_time):
                    self.collision3 |= 0x40  # P1 BL
            if (self.decoded_p1 & self.decoded_pf).any():
                self.collision3 |= 0x80  # P1 PF

        if m0:
            if m1:
                if (self.collision_m0 << abs(self.m0_draw_time - self.m1_draw_time)) & self.collision_m1:
                    self.collision7 |= 0x40  # M0 M1
            if bl:
                if (self.collision_m0 << abs(self.m0_draw_time - self.bl_draw_time)) & self.collision_bl:
                    self.collision4 |= 0x40  # M0 BL
            if self.collision_with_pf(self.decoded_pf, self.collision_m0, self.m0_draw_time):
                self.collision4 |= 0x80  # M0 PF

        if m1:
            if bl:
                if (self.collision_m1 << abs(self.m1_draw_time - self.bl_draw_time)) & self.collision_bl:
                    self.collision5 |= 0x40  # M1 BL
            if self.collision_with_pf(self.decoded_pf, self.collision_m1, self.m1_draw_time):
                self.collision5 |= 0x80  # M1 PF

        if bl:
            if self.collision_with_pf(self.decoded_pf, self.collision_bl, self.bl_draw_time):
                self.collision6 |= 0x80  # BL PF

    @staticmethod
    def collision_with_pf(arr, x, x_offset):
        return x & np.packbits(arr[x_offset:x_offset + 8])
