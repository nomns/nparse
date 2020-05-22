from dataclasses import dataclass, field, asdict
from typing import List, Dict
import json

from PyQt5.QtCore import QFile, QByteArray


@dataclass
class TriggerTimer:
    enabled: bool = False
    duration: str = '60'
    icon: int = 1
    text: str = ''
    persistent: bool = False
    bar_color: List[int] = field(default_factory=lambda: [181, 178, 34, 255])
    text_color: List[int] = field(default_factory=lambda: [0, 0, 0, 255])


@dataclass
class TriggerText:
    enabled: bool = False
    text: str = ''
    text_size: int = 20
    color: List[int] = field(default_factory=lambda: [101, 184, 50, 255])


@dataclass
class TriggerSound:
    enabled: bool = False
    volume: int = 100
    data: QByteArray = None


@dataclass
class TriggerAction:
    sound: TriggerSound = TriggerSound()
    timer: TriggerTimer = TriggerTimer()
    text: TriggerText = TriggerText()


@dataclass
class Trigger:
    name: str = ''
    text: str = ''
    regex: str = ''
    duration: str = '60'
    start_action: TriggerAction = TriggerAction()
    end_action: TriggerAction = TriggerAction()

    def json(self):
        return json.dumps(asdict(self), indent=4, sort_keys=True)

    def update(self, dictionary: Dict[str, any], ref: Dict[str, any] = None):
        ref = self.__dict__ if ref is None else ref
        for k, v in dictionary.items():
            if type(ref[k]) in [TriggerAction, TriggerSound, TriggerText, TriggerTimer]:
                self.update(v, ref[k].__dict__)
            else:
                ref[k] = v


@dataclass
class TriggerContainer:
    name: str = ''
    triggers: List[any] = field(default_factory=lambda: [])
