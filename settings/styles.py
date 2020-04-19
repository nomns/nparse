from helpers import config


def hgradient(rgb):
    return """
        ::chunk {{
            background-color: qlineargradient(y0: 0, y1: 1,
                stop: 0 transparent, stop: 0.3 rgb({c}),
                stop: 0.30001 rgb({c}), stop: 0.7 rgb({c}),
                stop: 0.70001 rgb({c}), stop: 1 transparent);}}
        """.format(c=','.join(map(str, rgb)))


parser_window = """
ParserWindow {
    background-color: black;
    border: none;
    font-family: 'Noto Sans';
}

#Container {
    background-color: black;
    border: none;
}

#ScrollArea {
    border: none;
}

#ScrollArea QScrollBar::vertical {
    background: #111;
    width: 12px;
    margin: 12px 0 12px 0;
}

#ScrollArea QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

#ScrollArea QScrollBar::up-arrow:vertical {
    background: #333;
    width: 10px;
    height: 10px;
    border: none;
    border-top-right-radius: 5px;
    border-top-left-radius: 5px;
}

#ScrollArea QScrollBar::down-arrow:vertical {
    background: #333;
    width: 10px;
    height: 10px;
    border: none;
    border-bottom-right-radius: 5px;
    border-bottom-left-radius: 5px;
}

#ScrollArea QScrollBar::add-line:vertical {
    background: none;
    height: 12px;
    subcontrol-position: bottom;
    subcontrol-origin: margin;
}

#ScrollArea QScrollBar::sub-line:vertical {
    background: none;
    height: 12px;
    subcontrol-position: top;
    subcontrol-origin: margin;
}

#ScrollArea QScrollBar::handle:vertical {
    min-height: 10px;
    width: 10px;
    max-width: 10px;
    background: #333;
    border: 1px solid #111;
}

#ParserWindowMoveButton {
    color:white;
    background: black;
    font-size: 18px;
    padding: 1px;
    border-radius: 5px;
    height: 20px;
    width: 20px;
}

#ParserWindowTitle {
    color: rgb(200, 200, 200);
    font-weight: bold;
    font-size: 14px;
}

#ParserWindowMenu QPushButton {
    color: darkslategray;
    background: black;
    font-size: 18px;
    padding: 1px;
    border-radius: 5px;
    height: 20px;
    width: 20px;
}

#ParserWindowMenu QPushButton:hover {
    background: #e5d62d;
    color: black;
}

#ParserWindowMenu QPushButton:checked {
    color: white;
}

#ParserWindowMenu QLabel {

    color: rgb(200, 200, 200);
    font-weight: bold;
    font-size: 14px;
}

#ParserWindowMenu QSpinBox {
    color:white;
    font-size: 14px;
    font-weight: bold;
    padding: 3px;
    background-color: #050505;
    border: none;
    border-radius: 3px;
}

#MapCanvas {
    background-color: rgb(0, 0, 0);
    border:none;
}

#MapAreaLabel {
    color: rgb(200, 200, 200);
    font-size: 12px;
}
"""


def enemy_target():
    return """
        #SpellTargetLabel {{
            color: white;
            font-size: 12px;
            background: qlineargradient(y0: 0, y1: 1,
                stop: 0 rgba({c}), stop: 0.7 rgba({c}),
                stop: 1.0 transparent
            );
        }}
    """.format(
        c=','.join(map(str, config.data['spells']['enemy_target_color'])),
        f=','.join(map(str, config.data['spells']['target_text_color']))
    )


def friendly_target():
    return """
        #SpellTargetLabel {{
            color: rgba({f});
            font-size: 12px;
            background: qlineargradient(y0: 0, y1: 1,
                stop: 0 rgba({c}), stop: 0.7 rgba({c}),
                stop: 1.0 transparent
            );
        }}
    """.format(
        c=','.join(map(str, config.data['spells']['friendly_target_color'])),
        f=','.join(map(str, config.data['spells']['target_text_color']))
    )


def you_target():
    return """
        #SpellTargetLabel {{
            color: rgba({f});
            font-size: 12px;
            background: qlineargradient(y0: 0, y1: 1,
                stop: 0 rgba({c}), stop: 0.7 rgba({c}),
                stop: 1.0 transparent
            );
        }}
    """.format(
        c=','.join(map(str, config.data['spells']['you_target_color'])),
        f=','.join(map(str, config.data['spells']['target_text_color']))
    )


def good_spell():
    return """
        QProgressBar::chunk {{
            background: qlineargradient(y0: 0, y1: 1,
                stop: 0 rgba({c}),
                stop: 0.5 rgba({c}),
                stop: 1 transparent
            );
            border-right: 1px solid rgb(100, 100, 100);
        }}
        QLabel {{
            color: rgba({f});
            font-size: 12px;
        }}
    """.format(
        c=','.join(map(str, config.data['spells']['buff_bar_color'])),
        f=','.join(map(str, config.data['spells']['buff_text_color']))
    )


def spell_warning():
    return """
        QProgressBar {
            border-top: 2px solid rgba(255, 0, 0, 70%);
            border-bottom: 2px solid rgba(255, 0, 0, 70%);
        }
        QLabel {
            font-weight: bold;
        }
    """


def debuff_spell():
    return """
        QProgressBar::chunk {{
            font-size: 12px;
            background: qlineargradient(y0: 0, y1: 1,
                stop: 0 rgba({c}),
                stop: 0.5 rgba({c}),
                stop: 1 transparent
            );
        }}
        QLabel {{
            color: rgba({f});
            font-size: 12px;
        }}
    """.format(
        c=','.join(map(str, config.data['spells']['debuff_bar_color'])),
        f=','.join(map(str, config.data['spells']['debuff_text_color']))
    )

def trigger(bar_color, text_color):
    return """
        QProgressBar::chunk {{
            background: qlineargradient(y0: 0, y1: 1,
                stop: 0 rgb({c}),
                stop: 0.5 rgb({c}),
                stop: 1 transparent
            );
            border-right: 1px solid rgb(100, 100, 100);
        }}
        QLabel {{
            color: rgb({f});
            font-size: 12px;
        }}
    """.format(
        c=','.join(map(str, bar_color)),
        f=','.join(map(str, text_color))
    )
