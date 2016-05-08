consoles = {
    'nes': {
        'name': 'Nintendo Entertainment System',
        'controls': [
            ("up", "Up"),
            ("down", "Down"),
            ("left", "Left"),
            ("right", "Right"),
            ("a", "A"),
            ("b", "B"),
            ("select", "Select"),
            ("start", "Start"),
        ],
        'exec': [
            'sudo', '-u', 'meldnafen', 'retroarch', '-v',
            '-L', '/usr/lib/libretro/quicknes_libretro.so'
        ],
    },
    'pce': {
        'name': 'PC Engine & SuperGrafx',
        'controls': [
            ("up", "Up"),
            ("down", "Down"),
            ("left", "Left"),
            ("right", "Right"),
            ("a", "I"),
            ("b", "II"),
            ("select", "Select"),
            ("start", "Run"),
        ],
        'exec': [
            'sudo', '-u', 'meldnafen', 'retroarch', '-v',
            '-L', '/usr/lib/libretro/mednafen_supergrafx_libretro.so'
        ],
    },
    'snes': {
        'name': 'Super Nintendo',
        'controls': [
            ("up", "Up"),
            ("down", "Down"),
            ("left", "Left"),
            ("right", "Right"),
            ("a", "A"),
            ("b", "B"),
            ("x", "X"),
            ("y", "Y"),
            ("l", "L"),
            ("r", "R"),
            ("select", "Select"),
            ("start", "Start"),
        ],
        'exec': [
            'sudo', '-u', 'meldnafen', 'retroarch', '-v',
            '-L', '/usr/lib/libretro/snes9x_next_libretro.so'
        ],
    },
    'md': {
        'name': 'Mega Drive / Genesis',
        'controls': [
            ("up", "Up"),
            ("down", "Down"),
            ("left", "Left"),
            ("right", "Right"),
            ("y", "A"),
            ("b", "B"),
            ("a", "C"),
            ("l", "X"),
            ("x", "Y"),
            ("r", "Z"),
            ("start", "Start"),
        ],
        'exec': [
            'sudo', '-u', 'meldnafen', 'retroarch', '-v',
            '-L', '/usr/lib/libretro/genesis_plus_gx_libretro.so'
        ],
    },
}
