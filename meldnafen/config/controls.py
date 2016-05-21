import logging
import sdl2
import sdl2ui
import sdl2ui.joystick
import sdl2ui.mixins


DEFAULT_COUNTDOWN = 8


class JoystickCapture(sdl2ui.Component, sdl2ui.mixins.ImmutableMixin):
    def init(self):
        self.register_event_handler(
            sdl2.SDL_JOYBUTTONDOWN, self.capture_button)
        self.register_event_handler(sdl2.SDL_JOYAXISMOTION, self.capture_axis)

    def capture_button(self, event):
        if not event.jbutton.which == self.state['joystick'].id:
            return
        self.register_control("{}_btn", str(event.jbutton.button))

    def capture_axis(self, event):
        if not event.jaxis.which == self.state['joystick'].id:
            return
        value = event.jaxis.value
        if value < -0x4000:
            self.register_control("{}_axis", "-{}".format(event.jaxis.axis))
        elif value >= 0x4000:
            self.register_control("{}_axis", "+{}".format(event.jaxis.axis))

    def register_control(self, mapping, input):
        new_controls = self.state['controls'].copy()
        control = new_controls.pop(0)
        new_config = self.state['config'].copy()
        new_config.update({
            mapping.format(control[0]): input,
        })
        self.set_state({
            'config': new_config,
            'x': control,
        })
        if not new_controls:
            self.disable()
            self.props['on_finish'](self.state['config'])
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
            on_finish=self.finish,
            x=self.props['x'],
            y=self.props['y'] + self.props['line_space'] * 4)
        self.register_event_handler(sdl2.SDL_JOYDEVICEADDED, self.detect)
        self.register_event_handler(sdl2.SDL_JOYBUTTONDOWN, self.button_down)
        self.register_event_handler(sdl2.SDL_JOYAXISMOTION, self.axis_motion)

    def start(self, **kwargs):
        self.enable()
        self.set_state({
            'kwargs': kwargs,
        })

    def detect(self, event):
        index = event.jdevice.which
        self.app.joystick_manager.get(index).open()

    def activate(self):
        for joystick in self.app.joystick_manager.joysticks:
            joystick.open()
        self.reset_countdown()

    def deactivate(self):
        self.capture.disable()
        self.reset_countdown()

    def reset_countdown(self):
        self.set_state({
            'countdown': self.props.get('countdown', DEFAULT_COUNTDOWN),
        })

    def update_countdown(self):
        if not self.active:
            return
        remaining = self.state['countdown'] - 1
        self.set_state({
            'countdown': remaining,
        })
        if remaining > 0:
            self.app.add_timer(1000, self.update_countdown)
        else:
            self.capture.disable()
            self.reset_countdown()
            if self.props.get('cancellable', True):
                self.disable()
                self.props['on_finish']()

    def button_down(self, event):
        if not self.capture.active:
            joystick = self.app.joystick_manager.find(event.jbutton.which)
            self.start_capture(joystick)
        elif event.jbutton.which == self.state['joystick_id']:
            self.reset_countdown()

    def axis_motion(self, event):
        if not self.capture.active:
            joystick = self.app.joystick_manager.find(event.jaxis.which)
            self.start_capture(joystick)
        elif event.jaxis.which == self.state['joystick_id']:
            self.reset_countdown()

    def start_capture(self, joystick):
        self.set_state({
            'joystick': joystick,
            'joystick_id': joystick.id,
        })
        self.capture.set_state({
            'joystick': joystick,
            'controls': self.props['controls'].copy(),
            'config': {},
        })
        self.capture.enable()
        self.app.add_timer(1000, self.update_countdown)

    def finish(self, config):
        self.disable()
        self.props['on_finish'](
            joystick=self.state['joystick'],
            config=config,
            **self.state['kwargs'])

    def render(self):
        x, y = self.props['x'], self.props['y']
        if self.capture.active:
            self.app.write('font-12', x, y, self.state['joystick'].name)
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
