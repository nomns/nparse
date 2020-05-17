from dataclasses import dataclass, field
from typing import List
import json

from helpers import logger
log = logger.get_logger(__name__)


@dataclass
class MapsSetting:
    auto_follow: bool = True
    parser_opacity: int = 30
    closest_z_alpha: int = 20
    current_z_alpha: int = 100
    geometry: List[int] = field(default_factory=lambda: [0, 0, 100, 100])
    grid_line_width: int = 1
    last_zone: str = 'west freeport'
    line_width: int = 1
    other_z_alpha: int = 5
    scale: float = 0.07
    show_grid: bool = True
    show_mouse_location: bool = True
    show_poi: bool = True
    toggled: bool = True
    use_z_mlayers: bool = False


@dataclass
class SpellsSetting:
    buff_bar_color: List[int] = field(default_factory=lambda: [40, 122, 169, 255])
    buff_text_color: List[int] = field(default_factory=lambda: [0, 0, 0, 255])
    casting_window_buffer: int = 1000
    debuff_bar_color: List[int] = field(default_factory=lambda: [221, 119, 0, 255])
    debuff_text_color: List[int] = field(default_factory=lambda: [0, 0, 0, 255])
    delay_self_buffs_on_zone: bool = True
    enemey_target_color: List[int] = field(default_factory=lambda: [68, 0, 0, 255])
    friendly_target_color: List[int] = field(default_factory=lambda: [0, 68, 0, 255])
    geometry: List[int] = field(default_factory=lambda: [101, 0, 100, 100])
    level: int = 1
    sound_enabled: bool = True
    sound_file: str = 'data/mp3/ding.mp3'
    target_text_color: List[int] = field(default_factory=lambda: [255, 255, 255, 255])
    toggled: bool = True
    use_casting_window: bool = True
    use_secondary: List[str] = field(default_factory=lambda: [
        'levitate', 'malise', 'malisement'])
    use_secondary_all: bool = False
    you_target_color: List[int] = field(default_factory=lambda: [22, 66, 91, 255])


@dataclass
class TextSetting:
    direction: str = 'down'
    fade_seconds: int = 10
    geometry: List[int] = field(default_factory=lambda: [201, 0, 100, 100])
    pixels_per_second: int = 35
    shadow_color: List[int] = field(default_factory=lambda: [0, 0, 0, 255])
    shadow_blur_radius: int = 20
    toggled: bool = True


@dataclass
class TriggersSetting:
    geometry: List[int] = field(default_factory=lambda: [301, 0, 100, 100])
    toggled: bool = True


@dataclass
class Profile:
    name: str = ''
    log_file: str = ''
    sound_volume: int = 25
    maps: MapsSetting = MapsSetting()
    spells: SpellsSetting = SpellsSetting()
    text: TextSetting = TextSetting()
    triggers: TriggersSetting = TriggersSetting()

    def json(self):
        return json.dumps(
            {
                k: v.__dict__ if type(v) not in [str, int] else v
                for k, v in self.__dict__.items()
            },
            indent=4,
            sort_keys=True
        )
