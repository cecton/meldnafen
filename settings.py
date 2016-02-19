width, height = 256, 224

emulators = [
    {
        'name': "PC Engine",
        'path': 'pce_roms',
        'exclude': '*.bin',
        'exec': ['mednafen', '-force_module', 'pce_fast'],
    },
    {
        'name': "Nintendo Entertainment System",
        'path': 'nes_roms',
        'exec': ['mednafen'],
    },
    {
        'name': "Mega Drive",
        'path': 'md_roms',
        'exec': ['mednafen'],
    },
    {
        'name': "Super NES",
        'path': 'snes_roms',
        'exec': ['zsnes'],
    },
]

menu_actions = [
    ("Shutdown", ['systemctl', 'poweroff']),
    ("Reboot", ['systemctl', 'reboot']),
    ("Quit", None),
]
