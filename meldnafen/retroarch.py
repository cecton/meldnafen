import re
from tempfile import NamedTemporaryFile


def prepare(command, controls, settings):
    with NamedTemporaryFile('wt', prefix='retroarch-', delete=False) as fh:
        for player, player_controls in controls.items():
            write_retroarch_controls(fh, player, player_controls)
            fh.write("\n")
        fh.write("input_autodetect_enable = false\n")
        fh.write("video_force_aspect = true\n")
        fh.write("video_scale_integer = true\n")
        fh.write("video_smooth = {}\n".format(
            "true" if settings['smooth'] else "false"))
        return command + ['--appendconfig', fh.name]


def write_retroarch_controls(fileobj, player, controls):
    for k, v in controls.items():
        if player == "1" and re.search(r"^(enable_hotkey|menu_toggle)", k):
            fileobj.write("input_{} = {}\n".format(k, v))
        else:
            fileobj.write("input_player{}_{} = {}\n".format(player, k, v))
