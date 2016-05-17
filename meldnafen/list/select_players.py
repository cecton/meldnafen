import sdl2
import sdl2ui
import sdl2ui.mixins


class SelectPlayers(sdl2ui.Component, sdl2ui.mixins.ImmutableMixin):
    def init(self):
        self.keyboard_mapping = {
            sdl2.SDL_SCANCODE_DOWN: self.next_option,
            sdl2.SDL_SCANCODE_UP: self.prev_option,
            sdl2.SDL_SCANCODE_RETURN: self.select_option,
        }
        self.register_event_handler(sdl2.SDL_KEYDOWN, self.keypress)

    def keypress(self, event):
        if event.key.keysym.scancode in self.keyboard_mapping:
            self.keyboard_mapping[event.key.keysym.scancode]()

    def start(self, max_players):
        self.options = [(1, "1 player")]
        self.options.extend([
            (n, "{} players".format(n))
            for n in range(2, max_players + 1)
        ])
        self.options.append((None, "Return"))
        self.set_state({
            'select': 0,
        })
        self.enable()

    def next_option(self):
        if self.state['select'] == len(self.options) - 1:
            return
        self.set_state({
            'select': self.state['select'] + 1,
        })

    def prev_option(self):
        if self.state['select'] == 0:
            return
        self.set_state({
            'select': self.state['select'] - 1,
        })

    def select_option(self):
        value, _ = self.options[self.state['select']]
        self.disable()
        if value is None:
            self.props['on_return']()
        else:
            self.props['on_select'](value)

    def render(self):
        x, y = self.props['x'], self.props['y']
        for i, (_, option) in enumerate(self.options):
            if i == self.state['select']:
                with self.app.tint(self.props['highlight']):
                    self.app.write('font-12', x, y, option)
            else:
                self.app.write('font-12', x, y, option)
            y += self.props['line_space']
