from __future__ import division

import fnmatch
from itertools import islice, chain
import json
import logging
from math import ceil
import os
import random
import re
import sdl2
import sdl2ui
import sdl2ui.ext.joystick


command = None
with open(os.path.expanduser('~/.config/meldnafenrc')) as rc:
    settings = json.load(rc)
    if settings.get('musics'):
        settings['musics'] = os.path.expanduser(settings['musics'])

def pick_random_bgm():
    return random.choice(
        list(chain.from_iterable(
            map(
                lambda x: map(
                    lambda y: os.path.join(x[0], y),
                    x[2]),
                os.walk(settings['musics'])))))


class MenuComponent(sdl2ui.ImmutableComponent):
    @property
    def _x(self):
        return int((self.app.viewport.w - 256) / 2 + self.props['border'])

    @property
    def _y(self):
        return int((self.app.viewport.h - 224) / 2 + self.props['border'])

    def init(self):
        self.keyboard_mapping = {
            sdl2.SDL_SCANCODE_UP: self.previous_item,
            sdl2.SDL_SCANCODE_DOWN: self.next_item,
            sdl2.SDL_SCANCODE_RETURN: self.run_command,
        }
        self.register_event_handler(sdl2.SDL_KEYDOWN, self.keypress)
        self.set_state({'select': 0})

    def run_command(self):
        global command
        _, command = self.props['actions'][self.props['select']]
        self.app.quit()

    def keypress(self, event):
        if event.key.keysym.scancode in self.keyboard_mapping:
            self.keyboard_mapping[event.key.keysym.scancode]()

    def previous_item(self):
        self.set_state({
            'select':
                len(self.props['actions']) - 1
                if self.props['select'] >= len(self.props['actions'])
                else self.props['select'] - 1,
        })

    def next_item(self):
        self.set_state({
            'select':
                0
                if self.props['select'] >= len(self.props['actions'])
                else self.props['select'] + 1,
        })

    def render(self):
        x, y = self._x, self._y
        for i, (label, _) in enumerate(self.props['actions']):
            if i == self.props['select']:
                with self.app.tint(self.props['highlight']):
                    self.app.write('font-6', x, y, label)
            else:
                self.app.write('font-6', x, y, label)
            y += self.props['line_space']


class Bgm(sdl2ui.audio.AudioDevice):
    frequency = 44100
    format = sdl2.AUDIO_S16MSB
    channels = 2
    chunksize = 4096

    def init(self):
        import vgmplayer
        OUT, IN = os.pipe()
        self.t = vgmplayer.PlayThread(pick_random_bgm(), IN, 100)
        self.t.start()
        self.stream = open(OUT, 'rb')

    def callback(self, length):
        return self.stream.read(length)


class ListRomsComponent(sdl2ui.ImmutableComponent):
    @property
    def _x(self):
        return int((self.app.viewport.w - 256) / 2 + self.props['border'])

    @property
    def _y(self):
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
        self.set_state({
            'selected':
                0
                if self.props['selected'] == len(self.props['roms']) - 1
                else self.props['selected'] + 1,
        })

    def prev_rom(self):
        self.set_state({
            'selected':
                len(self.props['roms']) - 1
                if self.props['selected'] == 0
                else self.props['selected'] - 1,
        })

    def next_page(self):
        self.set_state({
            'selected': min(
                self.props['selected'] + self.props['page_size'],
                len(self.props['roms']) - 1),
        })

    def prev_page(self):
        self.set_state({
            'selected': max(
                self.props['selected'] - self.props['page_size'], 0),
        })

    def next_emulator(self):
        self.app.components['main'].next_emulator()

    def prev_emulator(self):
        self.app.components['main'].prev_emulator()

    def run_emulator(self):
        if not self.props['roms']:
            return
        self.app.components['main'].run_emulator(
            self.props['emulator'],
            self.props['roms'][self.props['selected']])

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
        x, y = self._x, self._y
        self.app.write('font-6', x, y, self.props['emulator']['name'])
        y += self.props['line_space'] * 2
        if not self.props['roms']:
            self.app.write('font-6', x, y, "No rom found")
            return
        page, selected = divmod(
            self.props['selected'], self.props['page_size'])
        for i, rom in enumerate(islice(
                self.props['roms'],
                (self.props['page_size'] * page),
                (self.props['page_size'] * (page + 1)))):
            if i == selected:
                with self.app.tint(self.props['highlight']):
                    self.app.write('font-6', x, y, rom)
            else:
                self.app.write('font-6', x, y, rom)
            y += self.props['line_space']
        y += self.props['line_space']
        self.app.write('font-6', x, y,
            "Page %d of %d (%d roms)" % (
                (page + 1), self.props['last_page'], len(self.props['roms'])))


