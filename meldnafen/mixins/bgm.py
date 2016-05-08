from itertools import chain
import os
import random
import sdl2
import sdl2ui

from meldnafen.vgm import VgmPlayer, VgmFile


class BgmMixin:
    def init(self):
        filepath = self.pick_random_bgm()
        if filepath:
            self.load_resource('bgm', filepath)
        if 'bgm' not in self.resources:
            self.bgm = self.add_component(sdl2ui.NullComponent)
        elif isinstance(self.resources['bgm'], VgmFile):
            self.bgm = self.add_component(VgmPlayer,
                resource='bgm',
                frequency=44100,
                format=sdl2.AUDIO_S16MSB,
                channels=2,
                chunksize=4096)
        else:
            self.mixer = self.add_component(Mixer)
            self.bgm = self.mixer.open('bgm', loops=-1)

    def activate(self):
        self.bgm.enable()

    def pick_random_bgm(self):
        if not self.settings.get('musics'):
            return None
        musics_dir = os.path.expanduser(self.settings['musics'])
        if not (os.path.exists(musics_dir) and os.listdir(musics_dir)):
            return None
        else:
            return random.choice(
                list(chain.from_iterable(
                    map(
                        lambda x: map(
                            lambda y: os.path.join(x[0], y),
                            x[2]),
                        os.walk(musics_dir)))))
