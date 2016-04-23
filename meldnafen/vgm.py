import os
import re
import sdl2
import sdl2ui
from sdl2ui.audio import AudioDevice
import vgmplayer


class VgmFile(sdl2ui.resource.BaseResource):
    regex = re.compile(r".*\.(vgm(\.gz)?|vgz)$")

    def load(self):
        OUT, IN = os.pipe()
        self.t = vgmplayer.PlayThread(self.filepath, IN, 100)
        self.t.start()
        self.sample = open(OUT, 'rb')


class VgmPlayer(AudioDevice):
    def load(self):
        self.stream = self.app.resources[self.props['resource']].sample

    def unload(self):
        self.stream.close()

    def callback(self, length):
        return self.stream.read(length)
