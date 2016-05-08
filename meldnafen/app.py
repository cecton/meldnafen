import os
import sdl2
import sdl2ui
from sdl2ui.mixer import Mixer
import sdl2ui.mixins
from sdl2ui.debugger import Debugger
from sdl2ui.joystick import JoystickManager

import meldnafen
from meldnafen.joystick import MenuJoystick
from meldnafen.mixins.bgm import BgmMixin
from meldnafen.mixins.controls import ControlsMixin
from meldnafen.mixins.emulator import EmulatorMixin


class Meldnafen(
        sdl2ui.App, sdl2ui.mixins.ImmutableMixin,
        BgmMixin, EmulatorMixin, ControlsMixin):

    name = "Meldnafen"

    @property
    def x(self):
        return int((self.app.viewport.w - 256) / 2 + self.settings['border'])

    @property
    def y(self):
        return int((self.app.viewport.h - 224) / 2 + self.settings['border'])

    @property
    def settings(self):
        return self.state['settings']

    def startup(self):
        if self.settings.get('startup'):
            for command in self.settings['startup']:
                os.system(command)

    def init(self):
        self.set_state({
            'settings': self.props['settings'].copy(),
        })
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
        self.debugger = self.add_component(Debugger,
            x=self.x - 8,
            y=self.y - 8)
        self.joystick_manager = self.add_component(JoystickManager)
        self.joystick = self.add_component(MenuJoystick,
            manager=self.joystick_manager,
            index=0,
            on_joystick_added=self.menu_joystick_added,
            on_joystick_removed=self.menu_joystick_removed)
        self.register_event_handler(sdl2.SDL_KEYDOWN, self.keypress)

    def activate(self):
        if self.settings['debug']:
            self.debugger.enable()

    def quit(self, exception=None):
        if not isinstance(exception, Exception):
            try:
                meldnafen.write_config(self.settings)
            except Exception:
                self.logger.error("Could not save configuration")
            else:
                self.logger.debug("Configuration saved")
        sdl2ui.App.quit(self)

    def keypress(self, event):
        if event.key.keysym.scancode in self.keyboard_mapping:
            self.keyboard_mapping[event.key.keysym.scancode]()

    def toggle_debug_mode(self):
        self.debugger.toggle()

    def lock(self):
        self.emulators[self.state['emulator']].disable()
        self.joystick.disable()

    def unlock(self):
        self.emulators[self.state['emulator']].enable()
        self.joystick.enable()
