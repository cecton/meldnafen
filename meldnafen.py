from __future__ import division

import fnmatch
from itertools import islice
import json
import logging
from math import ceil
import os
import random
import re
import sdl2
import sdl2ui
import sdl2ui.ext.mixer
import sdl2ui.ext.joystick


command = None
with open(os.path.expanduser('~/.config/meldnafenrc')) as rc:
    settings = json.load(rc)
    settings['musics'] = os.path.expanduser(settings['musics'])


class MenuComponent(sdl2ui.Component):
    highlight = (0x00, 0x00, 0xff, 0xff)
    line_space = 8
    default_active = False

    def init(self):
        self.select = 0

    def run_command(self):
        global command
        _, command = settings['menu_actions'][self.select]
        self.app.quit()

    def peek(self):
        if self.app.keys[sdl2.SDL_SCANCODE_UP]:
            self.app.keys[sdl2.SDL_SCANCODE_UP] = sdl2.SDL_FALSE
            self.select -= 1
            if self.select < 0:
                self.select = len(settings['menu_actions']) - 1
        elif self.app.keys[sdl2.SDL_SCANCODE_DOWN]:
            self.app.keys[sdl2.SDL_SCANCODE_DOWN] = sdl2.SDL_FALSE
            self.select += 1
            if self.select >= len(settings['menu_actions']):
                self.select = 0
        elif self.app.keys[sdl2.SDL_SCANCODE_RETURN]:
            self.app.keys[sdl2.SDL_SCANCODE_RETURN] = sdl2.SDL_FALSE
            self.run_command()
        else:
            return False
        return True

    def render(self):
        border = 10
        x, y = border, border
        for i, (label, _) in enumerate(settings['menu_actions']):
            if i == self.select:
                with self.app.tint(self.highlight):
                    self.app.write('font-6', x, y, label)
            else:
                self.app.write('font-6', x, y, label)
            y += self.line_space


class ListRomsComponent(sdl2ui.Component):
    border = 10
    page_size = 20
    line_space = 8
    highlight = (0xff, 0xff, 0x00, 0xff)

    def init(self):
        self.x = int((self.app.width - 256) / 2 + self.border)
        self.y = int((self.app.height - 224) / 2 + self.border)
        self.roms = []
        self.emulator = 0
        self.selected = 0
        self.last_page = 0
        self.update_roms()
        self.bgm = self.app.play('bgm', loops=-1)
        self.bgm.volume /= 3

    def run_emulator(self):
        global command
        os.chdir(settings['emulators'][self.emulator]['path'])
        command = settings['emulators'][self.emulator]['exec'] + \
            [self.roms[self.selected]]
        self.app.quit()

    def update_roms(self):
        includes = [
            re.compile(fnmatch.translate(x))
            for x in (
                settings['emulators'][self.emulator]['include'].split(';')
                if settings['emulators'][self.emulator].get('include')
                else []
            )
        ]
        excludes = [
            re.compile(fnmatch.translate(x))
            for x in (
                settings['emulators'][self.emulator]['exclude'].split(';')
                if settings['emulators'][self.emulator].get('exclude')
                else []
            )
        ]
        self.roms = sorted(filter(
            lambda x: (not any(y.match(x) for y in excludes) or
                any(y.match(x) for y in includes)),
            os.listdir(settings['emulators'][self.emulator]['path'])))
        self.last_page = ceil(len(self.roms) / self.page_size)
        self.selected = 0

    def peek(self):
        if self.app.keys[sdl2.SDL_SCANCODE_UP]:
            self.app.keys[sdl2.SDL_SCANCODE_UP] = sdl2.SDL_FALSE
            self.selected -= 1
            if self.selected < 0:
                self.selected = len(self.roms) - 1
        elif self.app.keys[sdl2.SDL_SCANCODE_DOWN]:
            self.app.keys[sdl2.SDL_SCANCODE_DOWN] = sdl2.SDL_FALSE
            self.selected += 1
            if self.selected >= len(self.roms):
                self.selected = 0
        elif self.app.keys[sdl2.SDL_SCANCODE_PAGEUP]:
            self.app.keys[sdl2.SDL_SCANCODE_PAGEUP] = sdl2.SDL_FALSE
            self.selected = max(self.selected - self.page_size, 0)
        elif self.app.keys[sdl2.SDL_SCANCODE_PAGEDOWN]:
            self.app.keys[sdl2.SDL_SCANCODE_PAGEDOWN] = sdl2.SDL_FALSE
            self.selected = min(
                self.selected + self.page_size, len(self.roms) - 1)
        elif self.app.keys[sdl2.SDL_SCANCODE_LEFT]:
            self.app.keys[sdl2.SDL_SCANCODE_LEFT] = sdl2.SDL_FALSE
            self.emulator = (self.emulator - 1) % len(settings['emulators'])
            self.update_roms()
        elif self.app.keys[sdl2.SDL_SCANCODE_RIGHT]:
            self.app.keys[sdl2.SDL_SCANCODE_RIGHT] = sdl2.SDL_FALSE
            self.emulator = (self.emulator + 1) % len(settings['emulators'])
            self.update_roms()
        elif self.app.keys[sdl2.SDL_SCANCODE_RETURN]:
            self.app.keys[sdl2.SDL_SCANCODE_RETURN] = sdl2.SDL_FALSE
            if self.roms:
                self.run_emulator()
        else:
            return False
        return True

    def render(self):
        x, y = self.x, self.y
        self.app.write('font-6', x, y,
            settings['emulators'][self.emulator]['name'])
        y += self.line_space * 2
        if not self.roms:
            self.app.write('font-6', x, y, "No rom found")
            return
        page, selected = divmod(self.selected, self.page_size)
        for i, rom in enumerate(islice(self.roms, (self.page_size * page),
                (self.page_size * (page + 1)))):
            if i == selected:
                with self.app.tint(self.highlight):
                    self.app.write('font-6', x, y, rom)
            else:
                self.app.write('font-6', x, y, rom)
            y += self.line_space
        y += self.line_space
        self.app.write('font-6', x, y,
            "Page %d of %d (%d roms)" % (
                (page + 1), self.last_page, len(self.roms)))

    def deactivate(self):
        self.bgm.pause()

    def activate(self):
        self.bgm.resume()


