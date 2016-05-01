from tempfile import NamedTemporaryFile


def prepare(command, controls):
    with NamedTemporaryFile('wt', prefix='retroarch-', delete=False) as fh:
        for player, player_controls in controls.items():
            write_retroarch_controls(fh, player, player_controls)
            fh.write("\n")
        return command + ['--appendconfig', fh.name]


def write_retroarch_controls(fileobj, player, controls):
    for k, v in controls.items():
        fileobj.write("input_player{}_{} = {}\n".format(player, k, v))
