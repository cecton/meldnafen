from __future__ import division

import sdl2
import sdl2ui
import sdl2ui.mixins


class Menu(sdl2ui.Component, sdl2ui.mixins.ImmutableMixin):
    @property
    def x(self):
        return int((self.app.viewport.w - 256) / 2 + self.props['border'])

    @property
    def y(self):
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
        _, command = self.props['actions'][self.state['select']]
        self.app.run_command(command)

    def keypress(self, event):
        if event.key.keysym.scancode in self.keyboard_mapping:
            self.keyboard_mapping[event.key.keysym.scancode]()

    def previous_item(self):
        self.set_state({
            'select':
                len(self.props['actions']) - 1
                if self.state['select'] == 0
                else self.state['select'] - 1,
        })

    def next_item(self):
        self.set_state({
            'select':
                0
                if self.state['select'] == len(self.props['actions']) - 1
                else self.state['select'] + 1,
        })

    def render(self):
        x, y = self.x, self.y
        for i, (label, _) in enumerate(self.props['actions']):
            if i == self.state['select']:
                with self.app.tint(self.props['highlight']):
                    self.app.write('font-6', x, y, label)
            else:
                self.app.write('font-6', x, y, label)
            y += self.props['line_space']
