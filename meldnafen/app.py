from itertools import chain
import os
import random
import sdl2
import sdl2ui
from sdl2ui.mixer import Mixer
import sdl2ui.mixins
from sdl2ui.debugger import Debugger
from sdl2ui.joystick import KeyboardJoystick

from meldnafen.menu import Menu
from meldnafen.list_roms import ListRoms
from meldnafen.vgm import VgmPlayer, VgmFile


class Meldnafen(sdl2ui.App, sdl2ui.mixins.ImmutableMixin):
    name = "Meldnafen"

    def _load_emulator_components(self):
        self.emulators = [
            self.add_component(ListRoms,
                emulator=emulator,
                border=10,
                page_size=15,
                line_space=10,
                highlight=(0xff, 0xff, 0x00, 0xff))
            for emulator in self.props['emulators']
        ]

    def startup(self):
        if self.props.get('startup'):
            for command in self.props['startup']:
                os.system(command)

    def _pick_random_bgm(self):
        if not self.props.get('musics') or not os.listdir(self.props['musics']):
            return None
        else:
            return random.choice(
                list(chain.from_iterable(
                    map(
                        lambda x: map(
                            lambda y: os.path.join(x[0], y),
                            x[2]),
                        os.walk(self.props['musics'])))))

    def _load_bgm(self):
        filepath = self._pick_random_bgm()
        if filepath:
            self.load_resource('bgm', filepath)
        if 'bgm' not in self.resources:
            return self.add_component(sdl2ui.NullComponent)
        elif isinstance(self.resources['bgm'], VgmFile):
            return self.add_component(VgmPlayer,
                resource='bgm',
                frequency=44100,
                format=sdl2.AUDIO_S16MSB,
                channels=2,
                chunksize=4096)
        else:
            return self.mixer.open('bgm', loops=-1)

    def init(self):
        self.mixer = self.add_component(Mixer)
        self.load_resource('font-12', 'font-12.png')
        self.resources['font-12'].make_font(
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!?("
            ")[]~-_+@:/'., ")
        self.startup()
        sdl2.SDL_ShowCursor(sdl2.SDL_FALSE)
        sdl2.SDL_SetHint(sdl2.SDL_HINT_JOYSTICK_ALLOW_BACKGROUND_EVENTS, b"1")
        self.command = None
        self.add_component(KeyboardJoystick,
            index=0,
            keyboard_mapping={
                k: getattr(sdl2, v)
                for k, v in self.props['joystick']
            }).enable()
        self._load_emulator_components()
        self.menu = self.add_component(Menu,
            actions=self.props['menu_actions'],
            highlight=(0x00, 0x00, 0xff, 0xff),
            line_space=10,
            border=10)
        self.debugger = self.add_component(Debugger,
            x=self.menu.x - 8,
            y=self.menu.y - 8)
        self.keyboard_mapping = {
            sdl2.SDL_SCANCODE_Q: self.app.quit,
            sdl2.SDL_SCANCODE_D: self.toggle_debug_mode,
            sdl2.SDL_SCANCODE_ESCAPE: self.toggle_menu,
        }
        self.bgm = self._load_bgm()
        self.register_event_handler(sdl2.SDL_KEYDOWN, self.keypress)
        self.set_state({'emulator': 0})
        self.emulators[0].enable()
        self.bgm.enable()

    def run_command(self, command, cwd=None):
        if cwd is not None:
            os.chdir(cwd)
        self.command = command
        self.quit()

    def keypress(self, event):
        if event.key.keysym.scancode in self.keyboard_mapping:
            self.keyboard_mapping[event.key.keysym.scancode]()

    def toggle_debug_mode(self):
        self.debugger.toggle()

    def toggle_menu(self):
        self.emulators[self.state['emulator']].toggle()
        self.menu.toggle()
        self.bgm.toggle()

    def next_emulator(self):
        self.show_emulator((self.state['emulator'] + 1) % len(self.emulators))

    def prev_emulator(self):
        self.show_emulator((self.state['emulator'] - 1) % len(self.emulators))

    def show_emulator(self, index):
        self.emulators[self.state['emulator']].disable()
        self.emulators[index].enable()
        self.set_state({'emulator': index})
