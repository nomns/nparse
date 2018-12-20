
import math

from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QRect

from .spell import Spell

from helpers import config


def get_spell_icon(icon_index):
    # Spell Icons are 40x40 pixels
    file_number = math.ceil(icon_index / 36)
    file_name = 'data/spells/spells0' + str(file_number) + '.png'
    spell_number = icon_index % 36
    file_row = math.floor((spell_number + 6) / 6)
    file_col = spell_number % 6 + 1
    x = (file_col - 1) * 40
    y = (file_row - 1) * 40
    icon_image = QPixmap(file_name)
    scaled_icon_image = icon_image.copy(QRect(x, y, 40, 40)).scaled(
        15, 15, transformMode=Qt.SmoothTransformation)
    label = QLabel()
    label.setPixmap(scaled_icon_image)
    label.setFixedSize(15, 15)
    return label


def create_spell_book():
    """ Returns a dictionary of Spell by k, v -> spell_name, Spell() """
    spell_book = {}
    with open('data/spells/spells_us.txt') as spell_file:
        for line in spell_file:
            values = line.strip().split('^')
            spell_book[values[1]] = Spell(
                id=int(values[0]),
                name=values[1].lower(),
                effect_text_you=values[6],
                effect_text_other=values[7],
                effect_text_worn_off=values[8],
                aoe_range=int(values[10]),
                max_targets=(6 if int(values[10]) > 0 else 1),
                cast_time=int(values[13]),
                resist_type=int(values[85]),
                duration_formula=int(values[16]),
                pvp_duration_formula=int(values[181]),
                duration=int(values[17]),
                pvp_duration=int(values[182]),
                type=int(values[83]),
                spell_icon=int(values[144])
            )
    return spell_book


def get_spell_duration(spell, level):
    if spell.name in config.data['spells']['use_secondary']:
        formula, duration = spell.pvp_duration_formula, spell.pvp_duration
    elif config.data['spells']['use_secondary_all'] and spell.type == 0:
        formula, duration = spell.pvp_duration_formula, spell.pvp_duration
    else:
        formula, duration = spell.duration_formula, spell.duration

    spell_ticks = 0
    if formula == 0:
        spell_ticks = 0
    if formula == 1:
        spell_ticks = int(math.ceil(level / float(2.0)))
        if spell_ticks > duration:
            spell_ticks = duration
    if formula == 2:
        spell_ticks = int(math.ceil(level / float(5.0) * 3))
        if spell_ticks > duration:
            spell_ticks = duration
    if formula == 3:
        spell_ticks = int(level * 30)
        if spell_ticks > duration:
            spell_ticks = duration
    if formula == 4:
        if duration == 0:
            spell_ticks = 50
        else:
            spell_ticks = duration
    if formula == 5:
        spell_ticks = duration
        if spell_ticks == 0:
            spell_ticks = 3
    if formula == 6:
        spell_ticks = int(math.ceil(level / float(2.0)))
        if spell_ticks > duration:
            spell_ticks = duration
    if formula == 7:
        spell_ticks = level
        if spell_ticks > duration:
            spell_ticks = duration
    if formula == 8:
        spell_ticks = level + 10
        if spell_ticks > duration:
            spell_ticks = duration
    if formula == 9:
        spell_ticks = int((level * 2) + 10)
        if spell_ticks > duration:
            spell_ticks = duration
    if formula == 10:
        spell_ticks = int(level * 3 + 10)
        if spell_ticks > duration:
            spell_ticks = duration
    if formula == 11:
        spell_ticks = duration
    if formula == 12:
        spell_ticks = duration
    if formula == 15:
        spell_ticks = duration
    if formula == 50:
        spell_ticks = 72000
    if formula == 3600:
        if duration == 0:
            spell_ticks = 3600
        else:
            spell_ticks = duration
    return spell_ticks