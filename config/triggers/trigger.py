from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class TriggerChoice:
    name: str = ""
    enabled: bool = False
    type_: str = "group"
    group: List[any] = field(default_factory=lambda: [])


@dataclass
class TriggerTimer:
    enabled: bool = False
    duration: str = "60"
    icon: int = 1
    text: str = ""
    persistent: bool = False
    bar_color: List[int] = field(default_factory=lambda: [181, 178, 34, 255])
    text_color: List[int] = field(default_factory=lambda: [0, 0, 0, 255])


@dataclass
class TriggerText:
    enabled: bool = False
    text: str = ""
    text_size: int = 20
    color: List[int] = field(default_factory=lambda: [101, 184, 50, 255])


@dataclass
class TriggerSound:
    enabled: bool = False
    volume: int = 100
    name: str = ""


@dataclass
class TriggerAction:
    sound: TriggerSound = field(default_factory=lambda: TriggerSound())
    timer: TriggerTimer = field(default_factory=lambda: TriggerTimer())
    text: TriggerText = field(default_factory=lambda: TriggerText())


@dataclass
class Trigger:
    name: str = ""
    type_: str = "trigger"
    text: str = ""
    regex: str = ""
    duration: str = "60"
    start_action: TriggerAction = field(default_factory=lambda: TriggerAction())
    end_action: TriggerAction = field(default_factory=lambda: TriggerAction())

    def update(self, dictionary: Dict[str, any], ref: Dict[str, any] = None):
        ref = self.__dict__ if ref is None else ref
        for k, v in dictionary.items():
            if isinstance(
                ref[k], (TriggerAction, TriggerSound, TriggerText, TriggerTimer)
            ):
                self.update(v, ref[k].__dict__)
            else:
                ref[k] = v


@dataclass
class TriggerContainer:
    name: str = ""
    type_: str = "container"
    items: List[any] = field(default_factory=lambda: [])
