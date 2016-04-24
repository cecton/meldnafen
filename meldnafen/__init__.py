import json
import logging
import os
import sdl2


DEFAULT_CONFIG = "~/.config/meldnafenrc"


def read_config(config, overrides={}):
    settings = {
        'border': 10,
        'width': 640,
        'height': 480,
        'fps': 30,
        'renderer_flags': 0,
        'init_flags': sdl2.SDL_INIT_VIDEO | sdl2.SDL_INIT_AUDIO,
    }
    with open(os.path.expanduser(config)) as rc:
        settings.update(json.load(rc))
    if settings.get('musics'):
        settings['musics'] = os.path.expanduser(settings['musics'])
    settings['zoom'] = max(
        min(int(settings['width'] / 256), int(settings['height'] / 224)),
        1)
    settings.update(overrides)
    return settings


def start_meldnafen(**kwargs):
    from meldnafen.app import Meldnafen
    logging.basicConfig(level=logging.DEBUG)
    settings = read_config(kwargs.get('config', DEFAULT_CONFIG), kwargs)
    app = Meldnafen.run(**settings)
    if app.command:
        os.execvp(app.command[0], app.command)
    exit(2)
