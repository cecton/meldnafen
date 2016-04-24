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
    }
    with open(os.path.expanduser(config)) as rc:
        settings.update(json.load(rc))
    settings.update(overrides)
    return settings


def write_config(settings):
    with open(os.path.expanduser(DEFAULT_CONFIG), 'wt') as rc:
        rc.write(json.dumps(settings, sort_keys=True, indent=2))


def start_meldnafen(**kwargs):
    from meldnafen.app import Meldnafen
    logging.basicConfig(level=logging.DEBUG)
    settings = read_config(kwargs.get('config', DEFAULT_CONFIG), kwargs)
    zoom = min(int(settings['width'] / 256), int(settings['height'] / 224))
    props = {
        'zoom': (zoom if zoom > 0 else 1),
        'renderer_flags': 0,
        'init_flags': sdl2.SDL_INIT_VIDEO | sdl2.SDL_INIT_AUDIO,
        'width': settings['width'],
        'height': settings['height'],
        'fps': settings['fps'],
    }
    app = Meldnafen.run(settings=settings, **props)
    if app.command:
        os.execvp(app.command[0], app.command)
    exit(2)
