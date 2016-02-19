#!/usr/bin/env python

import fnmatch
import harness
from itertools import islice
from math import ceil
import os
import re
import settings


HIGHLIGHT = (0xff, 0xff, 0x00, 0xff)
LINE_SPACE = 8
PAGE_SIZE = 20


game = harness.Harness(width=settings.width, height=settings.height, zoom=3)

font = game.load_bitmap_font("font.png", 4, 11,
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!?()[]~-_+@"
    ":/'., ")

emulator = 0
page = 0
last_page = 0
select = 0
roms = []
menu = False
command = None


def write(renderer, x, y, text, **kw):
    filtered_text = "".join(filter(lambda x: x in font.font_map, text))\
        .replace('  ', ' ')
    renderer.draw_text(font, x, y, filtered_text, **kw)


def run_emulator():
    global command
    os.chdir(settings.emulators[emulator]['path'])
    command = settings.emulators[emulator]['exec'] + \
        [roms[page * PAGE_SIZE + select]]
    game.quit()


def run_command():
    global command
    _, command = settings.menu_actions[select]
    game.quit()


def update_roms():
    global roms
    global select
    global page
    global last_page
    includes = [
        re.compile(fnmatch.translate(x))
        for x in (
            settings.emulators[emulator]['include'].split(';')
            if settings.emulators[emulator].get('include')
            else []
        )
    ]
    excludes = [
        re.compile(fnmatch.translate(x))
        for x in (
            settings.emulators[emulator]['exclude'].split(';')
            if settings.emulators[emulator].get('exclude')
            else []
        )
    ]
    roms = sorted(filter(
        lambda x: (not any(y.match(x) for y in excludes) or
            any(y.match(x) for y in includes)),
        os.listdir(settings.emulators[emulator]['path'])))
    last_page = ceil(len(roms) / PAGE_SIZE)
    select = 0
    page = 0


@game.draw
def draw_list_roms(renderer):
    border = 10
    bottom = game.height - border - font.height
    x, y = border, border
    write(renderer, x, y, settings.emulators[emulator]['name'])
    y += LINE_SPACE * 2
    if not roms:
        write(renderer, x, y, "No rom found")
        return
    for i, rom in enumerate(islice(roms, (PAGE_SIZE * page),
            (PAGE_SIZE * (page + 1)))):
        write(renderer, x, y, rom, tint=(i == select and HIGHLIGHT))
        y += LINE_SPACE
    y += LINE_SPACE
    write(renderer, x, y,
        "Page %d of %d (%d roms)" % ((page + 1), last_page, len(roms)))


@game.update
def update_list_roms(dt):
    global emulator
    global select
    global page
    if game.keys[game.KEY_UP]:
        game.keys[game.KEY_UP] = False
        select -= 1
        if select < 0:
            select = PAGE_SIZE - 1
            page -= 1
        if page < 0:
            page = last_page - 1
            select = len(roms) % PAGE_SIZE - 1
    elif game.keys[game.KEY_DOWN]:
        game.keys[game.KEY_DOWN] = False
        select += 1
        if select >= PAGE_SIZE:
            select = 0
            page += 1
        if ((page == last_page - 1 and select >= len(roms) % PAGE_SIZE) or
                page > last_page):
            page = 0
            select = 0
    elif game.keys[game.KEY_LEFT]:
        game.keys[game.KEY_LEFT] = False
        emulator = (emulator - 1) % len(settings.emulators)
        update_roms()
    elif game.keys[game.KEY_RIGHT]:
        game.keys[game.KEY_RIGHT] = False
        emulator = (emulator + 1) % len(settings.emulators)
        update_roms()
    elif game.keys[game.KEY_A]:
        game.keys[game.KEY_A] = False
        run_emulator()


def draw_menu(renderer):
    border = 10
    bottom = game.height - border - font.height
    x, y = border, border
    for i, (label, _) in enumerate(settings.menu_actions):
        write(renderer, x, y, label, tint=(i == select and HIGHLIGHT))
        y += LINE_SPACE


def update_menu(dt):
    global select
    global page
    if game.keys[game.KEY_UP]:
        game.keys[game.KEY_UP] = False
        select -= 1
        if select < 0:
            select = len(settings.menu_actions) - 1
    elif game.keys[game.KEY_DOWN]:
        game.keys[game.KEY_DOWN] = False
        select += 1
        if select >= len(settings.menu_actions):
            select = 0
    elif game.keys[game.KEY_A]:
        game.keys[game.KEY_A] = False
        run_command()


@game.update
def update(dt):
    global menu
    global select
    global page
    if game.keys[game.KEY_ESCAPE]:
        game.quit()
    elif game.keys[game.KEY_S]:
        game.keys[game.KEY_S] = False
        menu = not menu
        if menu:
            game.draw(draw_menu)
            game.update(update_menu)
            game.remove_handler(draw_list_roms)
            game.remove_handler(update_list_roms)
        else:
            game.draw(draw_list_roms)
            game.update(update_list_roms)
            game.remove_handler(draw_menu)
            game.remove_handler(update_menu)
        select = 0
        page = 0


update_roms()
game.loop()
if command:
    os.execvp(command[0], command)
exit(1)
