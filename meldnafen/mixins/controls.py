import re
import sdl2

from meldnafen.config.controls import Controls


JOYSTICK_ACTIONS = {
    'up': sdl2.SDL_SCANCODE_UP,
    'down': sdl2.SDL_SCANCODE_DOWN,
    'left': sdl2.SDL_SCANCODE_LEFT,
    'right': sdl2.SDL_SCANCODE_RIGHT,
    'ok': sdl2.SDL_SCANCODE_RETURN,
    'cancel': sdl2.SDL_SCANCODE_BACKSPACE,
    'menu': sdl2.SDL_SCANCODE_ESCAPE,
    'next_page': sdl2.SDL_SCANCODE_PAGEDOWN,
    'prev_page': sdl2.SDL_SCANCODE_PAGEUP,
}


class ControlsMixin:
    def init(self):
        self.set_state({
            'menu_joystick_connected': False,
        })
        self.joystick_configure = self.add_component(Controls,
            line_space=10,
            cancellable=False,
            countdown=8,
            on_finish=self.finish_joystick_configuration,
            controls=[
                ('up', "Up"),
                ('down', "Down"),
                ('left', "Left"),
                ('right', "Right"),
                ('ok', "OK"),
                ('cancel', "Cancel"),
                ('menu', "Menu"),
                ('next_page', "Next page"),
                ('prev_page', "Previous page"),
            ],
            x=self.x,
            y=self.y)
        self.register_event_handler(
            sdl2.SDL_JOYDEVICEREMOVED, self.joy_removed)

    def render(self):
        if not self.state['menu_joystick_connected']:
            with self.tint((0xff, 0x00, 0x00, 0xff)):
                self.write('font-12', self.x, self.y, "No joystick connected")

    def joy_removed(self, event):
        if not self.joystick_manager.joysticks:
            self.set_state({
                'menu_joystick_connected': False,
            })
            self.lock()
            self.joystick_configure.disable()

    def activate_joystick_configuration(self):
        self.lock()
        self.joystick_configure.start()

    def finish_joystick_configuration(self, joystick=None, config=None):
        if config:
            self.update_joystick_configuration(joystick, config)
        self.unlock()

    def load_joystick_configuriation(self, joystick):
        self.joystick.load(joystick, {
            v: JOYSTICK_ACTIONS[re.sub(r"(_btn|_axis)$", "", k)]
            for k, v in
                self.settings['controls']['menu'][joystick.guid].items()
        })

    def menu_joystick_added(self, joystick):
        if joystick.guid not in self.settings['controls'].get('menu', {}):
            if not self.joystick.available:
                self.activate_joystick_configuration()
        else:
            self.load_joystick_configuriation(joystick)
            if self.joystick.available:
                self.joystick_configure.disable()
                self.unlock()
        self.set_state({
            'menu_joystick_connected': True,
        })

    def menu_joystick_removed(self):
        if self.joystick_manager.joysticks and not self.joystick.available:
            self.activate_joystick_configuration()

    def update_joystick_configuration(self, joystick, config):
        self.settings['controls']\
            .setdefault('menu', {})[joystick.guid] = config
        self.load_joystick_configuriation(joystick)
