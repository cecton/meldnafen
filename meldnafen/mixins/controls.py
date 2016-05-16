import re
import sdl2

from meldnafen.config.controls import Controls


JOYSTICK_ACTIONS = {
    'up': sdl2.SDL_SCANCODE_UP,
    'down': sdl2.SDL_SCANCODE_DOWN,
    'left': sdl2.SDL_SCANCODE_LEFT,
    'right': sdl2.SDL_SCANCODE_RIGHT,
    'run': sdl2.SDL_SCANCODE_RETURN,
    'cancel': sdl2.SDL_SCANCODE_BACKSPACE,
    'menu': sdl2.SDL_SCANCODE_ESCAPE,
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
                ('run', "Run/Start"),
                ('cancel', "Cancel"),
                ('menu', "Menu"),
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
        controls = self.settings['controls'].get('menu', {}).get(joystick.guid)
        if not controls:
            return False
        key_bindings = {
            re.sub(r"(_btn|_axis)$", "", k): v
            for k, v in controls.items()
        }
        if set(JOYSTICK_ACTIONS) - set(key_bindings):
            return False
        self.joystick.load(joystick, {
            key_bindings[action]: key
            for action, key in JOYSTICK_ACTIONS.items()
        })
        return True

    def menu_joystick_added(self, joystick):
        if not self.load_joystick_configuriation(joystick):
            if not self.joystick.available:
                self.activate_joystick_configuration()
        else:
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
