from config import profile


def parser_window() -> str:
    return """
        #NWindow {{
            background: rgba(0, 0, 0, {window_opacity});
            border: none;
            font-family: 'Noto Sans';
        }}

        #Container {{
            border: none;
        }}

        #ScrollArea {{
            background: transparent;
            border: none;
        }}

        #ScrollArea QScrollBar::vertical {{
            background: #111;
            width: 12px;
            margin: 12px 0 12px 0;
        }}

        #ScrollArea QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
        }}

        #ScrollArea QScrollBar::up-arrow:vertical {{
            background: #333;
            width: 10px;
            height: 10px;
            border: none;
            border-top-right-radius: 5px;
            border-top-left-radius: 5px;
        }}

        #ScrollArea QScrollBar::down-arrow:vertical {{
            background: #333;
            width: 10px;
            height: 10px;
            border: none;
            border-bottom-right-radius: 5px;
            border-bottom-left-radius: 5px;
        }}

        #ScrollArea QScrollBar::add-line:vertical {{
            background: none;
            height: 12px;
            subcontrol-position: bottom;
            subcontrol-origin: margin;
        }}

        #ScrollArea QScrollBar::sub-line:vertical {{
            background: none;
            height: 12px;
            subcontrol-position: top;
            subcontrol-origin: margin;
        }}

        #ScrollArea QScrollBar::handle:vertical {{
            min-height: 10px;
            width: 10px;
            max-width: 10px;
            background: #333;
            border: 1px solid #111;
        }}

        #NWindowTitle {{
            color: rgb(200, 200, 200);
            font-weight: bold;
            font-size: 14px;
        }}

        #NWindowMenu {{
            color: white;
        }}

        #NWindowMenu QPushButton {{
            color: darkslategray;
            font-size: 18px;
            padding: 1px;
            border-radius: 5px;
            height: 20px;
            width: 20px;
        }}

        #NWindowMenu QPushButton:hover {{
            background: #e5d62d;
            color: black;
        }}

        #NWindowMenu QPushButton:checked {{
            color: white;
        }}

        #NWindowMoveButton {{
            color: rgba(255, 255, 255, 255);
            font-size: 18px;
            padding: 1px;
            border-radius: 5px;
            height: 20px;
            width: 20px;
        }}

        #NWindowMenu QLabel {{
            color: rgb(200, 200, 200);
            font-weight: bold;
            font-size: 14px;
        }}

        #NWindowMenu QSpinBox {{
            color:white;
            font-size: 14px;
            font-weight: bold;
            padding: 3px;
            background-color: #050505;
            border: none;
            border-radius: 3px;
        }}

        #MapCanvas {{
            background: transparent;
            border: none;
        }}

        #NMoverTitle {{
            color: white;
            font-size: 16px;
        }}

        #TextView {{
            border: none;
            background: transparent;
        }}

        """.format(
        window_opacity=profile.maps.opacity / 100 * 255
    )


group_label = """
    #GroupLabel {{
        color: rgba({f});
        font-size: 12px;
        background: qlineargradient(x0: 0, x1: 1,
            stop: 0 transparent,
            stop: 0.3 rgba({c}),
            stop: 0.7 rgba({c}),
            stop: 1.0 transparent
        );
    }}
"""


def enemy_target() -> str:
    return group_label.format(
        c=",".join(map(str, profile.spells.enemy_target_color)),
        f=",".join(map(str, profile.spells.target_text_color)),
    )


def friendly_target() -> str:
    return group_label.format(
        c=",".join(map(str, profile.spells.friendly_target_color)),
        f=",".join(map(str, profile.spells.target_text_color)),
    )


def you_target() -> str:
    return group_label.format(
        c=",".join(map(str, profile.spells.you_target_color)),
        f=",".join(map(str, profile.spells.target_text_color)),
    )


def good_spell() -> str:
    return """
        QProgressBar {{
            background: black;
            border-top: 1px solid rgba(0, 0, 0, 255);
            border-bottom: 1px solid rgba(0, 0, 0, 255);
        }}
        QProgressBar::horizontal {{
            background: #999999;
        }}
        QProgressBar::chunk {{
            background: qlineargradient(y0: 0, y1: 1,
                stop: 0 rgba(0, 0, 0, 255),
                stop: 0.1 rgba({c}),
                stop: 0.9 rgba({c}),
                stop: 1 rgba(0, 0, 0, 255)
            );
            border-right: 1px solid rgb(100, 100, 100);
        }}
        QLabel {{
            color: rgba({f});
            font-size: 12px;
        }}
    """.format(
        c=",".join(map(str, profile.spells.buff_bar_color)),
        f=",".join(map(str, profile.spells.buff_text_color)),
    )


def spell_warning() -> str:
    return """
        QProgressBar {
            border-top: 1px solid rgba(255, 0, 0, 255);
            border-bottom: 1px solid rgba(255, 0, 0, 255);
        }
        QLabel {
            font-weight: bold;
        }
    """


def debuff_spell() -> str:
    return """
        QProgressBar {{
            background: black;
            border-top: 1px solid rgba(0, 0, 0, 255);
            border-bottom: 1px solid rgba(0, 0, 0, 255);
        }}
        QProgressBar::horizontal {{
            background: #999999;
        }}
        QProgressBar::chunk {{
            background: qlineargradient(y0: 0, y1: 1,
                stop: 0 rgba(0, 0, 0, 255),
                stop: 0.1 rgba({c}),
                stop: 0.9 rgba({c}),
                stop: 1 rgba(0, 0, 0, 255)
            );
            border-right: 1px solid rgb(100, 100, 100);
        }}
        QLabel {{
            color: rgba({f});
            font-size: 12px;
        }}
    """.format(
        c=",".join(map(str, profile.spells.debuff_bar_color)),
        f=",".join(map(str, profile.spells.debuff_text_color)),
    )


def trigger(bar_color, text_color) -> str:
    return """
        QProgressBar {{
            background: black;
            border-top: 1px solid rgba(0, 0, 0, 255);
            border-bottom: 1px solid rgba(0, 0, 0, 255);
        }}
        QProgressBar::horizontal {{
            background: #999999;
        }}
        QProgressBar::chunk {{
            background: qlineargradient(y0: 0, y1: 1,
                stop: 0 rgba(0, 0, 0, 255),
                stop: 0.1 rgba({c}),
                stop: 0.9 rgba({c}),
                stop: 1 rgba(0, 0, 0, 255)
            );
            border-right: 1px solid rgb(100, 100, 100);
        }}
        QLabel {{
            color: rgba({f});
            font-size: 12px;
        }}
    """.format(
        c=",".join(map(str, bar_color)), f=",".join(map(str, text_color))
    )
