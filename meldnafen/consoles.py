consoles = {
    'nes': {
        'name': 'Nintendo Entertainment System',
        'controls': [
            ("up_btn", "Up"),
            ("down_btn", "Down"),
            ("left_btn", "Left"),
            ("right_btn", "Right"),
            ("a_btn", "A"),
            ("b_btn", "B"),
            ("start_btn", "Start"),
            ("select_btn", "Select"),
        ],
        'exec': [
            'sudo', '-u', 'meldnafen', 'retroarch', '-v', '-L',
            '/usr/lib/libretro/quicknes_libretro.so'
        ],
    },
    'pce': {
        'name': 'PC Engine & SuperGrafx',
        'controls': [
            ("up_btn", "Up"),
            ("down_btn", "Down"),
            ("left_btn", "Left"),
            ("right_btn", "Right"),
            ("y_btn", "A"),
            ("b_btn", "B"),
            ("a_btn", "C"),
            ("l_btn", "X"),
            ("x_btn", "Y"),
            ("r_btn", "Z"),
            ("start_btn", "Start"),
        ],
        'exec': [
            'sudo', '-u', 'meldnafen', 'retroarch', '-v', '-L',
            '/usr/lib/libretro/mednafen_supergrafx_libretro.so'
        ],
    },
    'snes': {
        'name': 'Super Nintendo',
        'controls': [
            ("up_btn", "Up"),
            ("down_btn", "Down"),
            ("left_btn", "Left"),
            ("right_btn", "Right"),
            ("y_btn", "A"),
            ("b_btn", "B"),
            ("a_btn", "C"),
            ("l_btn", "X"),
            ("x_btn", "Y"),
            ("r_btn", "Z"),
            ("start_btn", "Start"),
        ],
        'exec': [
            'sudo', '-u', 'meldnafen', 'retroarch', '-v', '-L',
            '/usr/lib/libretro/snes9x_next_libretro.so'
        ],
    },
    'md': {
        'name': 'Mega Drive / Genesis',
        'controls': [
            ("up_btn", "Up"),
            ("down_btn", "Down"),
            ("left_btn", "Left"),
            ("right_btn", "Right"),
            ("y_btn", "A"),
            ("b_btn", "B"),
            ("a_btn", "C"),
            ("l_btn", "X"),
            ("x_btn", "Y"),
            ("r_btn", "Z"),
            ("start_btn", "Start"),
        ],
        'exec': [
            'sudo', '-u', 'meldnafen', 'retroarch', '-v', '-L',
            '/usr/lib/libretro/genesis_plus_gx_libretro.so'
        ],
    },
}
