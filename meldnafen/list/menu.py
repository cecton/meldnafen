from __future__ import division

import sdl2
import sdl2ui
import sdl2ui.mixins


class Menu(sdl2ui.Component, sdl2ui.mixins.ImmutableMixin):
    def init(self):
        self.keyboard_mapping = {
            sdl2.SDL_SCANCODE_UP: self.previous_item,
            sdl2.SDL_SCANCODE_DOWN: self.next_item,
            sdl2.SDL_SCANCODE_RETURN: self.choose,
            sdl2.SDL_SCANCODE_BACKSPACE: self.quit_menu,
            sdl2.SDL_SCANCODE_ESCAPE: self.disable,
        }
        self.register_event_handler(sdl2.SDL_KEYDOWN, self.keypress)

    def activate(self):
        self.set_state({
            'root': self.props['menu'],
            'previous': [],
            'select': 0,
        })
        self.props['on_activated']()

    def deactivate(self):
        self.props['on_deactivated']()

    def choose(self):
        _, action, value = self.state['root'][self.state['select']]
        if action == 'submenu':
            self.set_state({
                'root': value,
                'previous': self.state['previous'] + [self.state['root']],
                'select': 0,
            })
        elif action == 'call':
            value()
        elif action == 'quit':
            self.app.quit()
        else:
            raise NotImplementedError("no action %s does not exist" % action)

    def keypress(self, event):
        if event.key.keysym.scancode in self.keyboard_mapping:
            self.keyboard_mapping[event.key.keysym.scancode]()

    def previous_item(self):
        self.set_state({
            'select':
                len(self.state['root']) - 1
                if self.state['select'] == 0
                else self.state['select'] - 1,
        })

    def next_item(self):
        self.set_state({
            'select':
                0
                if self.state['select'] == len(self.state['root']) - 1
                else self.state['select'] + 1,
        })

    def quit_menu(self):
        if not self.state['previous']:
            self.disable()
        else:
            previous = self.state['previous'].copy()
            last = previous.pop()
            self.set_state({
                'root': last,
                'previous': previous,
                'select': 0,
            })

    def render(self):
        x, y = self.props['x'], self.props['y']
        for i, (label, _, _) in enumerate(self.state['root']):
            if i == self.state['select']:
                with self.app.tint(self.props['highlight']):
                    self.app.write('font-12', x, y,
                        label.format(**self.state['vars']))
            else:
                self.app.write('font-12', x, y,
                    label.format(**self.state['vars']))
            y += self.props['line_space']
