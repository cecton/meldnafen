consoles = {
    'nes': {
        'name': 'Nintendo Entertainment System',
        'controls': [
            ("input_player{}_up_btn", "Up"),
            ("input_player{}_down_btn", "Down"),
            ("input_player{}_left_btn", "Left"),
            ("input_player{}_right_btn", "Right"),
            ("input_player{}_a_btn", "A"),
            ("input_player{}_b_btn", "B"),
            ("input_player{}_start_btn", "Start"),
            ("input_player{}_select_btn", "Select"),
        ],
        'exec': ['retroarch'],
    },
    'md': {
        'name': 'Mega Drive / Genesis',
        'controls': [
            ("input_player{}_up_btn", "Up"),
            ("input_player{}_down_btn", "Down"),
            ("input_player{}_left_btn", "Left"),
            ("input_player{}_right_btn", "Right"),
            ("input_player{}_y_btn", "A"),
            ("input_player{}_b_btn", "B"),
            ("input_player{}_a_btn", "C"),
            ("input_player{}_l_btn", "X"),
            ("input_player{}_x_btn", "Y"),
            ("input_player{}_r_btn", "Z"),
            ("input_player{}_start_btn", "Start"),
        ],
        'exec': ['retroarch'],
    },
}
