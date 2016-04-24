import logging
import sdl2
import sdl2ui
import sdl2ui.joystick
import sdl2ui.mixins


class JoystickCapture(sdl2ui.Component, sdl2ui.mixins.ImmutableMixin):
    def init(self):
        self.register_event_handler(
            sdl2.SDL_JOYBUTTONDOWN, self.capture_button)

    def capture_button(self, event):
        if not event.jbutton.which == self.state['joystick'].id:
            return
        new_controls = self.state['controls'].copy()
        control = new_controls.pop(0)
        new_config = self.state['config'].copy()
        new_config.update({
            control[0]: event.jbutton.button,
        })
        self.set_state({
            'config': new_config,
            'x': control,
        })
        if not new_controls:
            self.parent.stop_capture()
        else:
            self.set_state({
                'controls': new_controls,
            })

    def render(self):
        x, y = self.props['x'], self.props['y']
        self.app.write('font-12', x, y, self.state['controls'][0][1])


class Controls(sdl2ui.Component, sdl2ui.mixins.ImmutableMixin):
    def init(self):
        self.capture = self.add_component(JoystickCapture,
            x=self.props['x'],
            y=self.props['y'] + self.props['line_space'] * 4)
        self.register_event_handler(sdl2.SDL_JOYDEVICEADDED, self.detect)
        self.register_event_handler(sdl2.SDL_JOYBUTTONDOWN, self.button_down)

    def update_countdown(self):
        remaining = self.state['countdown'] - 1
        self.set_state({
            'countdown': remaining,
        })
        if remaining > 0:
            self.app.add_timer(1000, self.update_countdown)
        else:
            self.cancel()

    def detect(self, event):
        index = event.jdevice.which
        if index in self.joysticks:
            return
        self.app.joystick_manager.get(index).open()

    def activate(self):
        sdl2.SDL_JoystickUpdate()
        self.set_state({
            'countdown': self.props['countdown'],
        })
        self.app.add_timer(1000, self.update_countdown)

    def button_down(self, event):
        self.set_state({
            'countdown': self.props['countdown'],
        })
        if not self.capture.active:
            joysticks = filter(
                lambda x: x.id == event.jdevice.which,
                self.app.joystick_manager.joysticks.values())
            joystick = next(iter(joysticks))
            self.start_capture(joystick)

    def start_capture(self, joystick):
        self.set_state({
            'name': joystick.name,
        })
        self.capture.set_state({
            'joystick': joystick,
            'controls': self.props['controls'].copy(),
            'config': {},
        })
        self.capture.enable()

    def stop_capture(self):
        self.capture.disable()
        self.props['on_finish'](self.capture.state['config'])

    def cancel(self):
        self.capture.disable()
        self.props['on_finish']()

    def render(self):
        x, y = self.props['x'], self.props['y']
        if self.capture.active:
            self.app.write('font-12', x, y, self.state['name'])
            y += 2 * self.props['line_space']
            self.app.write('font-12', x, y, "Press the button...")
        else:
            self.app.write('font-12', x, y,
                "Press any button to start configuring")
        if self.state['countdown'] <= 5:
            with self.app.tint((0xff, 0x00, 0x00, 0xff)):
                y += 4 * self.props['line_space']
                self.app.write('font-12', x, y,
                    "Cancel configuration in %d seconds..."
                    % self.state['countdown'])
