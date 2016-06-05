import logging
import sdl2
import sdl2ui
import sdl2ui.mixins


class MenuJoystick(sdl2ui.Component, sdl2ui.mixins.ImmutableMixin):
    logger = logging.getLogger(__name__)

    def init(self):
        self.event = sdl2.SDL_Event()
        self.app.register_event_handler(sdl2.SDL_JOYDEVICEADDED, self.added)
        self.app.register_event_handler(
            sdl2.SDL_JOYDEVICEREMOVED, self.removed)
        self.register_event_handler(sdl2.SDL_JOYBUTTONDOWN, self.button_down)
        self.register_event_handler(sdl2.SDL_JOYAXISMOTION, self.axis_motion)
        self.register_event_handler(sdl2.SDL_JOYHATMOTION, self.hat_motion)
        self.set_state({
            'keyboard_mapping': {},
        })
        self.joysticks = {}

    def activate(self):
        self.axis_change = {}
        self.hat_change = {}

    def added(self, event):
        joystick = self.props['manager'].get(event.jdevice.which)
        self.props['on_joystick_added'](joystick)

    def removed(self, event):
        joystick = self.joysticks.get(event.jdevice.which)
        if not joystick:
            return
        self.logger.debug("Joystick removed: %s", joystick.name)
        joystick.close()
        self.joysticks.pop(joystick.id)
        self.props['on_joystick_removed']()

    @property
    def available(self):
        return any(x.opened for x in self.joysticks.values())

    def load(self, joystick, mapping):
        joystick.open()
        self.joysticks[joystick.id] = joystick
        keyboard_mapping = self.state['keyboard_mapping'].copy()
        keyboard_mapping[joystick.id] = mapping
        self.set_state({
            'keyboard_mapping': keyboard_mapping,
        })

    def _push_keyboard_event(self, key):
        self.event.type = sdl2.SDL_KEYDOWN
        self.event.key.keysym.scancode = key
        self.event.key.keysym.sym = sdl2.SDL_GetKeyFromScancode(key)
        sdl2.SDL_PushEvent(self.event)

    def button_down(self, event):
        if event.jbutton.which not in self.joysticks:
            return
        mapping = self.state['keyboard_mapping'].get(event.jbutton.which)
        if not mapping:
            return
        key = mapping.get(str(event.jbutton.button))
        if key:
            self.app.keys[key] = sdl2.SDL_TRUE
            self._push_keyboard_event(key)
        else:
            self.logger.debug(
                "Button %d on joystick %d not mapped",
                event.jbutton.button,
                self.joysticks[event.jbutton.which].index)

    def axis_motion(self, event):
        if event.jbutton.which not in self.joysticks:
            return
        mapping = self.state['keyboard_mapping'].get(event.jaxis.which)
        if not mapping:
            return
        value = event.jaxis.value
        if value < -0x7000:
            self.axis_change[event.jaxis.which] = "-{}".format(event.jaxis.axis)
        elif value >= 0x7000:
            self.axis_change[event.jaxis.which] = "+{}".format(event.jaxis.axis)
        elif value == 0 and self.axis_change.get(event.jaxis.which):
            key = mapping.get(self.axis_change[event.jaxis.which])
            if key:
                self.app.keys[key] = sdl2.SDL_TRUE
                self._push_keyboard_event(key)
            else:
                self.logger.debug(
                    "Axis %s on joystick %d not mapped",
                    self.axis_change[event.jaxis.which], self.joysticks[event.jaxis.which].index)
            self.axis_change[event.jaxis.which] = None

    def hat_motion(self, event):
        if event.jhat.which not in self.joysticks:
            return
        mapping = self.state['keyboard_mapping'].get(event.jhat.which)
        if not mapping:
            return
        value = event.jhat.value
        if value == sdl2.SDL_HAT_UP:
            self.hat_change[event.jhat.which] = "h{}up".format(event.jhat.hat)
        elif value == sdl2.SDL_HAT_DOWN:
            self.hat_change[event.jhat.which] = "h{}down".format(event.jhat.hat)
        elif value == sdl2.SDL_HAT_LEFT:
            self.hat_change[event.jhat.which] = "h{}left".format(event.jhat.hat)
        elif value == sdl2.SDL_HAT_RIGHT:
            self.hat_change[event.jhat.which] = "h{}right".format(event.jhat.hat)
        elif value == sdl2.SDL_HAT_CENTERED and self.hat_change:
            key = mapping.get(self.hat_change[event.jhat.which])
            if key:
                self.app.keys[key] = sdl2.SDL_TRUE
                self._push_keyboard_event(key)
            else:
                self.logger.debug(
                    "Hat %s on joystick %d not mapped",
                    self.hat_change[event.jhat.which], self.joysticks[event.jhat.which].index)
            self.hat_change[event.jhat.which] = None
