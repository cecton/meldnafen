import logging
import sdl2
import sdl2ui


class MenuJoystick(sdl2ui.Component):
    logger = logging.getLogger(__name__)

    def init(self):
        self.event = sdl2.SDL_Event()
        self.app.register_event_handler(sdl2.SDL_JOYDEVICEADDED, self.added)
        self.app.register_event_handler(
            sdl2.SDL_JOYDEVICEREMOVED, self.removed)
        self.register_event_handler(sdl2.SDL_JOYBUTTONDOWN, self.button_down)
        self.register_event_handler(sdl2.SDL_JOYAXISMOTION, self.axis_motion)
        self.set_state({
            'keyboard_mapping': {},
        })
        self.joysticks = {}

    def added(self, event):
        joystick = self.props['manager'].get(event.jdevice.which)
        self.props['on_joystick_added'](joystick)

    def removed(self, event):
        joystick = self.joysticks.get(event.jdevice.which)
        if not joystick:
            return
        self.logger.debug("Joystick %d removed", joystick.index)
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
        mapping = self.state['keyboard_mapping'].get(event.jbutton.which)
        if not mapping:
            return
        value = event.jaxis.value
        if value < -0x4000:
            axis = "-{}".format(event.jaxis.axis)
        elif value >= 0x4000:
            axis = "+{}".format(event.jaxis.axis)
        else:
            return
        key = mapping.get(axis)
        if key:
            self.app.keys[key] = sdl2.SDL_TRUE
            self._push_keyboard_event(key)
        else:
            self.logger.debug(
                "Axis %s on joystick %d not mapped",
                axis, self.joysticks[event.jbutton.which].index)
