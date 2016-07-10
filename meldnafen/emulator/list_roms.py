from __future__ import division

import fnmatch
from itertools import islice
from math import ceil
import os
import re
import sdl2
import sdl2ui
import sdl2ui.mixins

from meldnafen.exceptions import MissingControls


class ListRoms(sdl2ui.Component, sdl2ui.mixins.ImmutableMixin):
    def init(self):
        self.keyboard_mapping = {
            sdl2.SDL_SCANCODE_DOWN: self.next_option,
            sdl2.SDL_SCANCODE_UP: self.prev_option,
            sdl2.SDL_SCANCODE_RIGHT: self.switch_right,
            sdl2.SDL_SCANCODE_LEFT: self.switch_left,
            sdl2.SDL_SCANCODE_RETURN: self.run_emulator,
            sdl2.SDL_SCANCODE_ESCAPE: self.show_menu,
        }
        self.register_event_handler(sdl2.SDL_KEYDOWN, self.keypress)
        self.update_list()

    @property
    def game(self):
        index = self.state['page'] * self.props['page_size'] + \
            self.state['select']
        return self.state['roms'][index]

    def keypress(self, event):
        if event.key.keysym.scancode in self.keyboard_mapping:
            self.keyboard_mapping[event.key.keysym.scancode]()

    def next_option(self):
        if not self.state['roms']:
            return
        if self.state['page'] == self.state['last_page']:
            edge = len(self.state['roms']) % self.props['page_size']
        else:
            edge = self.props['page_size'] + 1
        if self.state['select'] == edge - 1:
            return
        self.set_state({
            'select': self.state['select'] + 1,
        })

    def prev_option(self):
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
        if not self.state['roms']:
            return
        if self.state['page'] == 0:
            return
        self.set_state({
            'page': self.state['page'] - 1,
        })

    def next_emulator(self):
        self.props['on_next_emulator']()

    def prev_emulator(self):
        self.props['on_prev_emulator']()

    def run_emulator(self):
        if not self.state['roms']:
            return
        if not -1 < self.state['select'] < self.props['page_size']:
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
        if not self.state['roms']:
            return
        if not -1 < self.state['select'] < self.props['page_size']:
            return
        self.props['show_menu']({
            'game': self.game,
            'app': self.app,
        })

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

    def render_footer(self, x, y):
        if self.state['last_page'] > 0:
            self.app.write('font-12', x, y,
                "< Page {} of {} ({} roms) >".format(
                (self.state['page'] + 1),
                self.state['last_page'] + 1,
                len(self.state['roms'])))
        else:
            self.app.write('font-12', x, y,
                "{} rom(s)".format(len(self.state['roms'])))

    def render(self):
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
        if self.state['select'] == self.props['page_size']:
            with self.app.tint(self.props['highlight']):
                self.render_footer(x, y)
        else:
            self.render_footer(x, y)
        if self.state['error']:
            y += self.props['line_space']
            with self.app.tint((0xff, 0x00, 0x00, 0xff)):
                self.app.write('font-12', x, y, self.state['error'])
