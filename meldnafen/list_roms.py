from __future__ import division

import fnmatch
from itertools import islice
from math import ceil
import os
import re
import sdl2
import sdl2ui
import sdl2ui.mixins


class ListRoms(sdl2ui.Component, sdl2ui.mixins.ImmutableMixin):
    @property
    def x(self):
        return int((self.app.viewport.w - 256) / 2 + self.props['border'])

    @property
    def y(self):
        return int((self.app.viewport.h - 224) / 2 + self.props['border'])

    def init(self):
        self.keyboard_mapping = {
            sdl2.SDL_SCANCODE_DOWN: self.next_rom,
            sdl2.SDL_SCANCODE_UP: self.prev_rom,
            sdl2.SDL_SCANCODE_PAGEDOWN: self.next_page,
            sdl2.SDL_SCANCODE_PAGEUP: self.prev_page,
            sdl2.SDL_SCANCODE_RIGHT: self.next_emulator,
            sdl2.SDL_SCANCODE_LEFT: self.prev_emulator,
            sdl2.SDL_SCANCODE_RETURN: self.run_emulator,
        }
        self.register_event_handler(sdl2.SDL_KEYDOWN, self.keypress)
        self.update_list()

    def keypress(self, event):
        if event.key.keysym.scancode in self.keyboard_mapping:
            self.keyboard_mapping[event.key.keysym.scancode]()

    def next_rom(self):
        if not self.state['roms']:
            return
        self.set_state({
            'selected':
                0
                if self.state['selected'] == len(self.state['roms']) - 1
                else self.state['selected'] + 1,
        })

    def prev_rom(self):
        if not self.state['roms']:
            return
        self.set_state({
            'selected':
                len(self.state['roms']) - 1
                if self.state['selected'] == 0
                else self.state['selected'] - 1,
        })

    def next_page(self):
        if not self.state['roms']:
            return
        self.set_state({
            'selected': min(
                self.state['selected'] + self.props['page_size'],
                len(self.state['roms']) - 1),
        })

    def prev_page(self):
        if not self.state['roms']:
            return
        self.set_state({
            'selected': max(
                self.state['selected'] - self.props['page_size'], 0),
        })

    def next_emulator(self):
        self.parent.next_emulator()

    def prev_emulator(self):
        self.parent.prev_emulator()

    def run_emulator(self):
        if not self.state['roms']:
            return
        self.app.run_command(
            self.props['emulator']['exec'] +
            [self.state['roms'][self.state['selected']]],
            cwd=self.props['emulator']['path'])

    def update_list(self):
        includes = [
            re.compile(fnmatch.translate(x))
            for x in (
                self.props['emulator']['include'].split(';')
                if self.props['emulator'].get('include')
                else []
            )
        ]
        excludes = [
            re.compile(fnmatch.translate(x))
            for x in (
                self.props['emulator']['exclude'].split(';')
                if self.props['emulator'].get('exclude')
                else []
            )
        ]
        roms = sorted(filter(
            lambda x: (not any(y.match(x) for y in excludes) or
                any(y.match(x) for y in includes)),
            os.listdir(self.props['emulator']['path'])))
        self.set_state({
            'roms': roms,
            'last_page': ceil(len(roms) / self.props['page_size']),
            'selected': 0,
        })

    def render(self):
        x, y = self.x, self.y
        self.app.write('font-12', x, y, self.props['emulator']['name'])
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
