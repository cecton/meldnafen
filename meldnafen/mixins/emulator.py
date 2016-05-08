import os

from meldnafen.consoles import consoles
from meldnafen.exceptions import MissingControls
from meldnafen.list.list_roms import ListRoms


def merge_dict(*dicts):
    result = {}
    for d in dicts:
        result.update(d)
    return result


class EmulatorMixin(object):
    def init(self):
        self.set_state({
            'emulator': 0,
            'command': None,
        })
        self.emulators = [
            self.add_component(ListRoms,
                **merge_dict(consoles[emulator['console']], emulator.items()),
                border=10,
                page_size=15,
                line_space=10,
                highlight=(0xff, 0xff, 0x00, 0xff),
                x=self.x,
                y=self.y,
                on_next_emulator=self.next_emulator,
                on_prev_emulator=self.prev_emulator,
                on_menu_activated=self.bgm.disable,
                on_menu_deactivated=self.bgm.enable)
            for emulator in self.settings['emulators']
        ]

    def get_player_controls(self, controls):
        self.joystick_manager.reload()
        config = {}
        for player in map(str, range(1, 9)):
            if not player in controls:
                continue
            self.logger.debug("Configuring joystick for player %s...", player)
            for index, joystick in self.joystick_manager.joysticks.items():
                if joystick.guid in controls[player]:
                    self.logger.debug("Found joystick %s in controls",
                        joystick.guid)
                    config[player] = merge_dict(
                        {"joypad_index": index},
                        controls[player][joystick.guid])
                    break
            else:
                self.logger.debug("No joystick configuration available")
        return config

    def next_emulator(self):
        self.show_emulator((self.state['emulator'] + 1) % len(self.emulators))

    def prev_emulator(self):
        self.show_emulator((self.state['emulator'] - 1) % len(self.emulators))

    def run_emulator(self, console, path, game):
        command = consoles[console]['exec'] + [os.path.join(path, game)]
        controls = {}
        try:
            controls.update(self.get_player_controls(
                self.settings['controls']['console'][console]))
        except KeyError:
            raise MissingControls()
        try:
            controls.update(self.get_player_controls(
                self.settings['controls']['game'][console][game]))
        except KeyError:
            pass
        self.set_state({
            'command': command,
            'controls': controls,
        })
        self.quit()

    def show_emulator(self, index):
        self.emulators[self.state['emulator']].disable()
        self.emulators[index].enable()
        self.set_state({'emulator': index})

    def toggle_smooth(self):
        self.set_state({
            'settings': merge_dict(
                self.settings,
                {'smooth': not self.settings['smooth']}),
        })
