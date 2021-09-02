import numpy as np
from pygame import mixer


class Audio:
    base_frequency = 31400
    note_time = 1.0 / 60.0
    frequency_per_frame = int(base_frequency / 60)

    def __init__(self):
        self.t = np.linspace(0, self.note_time, self.frequency_per_frame, False)
        self.t = self.t * 2 * np.pi
        self.buffer1 = np.zeros(self.frequency_per_frame, dtype="int16")
        self.buffer2 = np.zeros(self.frequency_per_frame, dtype="int16")

        mixer.init(frequency=self.base_frequency, size=-16, channels=1, buffer=512)
        self.channel1 = mixer.Channel(0)
        self.channel2 = mixer.Channel(1)
        self.channel1.set_volume(0.2)
        self.channel2.set_volume(0.2)

    def play_audio(self, audio1, audio2):
        frequency1 = self.calculate_channel(audio1)
        frequency2 = self.calculate_channel(audio2)

        if audio1[2] != 0 and frequency1 != -1:
            self.buffer1.fill(0)
            note = np.sign(np.sin(frequency1 * self.t)).astype("int16")
            self.buffer1 += note * 32767
            self.add_sound(self.channel1, self.buffer1)
        elif self.channel1.get_busy():
            self.channel1.stop()

        if audio2[2] != 0 and frequency2 != -1:
            self.buffer2.fill(0)
            note = np.sign(np.sin(frequency2 * self.t)).astype("int16")
            self.buffer2 += note * 32767
            self.add_sound(self.channel2, self.buffer2)
        elif self.channel2.get_busy():
            self.channel2.stop()

    @staticmethod
    def add_sound(channel, buffer):
        sound = mixer.Sound(array=buffer)

        channel.stop()
        channel.play(sound, loops=-1)

    def calculate_channel(self, audio):
        frequency = self.base_frequency // (audio[1] + 1)
        control = audio[0]
        if control == 0 or control == 11:  # no sound
            return -1
        elif control == 1:
            pass  # 4 bit poly
        elif control == 2:
            frequency //= 15
            pass  # 4 bit poly
        elif control == 3:
            pass  # 5 bit poly
            pass  # 4 bit poly
        elif control == 4 or control == 5:
            if audio[1] == 0:
                return -1
            frequency //= 2
        elif control == 6 or control == 10:
            frequency //= 31
        elif control == 7 or control == 9:
            pass  # 5 bit poly
            frequency //= 2
        elif control == 8:
            pass  # 9 bit poly
        elif control == 10:
            frequency //= 31
        elif control == 12 or control == 13:
            frequency //= 6
        elif control == 14:
            frequency //= 93
        elif control == 15:
            pass  # 5 bit poly
            frequency //= 6
        return frequency
