from __future__ import division

import fnmatch
from functools import partial
from itertools import islice
from math import ceil
import os
import re
import sdl2
import sdl2ui
import sdl2ui.mixins

from meldnafen.exceptions import MissingControls
from meldnafen.config.controls import Controls
from meldnafen.list.menu import Menu


class ListRoms(sdl2ui.Component, sdl2ui.mixins.ImmutableMixin):
    def generate_menu(self):
        return [
            ("Controls", "submenu", [
                ("Controls for {self.props[console]}",
                    "submenu", [
                        ("Configure player %s" % i, "call",
                            partial(self.confgure_controls,
                                target='console', player=str(i)))
                        for i in range(1, self.props['players_number'] + 1)
                    ]),
                ("Controls for {self.game}",
                    "submenu", [
                        ("Configure player %s" % i, "call",
                            partial(self.confgure_controls,
                                target='game', player=str(i)))
                        for i in range(1, self.props['players_number'] + 1)
                    ]),
                ("Remove controls for {self.game}", "call",
                    self.remove_game_controls),
                ("Controls of {app.name}", "call",
                    self.app.activate_joystick_configuration)
            ]),
            ("Smooth: {app.settings[smooth]}", "call", self.app.toggle_smooth),
            ("FPS: {app.debugger.active}", "call", self.app.debugger.toggle),
        ]

    def load_joystick_components(self):
        self.joystick_configure = {}
        for player in range(1, self.props['players_number'] + 1):
            controls = self.props['controls'].copy()
            if player == 1:
                controls.extend([
                    ("enable_hotkey", "Emulator Hotkey"),
                    ("menu_toggle",
                        "Emulator Menu (after pressing the hotkey)"),
                ])
            # NOTE: add the component to self.app, we don't want it to be
            # deactivated when the rest of the application is disabled
            self.joystick_configure[str(player)] = self.app.add_component(
                Controls,
                line_space=10,
                on_finish=self.finish_joystick_configuration,
                controls=controls,
                x=self.props['x'],
                y=self.props['y'])

    def init(self):
        self.keyboard_mapping = {
            sdl2.SDL_SCANCODE_DOWN: self.next_rom,
            sdl2.SDL_SCANCODE_UP: self.prev_rom,
            sdl2.SDL_SCANCODE_PAGEDOWN: self.next_page,
            sdl2.SDL_SCANCODE_PAGEUP: self.prev_page,
            sdl2.SDL_SCANCODE_RIGHT: self.next_emulator,
            sdl2.SDL_SCANCODE_LEFT: self.prev_emulator,
            sdl2.SDL_SCANCODE_RETURN: self.run_emulator,
            sdl2.SDL_SCANCODE_ESCAPE: self.show_menu,
        }
        self.menu = self.add_component(Menu,
            menu=self.generate_menu(),
            highlight=self.props['highlight'],
            line_space=10,
            x=self.props['x'],
            y=self.props['y'],
            on_activated=self.props['on_menu_activated'],
            on_deactivated=self.props['on_menu_deactivated'])
        self.load_joystick_components()
        self.register_event_handler(sdl2.SDL_KEYDOWN, self.keypress)
        self.update_list()

    @property
    def game(self):
        return self.state['roms'][self.state['selected']]

    def confgure_controls(self, **kwargs):
        self.app.lock()
        self.joystick_configure[kwargs['player']].start(**kwargs)

    def update_joystick_configuration(self,
            joystick=None, player=None, target=None, config=None):
        if target == 'console':
            self.app.settings.setdefault('controls', {})\
                .setdefault(target, {})\
                .setdefault(self.props['console'], {})\
                .setdefault(player, {})\
                [joystick.guid] = config
        else:
            self.app.settings.setdefault('controls', {})\
                .setdefault(target, {})\
                .setdefault(self.props['console'], {})\
                .setdefault(self.game, {})\
                .setdefault(player, {})\
                [joystick.guid] = config

    def remove_game_controls(self):
        self.app.settings['controls']\
            .setdefault('game', {})\
            .pop(self.props['console'], None)
        self.menu.disable()

    def finish_joystick_configuration(self, **kwargs):
        if kwargs:
            self.update_joystick_configuration(**kwargs)
        self.app.unlock()

    def keypress(self, event):
        if event.key.keysym.scancode in self.keyboard_mapping:
            self.keyboard_mapping[event.key.keysym.scancode]()

    def next_rom(self):
        if self.menu.active:
            return
        if not self.state['roms']:
            return
        self.set_state({
            'selected':
                0
                if self.state['selected'] == len(self.state['roms']) - 1
                else self.state['selected'] + 1,
        })

    def prev_rom(self):
        if self.menu.active:
            return
        if not self.state['roms']:
            return
        self.set_state({
            'selected':
                len(self.state['roms']) - 1
                if self.state['selected'] == 0
                else self.state['selected'] - 1,
        })

    def next_page(self):
        if self.menu.active:
            return
        if not self.state['roms']:
            return
        self.set_state({
            'selected': min(
                self.state['selected'] + self.props['page_size'],
                len(self.state['roms']) - 1),
        })

    def prev_page(self):
        if self.menu.active:
            return
        if not self.state['roms']:
            return
        self.set_state({
            'selected': max(
                self.state['selected'] - self.props['page_size'], 0),
        })

    def next_emulator(self):
        if self.menu.active:
            return
        self.props['on_next_emulator']()

    def prev_emulator(self):
        if self.menu.active:
            return
        self.props['on_prev_emulator']()

    def run_emulator(self):
        if self.menu.active:
            return
        if not self.state['roms']:
            return
        try:
            self.app.run_emulator(
                self.props,
                os.path.expanduser(self.props['path']),
                self.game)
        except MissingControls as exc:
            self.set_state({
                'error': exc.message,
            })

    def show_menu(self):
        if self.menu.active:
            return
        if not self.state['roms']:
            return
        self.menu.set_state({
            'vars': {
                'self': self,
                'app': self.app,
            },
        })
        self.menu.enable()

    def update_list(self):
        includes = [
            re.compile(fnmatch.translate(x))
            for x in (
                self.props['include'].split(';')
                if self.props.get('include')
                else []
            )
        ]
        excludes = [
            re.compile(fnmatch.translate(x))
            for x in (
                self.props['exclude'].split(';')
                if self.props.get('exclude')
                else []
            )
        ]
        roms = sorted(filter(
            lambda x: (not any(y.match(x) for y in excludes) or
                any(y.match(x) for y in includes)),
            os.listdir(os.path.expanduser(self.props['path']))))
        self.set_state({
            'roms': roms,
            'last_page': ceil(len(roms) / self.props['page_size']),
            'selected': 0,
            'error': 0,
        })

    def render(self):
        if self.menu.active:
            return
        x, y = self.props['x'], self.props['y']
        self.app.write('font-12', x, y, self.props['name'])
        y += self.props['line_space'] * 2
        if not self.state['roms']:
            self.app.write('font-12', x, y, "No rom found")
            return
        page, selected = divmod(
            self.state['selected'], self.props['page_size'])
        for i, rom in enumerate(islice(
                self.state['roms'],
                (self.props['page_size'] * page),
                (self.props['page_size'] * (page + 1)))):
            if i == selected:
                with self.app.tint(self.props['highlight']):
                    self.app.write('font-12', x, y, rom)
            else:
                self.app.write('font-12', x, y, rom)
            y += self.props['line_space']
        y += self.props['line_space']
        self.app.write('font-12', x, y,
            "Page %d of %d (%d roms)" % (
                (page + 1), self.state['last_page'], len(self.state['roms'])))
        if self.state['error']:
            y += self.props['line_space']
            with self.app.tint((0xff, 0x00, 0x00, 0xff)):
                self.app.write('font-12', x, y, self.state['error'])
