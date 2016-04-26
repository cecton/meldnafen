import json
import logging
import os
import sdl2

from meldnafen.consoles import consoles


DEFAULT_CONFIG = "~/.config/meldnafenrc"


def read_config(config, overrides={}):
    settings = {
        'controls': {},
        'border': 10,
        'width': 640,
        'height': 480,
        'fps': 30,
        'emulators': [
            {
                'console': console,
                'path': "~/%s_roms" % console,
            }
            for console in consoles.keys()
            if os.path.isdir(os.path.expanduser("~/%s_roms" % console))
        ],
        'musics': "~/bgm",
    }
    with open(os.path.expanduser(config)) as rc:
        try:
            settings.update(json.load(rc))
        except Exception:
            # NOTE: the configuration is broken, just wipe it
            pass
    settings.update(overrides)
    return settings


def write_config(settings):
    # NOTE: serialize first in case an error occur
    serialized = json.dumps(settings, sort_keys=True, indent=2)
    with open(os.path.expanduser(DEFAULT_CONFIG), 'wt') as rc:
        rc.write(serialized)


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
