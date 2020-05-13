from dataclasses import dataclass, field
from typing import List


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
    name: str = '__default__'
    log_file: str = ''
    eq_dir: str = ''
    parser_opacity: int = 30
    qt_scale_factor: int = 100
    sound_volume: int = 25
    update_check: bool = True
    maps: MapsSetting = None
    spells: SpellsSetting = None
    text: TextSetting = None
    triggers: TriggersSetting = None

    def __post_init__(self):
        self.maps = self.maps if self.maps else MapsSetting()
        self.spells = self.spells if self.spells else SpellsSetting()
        self.text = self.text if self.text else TextSetting()
        self.triggers = self.triggers if self.triggers else TriggersSetting()