class MainComponent(sdl2ui.Component):
    def peek(self):
        if self.app.keys[sdl2.SDL_SCANCODE_D]:
            self.app.keys[sdl2.SDL_SCANCODE_D] = sdl2.SDL_FALSE
            self.app.components[sdl2ui.component.DebuggerComponent].toggle()
        elif self.app.keys[sdl2.SDL_SCANCODE_ESCAPE]:
            self.app.keys[sdl2.SDL_SCANCODE_ESCAPE] = sdl2.SDL_FALSE
            self.app.components[ListRomsComponent].toggle()
            self.app.components[MenuComponent].toggle()
        elif self.app.keys[sdl2.SDL_SCANCODE_Q]:
            self.app.keys[sdl2.SDL_SCANCODE_Q] = sdl2.SDL_FALSE
            self.app.quit()
        else:
            return False
        return True


class Mixer(sdl2ui.ext.mixer.Mixer):
    frequency = 44100


class Joystick(sdl2ui.ext.joystick.BaseKeyboardJoystick):
    mapping = {
        button: getattr(sdl2, scancode_name)
        for button, scancode_name in settings['joystick']
    }

    def init(self):
        super(Joystick, self).init()
        sdl2.SDL_SetHint(sdl2.SDL_HINT_JOYSTICK_ALLOW_BACKGROUND_EVENTS, b"1")


class Meldnafen(sdl2ui.App):
    width = settings['width']
    height = settings['height']
    zoom = settings['zoom']
    fps = 30
    name = "Meldnafen"
    default_extensions = [Mixer, Joystick]
    default_components = [MainComponent, ListRomsComponent, MenuComponent]
    default_resources = [
        ('bgm', os.path.join(settings['musics'],
            random.choice(os.listdir(settings['musics'])))),
    ]
    renderer_flags = sdl2.SDL_RENDERER_SOFTWARE
    init_flags = sdl2.SDL_INIT_VIDEO

    def init(self):
        sdl2.SDL_ShowCursor(sdl2.SDL_FALSE)


logging.basicConfig(level=logging.DEBUG)
Meldnafen.run(
    components=[sdl2ui.component.DebuggerComponent],
    window_flags=getattr(sdl2, settings['window']))
if command:
    os.execvp(command[0], command)
exit(1)