class MainComponent(sdl2ui.ImmutableComponent):
    def init(self):
        self.keyboard_mapping = {
            sdl2.SDL_SCANCODE_Q: self.app.quit,
            sdl2.SDL_SCANCODE_D: self.toggle_debug_mode,
            sdl2.SDL_SCANCODE_ESCAPE: self.toggle_menu,
        }
        self.register_event_handler(sdl2.SDL_KEYDOWN, self.keypress)
        self.select_emulator(0)
        if self.props['musics'] and os.listdir(self.props['musics']):
            self.bgm = self.app.open_audio_device(Bgm)

    def keypress(self, event):
        if event.key.keysym.scancode in self.keyboard_mapping:
            self.keyboard_mapping[event.key.keysym.scancode]()

    def toggle_debug_mode(self):
        self.app.components['debug'].toggle()

    def toggle_menu(self):
        self.app.components['list-%d' % self.props['emulator']].toggle()
        self.app.components['menu'].toggle()
        self.bgm.toggle()

    def next_emulator(self):
        self.select_emulator(
            (self.props['emulator'] + 1) % len(self.props['emulators']))

    def prev_emulator(self):
        self.select_emulator(
            (self.props['emulator'] - 1) % len(self.props['emulators']))

    def select_emulator(self, index):
        if 'emulator' in self.props:
            self.app.components['list-%d' % self.props['emulator']].hide()
        self.app.components['list-%d' % index].show()
        self.set_state({'emulator': index})

    def run_emulator(self, emulator, rom):
        global command
        os.chdir(emulator['path'])
        command = emulator['exec'] + [rom]
        self.app.quit()


class Joystick(sdl2ui.ext.joystick.BaseKeyboardJoystick):
    mapping = {
        button: getattr(sdl2, scancode_name)
        for button, scancode_name in settings['joystick']
    }


class Meldnafen(sdl2ui.App):
    width = settings.get('width', 640)
    height = settings.get('height', 480)
    fps = 30
    name = "Meldnafen"
    default_extensions = [Joystick]
    window_flags = settings.get('window', 0)
    renderer_flags = sdl2.SDL_RENDERER_SOFTWARE
    init_flags = sdl2.SDL_INIT_VIDEO | sdl2.SDL_INIT_AUDIO

    _zoom = settings.get('zoom')

    def get_zoom(self):
        if self._zoom:
            return self._zoom
        else:
            return max(min(int(self.width / 256), int(self.height / 224)), 1)

    def set_zoom(self, value):
        self._zoom = value

    zoom = property(get_zoom, set_zoom)

    def init(self):
        sdl2.SDL_ShowCursor(sdl2.SDL_FALSE)
        sdl2.SDL_SetHint(sdl2.SDL_HINT_JOYSTICK_ALLOW_BACKGROUND_EVENTS, b"1")
        self.add_component('debug', sdl2ui.component.Debugger())
        self.add_component('menu', MenuComponent(
            actions=settings['menu_actions'],
            highlight=(0x00, 0x00, 0xff, 0xff),
            line_space=8,
            border=10))
        for i, emulator in enumerate(settings['emulators']):
            self.add_component('list-%s' % i, ListRomsComponent(
                emulator=emulator,
                border=10,
                page_size=20,
                line_space=8,
                highlight=(0xff, 0xff, 0x00, 0xff)))
        self.add_component('main', MainComponent(
            emulators=settings['emulators'],
            musics=settings.get('musics')))
        self.components['main'].show()


logging.basicConfig(level=logging.DEBUG)
Meldnafen.run()
if command:
    os.execvp(command[0], command)
exit(2)
