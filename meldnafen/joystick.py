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
        self.joysticks = {}

    def activate(self):
        self.axis_change = {}
        self.hat_change = {}

    def added(self, event):
        joystick = self.props['manager'].get(event.jdevice.which)
        self.load(joystick)

    def removed(self, event):
        joystick = self.joysticks.get(event.jdevice.which)
        if not joystick:
            return
        self.logger.debug("Joystick removed: %s", joystick.name)
        joystick.close()
        self.joysticks.pop(joystick.id)

    @property
    def available(self):
        return any(x.opened for x in self.joysticks.values())

    def load(self, joystick):
        joystick.open()
        self.joysticks[joystick.id] = joystick

    def _push_keyboard_event(self, key):
        self.event.type = sdl2.SDL_KEYDOWN
        self.event.key.keysym.scancode = key
        self.event.key.keysym.sym = sdl2.SDL_GetKeyFromScancode(key)
        sdl2.SDL_PushEvent(self.event)

    def button_down(self, event):
        if event.jbutton.which not in self.joysticks:
            return
        self.logger.debug(
            "Button %d on joystick %d pressed",
            event.jbutton.button,
            self.joysticks[event.jbutton.which].index)
        if event.jbutton.button == 1:
            self._push_keyboard_event(sdl2.SDL_SCANCODE_ESCAPE)
        elif event.jbutton.button in (0, 2):
            # NOTE: some joysticks have way too much buttons and their action
            #       overlaps with the hats. Let's limit this action to 2
            #       buttons. So 3 buttons gamepads like the Mega Drive will
            #       have A and C to validate.
            # TODO: cancel button action when a hat or an axis is used?
            self._push_keyboard_event(sdl2.SDL_SCANCODE_RETURN)

    def axis_motion(self, event):
        if event.jbutton.which not in self.joysticks:
            return
        if event.jaxis.axis > 1:
            return
        if event.jaxis.value < -0x4000:
            self.axis_change[event.jaxis.which] = "-{}".format(event.jaxis.axis)
        elif event.jaxis.value >= 0x4000:
            self.axis_change[event.jaxis.which] = "+{}".format(event.jaxis.axis)
        elif event.jaxis.value == 0 and self.axis_change.get(event.jaxis.which):
            self.logger.debug(
                "Axis motion detected on joystick %d: %s",
                self.joysticks[event.jaxis.which].index,
                self.axis_change[event.jaxis.which])
            if self.axis_change[event.jaxis.which] == "-0":
                self._push_keyboard_event(sdl2.SDL_SCANCODE_LEFT)
            elif self.axis_change[event.jaxis.which] == "+0":
                self._push_keyboard_event(sdl2.SDL_SCANCODE_RIGHT)
            elif self.axis_change[event.jaxis.which] == "-1":
                self._push_keyboard_event(sdl2.SDL_SCANCODE_UP)
            elif self.axis_change[event.jaxis.which] == "+1":
                self._push_keyboard_event(sdl2.SDL_SCANCODE_DOWN)
            self.axis_change[event.jaxis.which] = None

    def hat_motion(self, event):
        if event.jhat.which not in self.joysticks:
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
            self.logger.debug(
                "Hat motion detected on joystick %d: %s",
                self.joysticks[event.jhat.which].index,
                self.hat_change[event.jhat.which])
            if self.hat_change[event.jhat.which] == "h0up":
                self._push_keyboard_event(sdl2.SDL_SCANCODE_UP)
            if self.hat_change[event.jhat.which] == "h0down":
                self._push_keyboard_event(sdl2.SDL_SCANCODE_DOWN)
            if self.hat_change[event.jhat.which] == "h0left":
                self._push_keyboard_event(sdl2.SDL_SCANCODE_LEFT)
            if self.hat_change[event.jhat.which] == "h0right":
                self._push_keyboard_event(sdl2.SDL_SCANCODE_RIGHT)
            self.hat_change[event.jhat.which] = None
