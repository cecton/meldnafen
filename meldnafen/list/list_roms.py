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
                ("Controls: {self.props[name]}",
                    "submenu", [
                        ("Configure player %s" % i, "call",
                            partial(self.confgure_controls,
                                target='console', player=str(i)))
                        for i in range(1, self.props['players_number'] + 1)
                    ]),
                ("Controls: {self.game}",
                    "submenu", [
                        ("Configure player %s" % i, "call",
                            partial(self.confgure_controls,
                                target='game', player=str(i)))
                        for i in range(1, self.props['players_number'] + 1)
                    ] + [
                        ("Clear all", "call", self.remove_game_controls),
                    ]),
                ("Controls: {app.name}", "call",
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
        self.logger.debug(
            "Loading emulator %s: %d players",
            self.props['console'],
            self.props['players_number'])
        self.keyboard_mapping = {
            sdl2.SDL_SCANCODE_DOWN: self.next_option,
            sdl2.SDL_SCANCODE_UP: self.prev_option,
            sdl2.SDL_SCANCODE_RIGHT: self.switch_right,
            sdl2.SDL_SCANCODE_LEFT: self.switch_left,
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
        index = self.state['page'] * self.props['page_size'] + \
            self.state['select']
        return self.state['roms'][index]

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

    def next_option(self):
        if self.menu.active:
            return
        if not self.state['roms']:
            return
        if self.state['page'] == self.state['last_page']:
            edge = len(self.state['roms']) % self.props['page_size']
        else:
            edge = self.props['page_size']
        if self.state['select'] == edge - 1:
            return
        self.set_state({
            'select': self.state['select'] + 1,
        })

    def prev_option(self):
        if self.menu.active:
            return
        if not self.state['roms']:
            return
        if self.state['select'] == -1:
            return
        self.set_state({
            'select': self.state['select'] - 1,
        })

    def switch_right(self):
        if self.state['select'] == -1:
            self.next_emulator()
        else:
            self.next_page()

    def switch_left(self):
        if self.state['select'] == -1:
            self.prev_emulator()
        else:
            self.prev_page()

    def next_page(self):
        if self.menu.active:
            return
        if not self.state['roms']:
            return
        if self.state['page'] == self.state['last_page']:
            return
        self.set_state({
            'page': self.state['page'] + 1,
        })
        if self.state['page'] == self.state['last_page']:
            self.set_state({
                'select': min(
                    self.state['select'],
                    (len(self.state['roms']) % self.props['page_size']) - 1),
            })

    def prev_page(self):
        if self.menu.active:
            return
        if not self.state['roms']:
            return
        if self.state['page'] == 0:
            return
        self.set_state({
            'page': self.state['page'] - 1,
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
            'last_page': ceil(len(roms) / self.props['page_size']) - 1,
            'select': -1,
            'page': 0,
            'error': None,
        })

    def render(self):
        if self.menu.active:
            return
        x, y = self.props['x'], self.props['y']
        if self.state['select'] == -1:
            with self.app.tint(self.props['highlight']):
                self.app.write('font-12', x, y, "< %s >" % self.props['name'])
        else:
            self.app.write('font-12', x, y, "< %s >" % self.props['name'])
        y += self.props['line_space'] * 2
        if not self.state['roms']:
            self.app.write('font-12', x, y, "No rom found")
            return
        for i, rom in enumerate(islice(
                self.state['roms'],
                (self.props['page_size'] * self.state['page']),
                (self.props['page_size'] * (self.state['page'] + 1)))):
            if i == self.state['select']:
                with self.app.tint(self.props['highlight']):
                    self.app.write('font-12', x, y, rom)
            else:
                self.app.write('font-12', x, y, rom)
            y += self.props['line_space']
        y += self.props['line_space']
        self.app.write('font-12', x, y,
                "Page {} of {} ({} roms)".format(
                (self.state['page'] + 1),
                self.state['last_page'] + 1,
                len(self.state['roms'])))
        if self.state['error']:
            y += self.props['line_space']
            with self.app.tint((0xff, 0x00, 0x00, 0xff)):
                self.app.write('font-12', x, y, self.state['error'])
