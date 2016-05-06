from itertools import chain
import os
import random
import re
import sdl2
import sdl2ui
from sdl2ui.mixer import Mixer
import sdl2ui.mixins
from sdl2ui.debugger import Debugger
from sdl2ui.joystick import JoystickManager

import meldnafen
from meldnafen.config.controls import Controls
from meldnafen.consoles import consoles
from meldnafen.exceptions import MissingControls
from meldnafen.joystick import MenuJoystick
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
    'next_page': sdl2.SDL_SCANCODE_PAGEDOWN,
    'prev_page': sdl2.SDL_SCANCODE_PAGEUP,
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
            self.mixer = self.add_component(Mixer)
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
        self.bgm = self._load_bgm()
        self.debugger = self.add_component(Debugger,
            x=self.x - 8,
            y=self.y - 8)
        self.joystick_manager = self.add_component(JoystickManager)
        self.joystick = self.add_component(MenuJoystick,
            manager=self.joystick_manager,
            index=0,
            on_joystick_added=self.menu_joystick_added,
            on_joystick_removed=self.menu_joystick_removed)
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
        self.register_event_handler(sdl2.SDL_KEYDOWN, self.keypress)
        self.register_event_handler(
            sdl2.SDL_JOYDEVICEREMOVED, self.joy_removed)

    def activate(self):
        self.set_state({
            'emulator': 0,
            'command': None,
            'controls': None,
            'menu_joystick_connected': False,
        })
        self.bgm.enable()
        self.unlock()

    def quit(self, exception=None):
        if exception is None:
            try:
                meldnafen.write_config(self.settings)
            except Exception:
                self.logger.error("Could not save configuration")
        super(Meldnafen, self).quit()

    def get_player_controls(self, controls):
        config = {}
        for player in map(str, range(1, 9)):
            if not player in controls:
                continue
            self.logger.debug("Configuring joystick for player %s...", player)
            for index, joystick in self.joystick_manager.joysticks.items():
                if joystick.guid in controls[player]:
                    self.logger.debug("Found joystick %s in controls",
                        joystick.guid)
                    config[player] = merge_dict(
                        {"joypad_index": index},
                        controls[player][joystick.guid])
                    break
            else:
                self.logger.debug("No joystick configuration available")
        return config

    def run_emulator(self, console, path, game):
        command = consoles[console]['exec'] + [os.path.join(path, game)]
        controls = {}
        try:
            controls.update(self.get_player_controls(
                self.settings['controls']['console'][console]))
        except KeyError:
            raise MissingControls()
        try:
            controls.update(self.get_player_controls(
                self.settings['controls']['game'][console][game]))
        except KeyError:
            pass
        self.set_state({
            'command': command,
            'controls': controls,
        })
        self.quit()

    def keypress(self, event):
        if event.key.keysym.scancode in self.keyboard_mapping:
            self.keyboard_mapping[event.key.keysym.scancode]()

    def joy_removed(self, event):
        if not self.joystick_manager.joysticks:
            self.set_state({
                'menu_joystick_connected': False,
            })
            self.lock()
            self.joystick_configure.disable()

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

    def menu_joystick_added(self, joystick):
        if joystick.guid not in self.settings['controls'].get('menu', {}):
            if not self.joystick.available:
                self.activate_joystick_configuration()
        else:
            self.load_joystick_configuriation(joystick)
            if self.joystick.available and self.joystick_configure.active:
                self.joystick_configure.disable()
                self.unlock()
        self.set_state({
            'menu_joystick_connected': True,
        })

    def menu_joystick_removed(self):
        if self.joystick_manager.joysticks and not self.joystick.available:
            self.activate_joystick_configuration()

    def activate_joystick_configuration(self):
        self.lock()
        self.joystick_configure.start()

    def load_joystick_configuriation(self, joystick):
        self.joystick.load(joystick, {
            v: JOYSTICK_ACTIONS[re.sub(r"(_btn|_axis)$", "", k)]
            for k, v in
                self.settings['controls']['menu'][joystick.guid].items()
        })

    def update_joystick_configuration(self, joystick, config):
        self.settings['controls']\
            .setdefault('menu', {})[joystick.guid] = config
        self.load_joystick_configuriation(joystick)

    def finish_joystick_configuration(self, joystick=None, config=None):
        if config:
            self.update_joystick_configuration(joystick, config)
        self.unlock()

    def render(self):
        if not self.state['menu_joystick_connected']:
            with self.tint((0xff, 0x00, 0x00, 0xff)):
                self.write('font-12', self.x, self.y, "No joystick connected")
