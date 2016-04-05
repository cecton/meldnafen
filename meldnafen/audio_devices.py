import os
import sdl2
from sdl2ui.audio import AudioDevice


class Bgm(AudioDevice):
    def load(self):
        import vgmplayer
        OUT, IN = os.pipe()
        self.t = vgmplayer.PlayThread(self.props['filepath'], IN, 100)
        self.t.start()
        self.stream = open(OUT, 'rb')

    def unload(self):
        self.stream.close()

    def callback(self, length):
        return self.stream.read(length)
