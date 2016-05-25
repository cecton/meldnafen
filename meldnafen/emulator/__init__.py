from functools import partial
import sdl2ui
import sdl2ui.mixins

from meldnafen.config.controls import Controls
from .list_roms import ListRoms
from .menu import Menu


class Emulator(sdl2ui.Component, sdl2ui.mixins.ImmutableMixin):
    def init(self):
        self.logger.debug(
            "Loading emulator %s: %d players",
            self.props['console'],
            self.props['players_number'])
        self.list = self.add_component(ListRoms,
            show_menu=self.show_menu,
            hide_menu=self.hide_menu,
            **self.props)
        self.menu = self.add_component(Menu,
            menu=self.generate_menu(),
            highlight=self.props['highlight'],
            line_space=10,
            x=self.props['x'],
            y=self.props['y'],
            on_quit=self.hide_menu)
        self.load_joystick_components()
        self.list.enable()

    def load_joystick_components(self):
        self.joystick_configure = {}
        for player in range(1, self.props['players_number'] + 1):
            controls = self.props['controls'].copy()
            if player == 1:
                controls.extend([
                    ("enable_hotkey", "Emulator Hotkey"),
                    ("menu_toggle",
                        "Emulator Menu (after pressing the hotkey)"),
                ])
            # NOTE: add the component to self.app, we don't want it to be
            # deactivated when the rest of the application is disabled
            self.joystick_configure[str(player)] = self.app.add_component(
                Controls,
                line_space=10,
                on_finish=self.finish_joystick_configuration,
                controls=controls,
                x=self.props['x'],
                y=self.props['y'])

    def show_menu(self, vars):
        self.menu.start(vars)
        self.list.disable()
        self.props['on_menu_activated']()

    def hide_menu(self):
        self.menu.disable()
        self.list.enable()
        self.props['on_menu_deactivated']()

    def generate_menu(self):
        return [
            ("Controls", "submenu", [
                ("Controls: {}".format(self.props['name']),
                    "submenu", [
                        ("Configure player %s" % i, "call",
                            partial(self.confgure_controls,
                                target='console', player=str(i)))
                        for i in range(1, self.props['players_number'] + 1)
                    ]),
                ("Controls: {game}",
                    "submenu", [
                        ("Configure player %s" % i, "call",
                            partial(self.confgure_controls,
                                target='game', player=str(i)))
                        for i in range(1, self.props['players_number'] + 1)
                    ] + [
                        ("Clear all", "call", self.remove_game_controls),
                    ]),
                ("Controls: {app.name}", "call",
                    self.app.activate_joystick_configuration)
            ]),
            ("Smooth: {app.settings[smooth]}", "call", self.app.toggle_smooth),
            ("FPS: {app.debugger.active}", "call", self.app.debugger.toggle),
        ]

    def confgure_controls(self, **kwargs):
        self.app.lock()
        self.joystick_configure[kwargs['player']].start(**kwargs)

    def finish_joystick_configuration(self, **kwargs):
        if kwargs:
            self.update_joystick_configuration(**kwargs)
        self.app.unlock()

    def update_joystick_configuration(self,
            joystick=None, player=None, target=None, config=None):
        if target == 'console':
            self.app.settings.setdefault('controls', {})\
                .setdefault(target, {})\
                .setdefault(self.props['console'], {})\
                .setdefault(player, {})\
                [joystick.guid] = config
        else:
            self.app.settings.setdefault('controls', {})\
                .setdefault(target, {})\
                .setdefault(self.props['console'], {})\
                .setdefault(self.list.game, {})\
                .setdefault(player, {})\
                [joystick.guid] = config

    def remove_game_controls(self):
        self.app.settings['controls']\
            .setdefault('game', {})\
            .pop(self.props['console'], None)
        self.hide_menu()
