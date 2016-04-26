from itertools import chain
import os
import random
import sdl2
import sdl2ui
from sdl2ui.mixer import Mixer
import sdl2ui.mixins
from sdl2ui.debugger import Debugger
from sdl2ui.joystick import JoystickManager, KeyboardJoystick

import meldnafen
from meldnafen.config.controls import Controls
from meldnafen.consoles import consoles
from meldnafen.list.list_roms import ListRoms
from meldnafen.vgm import VgmPlayer, VgmFile


JOYSTICK_ACTIONS = {
    'up': sdl2.SDL_SCANCODE_UP,
    'down': sdl2.SDL_SCANCODE_DOWN,
    'left': sdl2.SDL_SCANCODE_LEFT,
    'right': sdl2.SDL_SCANCODE_RIGHT,
    'ok': sdl2.SDL_SCANCODE_RETURN,
    'cancel': sdl2.SDL_SCANCODE_BACKSPACE,
    'menu': sdl2.SDL_SCANCODE_ESCAPE,
    'next_page': sdl2.SDL_SCANCODE_PAGEUP,
    'prev_page': sdl2.SDL_SCANCODE_PAGEDOWN,
}


def merge_dict(*dicts):
    result = {}
    for d in dicts:
        result.update(d)
    return result


class Meldnafen(sdl2ui.App, sdl2ui.mixins.ImmutableMixin):
    name = "Meldnafen"

    @property
    def x(self):
        return int((self.app.viewport.w - 256) / 2 + self.settings['border'])

    @property
    def y(self):
        return int((self.app.viewport.h - 224) / 2 + self.settings['border'])

    @property
    def settings(self):
        return self.props['settings']

    def _load_emulator_components(self):
        self.emulators = [
            self.add_component(ListRoms,
                **merge_dict(consoles[emulator['console']], emulator.items()),
                border=10,
                page_size=15,
                line_space=10,
                highlight=(0xff, 0xff, 0x00, 0xff),
                x=self.x,
                y=self.y)
            for emulator in self.settings['emulators']
        ]

    def startup(self):
        if self.settings.get('startup'):
            for command in self.settings['startup']:
                os.system(command)

    def _pick_random_bgm(self):
        if not self.settings.get('musics'):
            return None
        musics_dir = os.path.expanduser(self.settings['musics'])
        if not os.listdir(musics_dir):
            return None
        else:
            return random.choice(
                list(chain.from_iterable(
                    map(
                        lambda x: map(
                            lambda y: os.path.join(x[0], y),
                            x[2]),
                        os.walk(musics_dir)))))

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
        self.command = None
        self.keyboard_mapping = {
            sdl2.SDL_SCANCODE_Q: self.app.quit,
            sdl2.SDL_SCANCODE_D: self.toggle_debug_mode,
        }
        self.startup()
        sdl2.SDL_ShowCursor(sdl2.SDL_FALSE)
        sdl2.SDL_SetHint(sdl2.SDL_HINT_JOYSTICK_ALLOW_BACKGROUND_EVENTS, b"1")
        self.load_resource('font-12', 'font-12.png')
        self.resources['font-12'].make_font(
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!?("
            ")[]<>~-_+@:/'., ")
        self.register_event_handler(sdl2.SDL_KEYDOWN, self.keypress)
        self.mixer = self.add_component(Mixer)
        self.bgm = self._load_bgm()
        self.debugger = self.add_component(Debugger,
            x=self.x - 8,
            y=self.y - 8)
        self.joystick_manager = self.add_component(JoystickManager)
        self.joystick = self.add_component(KeyboardJoystick,
            manager=self.joystick_manager,
            index=0)
        self.joystick_configure = self.add_component(Controls,
            line_space=10,
            cancellable=False,
            countdown=8,
            on_finish=self.finish_joystick_configuration,
            controls=[
                ('up', "Up"),
                ('down', "Down"),
                ('left', "Left"),
                ('right', "Right"),
                ('ok', "OK"),
                ('cancel', "Cancel"),
                ('menu', "Menu"),
                ('next_page', "Next page"),
                ('prev_page', "Previous page"),
            ],
            x=self.x,
            y=self.y)
        self._load_emulator_components()

    def activate(self):
        self.set_state({'emulator': 0})
        self.emulators[0].enable()
        self.joystick.enable()
        if not self.settings['controls'].get('menu'):
            self.activate_joystick_configuration()
        else:
            self.reload_joystick_configuriation()
        self.bgm.enable()

    def quit(self):
        try:
            meldnafen.write_config(self.settings)
        except Exception:
            raise
            self.logger.error("Could not save configuration")
        super(Meldnafen, self).quit()

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

    def next_emulator(self):
        self.show_emulator((self.state['emulator'] + 1) % len(self.emulators))

    def prev_emulator(self):
        self.show_emulator((self.state['emulator'] - 1) % len(self.emulators))

    def show_emulator(self, index):
        self.emulators[self.state['emulator']].disable()
        self.emulators[index].enable()
        self.set_state({'emulator': index})

    def lock(self):
        self.emulators[self.state['emulator']].disable()
        self.joystick.disable()

    def unlock(self):
        self.emulators[self.state['emulator']].enable()
        self.joystick.enable()

    def activate_joystick_configuration(self):
        self.lock()
        self.joystick_configure.enable()

    def reload_joystick_configuriation(self):
        self.joystick.load({
            v: JOYSTICK_ACTIONS[k]
            for k, v in self.settings['controls']['menu'].items()
        })

    def update_joystick_configuration(self, config):
        self.settings['controls']['menu'] = config
        self.reload_joystick_configuriation()

    def finish_joystick_configuration(self, config=None):
        if config:
            self.update_joystick_configuration(config)
        self.joystick_configure.disable()
        self.unlock()
