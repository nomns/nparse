import os
from dataclasses import dataclass, field, asdict
from typing import List, Dict
from datetime import datetime
import json

from utils import logger, mp3_to_data, parse_name_from_log, searches

from ..triggers.trigger import TriggerChoice

log = logger.get_logger(__name__)

PROFILES_LOCATION = "./data/profiles"


@dataclass
class ProfileMaps:
    auto_follow: bool = True
    opacity: int = 30
    closest_z_alpha: int = 20
    current_z_alpha: int = 100
    geometry: List[int] = field(default_factory=lambda: [0, 0, 300, 300])
    grid_line_width: int = 1
    last_zone: str = "west freeport"
    line_width: int = 1
    other_z_alpha: int = 5
    scale: float = 0.07
    show_grid: bool = True
    show_mouse_location: bool = True
    show_poi: bool = True
    toggled: bool = False
    use_z_layers: bool = False


@dataclass
class ProfileSpells:
    buff_bar_color: List[int] = field(default_factory=lambda: [40, 122, 169, 255])
    buff_text_color: List[int] = field(default_factory=lambda: [0, 0, 0, 255])
    casting_window_buffer: int = 1000
    debuff_bar_color: List[int] = field(default_factory=lambda: [168, 61, 61, 255])
    debuff_text_color: List[int] = field(default_factory=lambda: [0, 0, 0, 255])
    delay_self_buffs_on_zone: bool = True
    enemy_target_color: List[int] = field(default_factory=lambda: [104, 61, 61, 255])
    friendly_target_color: List[int] = field(default_factory=lambda: [0, 68, 0, 255])
    geometry: List[int] = field(default_factory=lambda: [301, 0, 300, 300])
    level: int = 1
    persistent_buffs: bool = False
    persistent_debuffs: bool = False
    sound_enabled: bool = True
    sound_file: str = "data/mp3/ding.mp3"
    sound_volume: int = 100
    target_text_color: List[int] = field(default_factory=lambda: [255, 255, 255, 255])
    toggled: bool = False
    use_casting_window: bool = True
    use_secondary_all: bool = False
    you_target_color: List[int] = field(default_factory=lambda: [22, 66, 91, 255])


@dataclass
class ProfileText:
    direction: str = "down"
    fade_seconds: int = 10
    geometry: List[int] = field(default_factory=lambda: [901, 0, 300, 300])
    pixels_per_second: int = 35
    shadow_color: List[int] = field(default_factory=lambda: [0, 0, 0, 255])
    shadow_blur_radius: int = 5
    toggled: bool = False


@dataclass
class ProfileTriggers:
    geometry: List[int] = field(default_factory=lambda: [601, 0, 300, 300])
    toggled: bool = False


@dataclass
class Profile:
    name: str = ""  # blank name means profile will not save.
    log_file: str = ""
    maps: ProfileMaps = field(default_factory=lambda: ProfileMaps())
    spells: ProfileSpells = field(default_factory=lambda: ProfileSpells())
    text: ProfileText = field(default_factory=lambda: ProfileText())
    triggers: ProfileTriggers = field(default_factory=lambda: ProfileTriggers())
    trigger_choices: List[TriggerChoice] = field(default_factory=lambda: [])

    def __post_init__(self):
        if not os.path.exists(PROFILES_LOCATION):
            os.mkdir(PROFILES_LOCATION)
        if self.log_file and not self.name:
            self.name = parse_name_from_log(self.log_file)

    def switch(self, log_file: str) -> None:
        self.save()
        log.info("Switching Profiles")
        self.load(log_file)

    def load(self, log_file: str) -> None:
        log.info(f"Loading profile {log_file}.")
        profile = Profile()
        if os.path.exists(os.path.join("data/profiles", f"{log_file}.json")):
            try:
                profile_dict = json.loads(
                    open(os.path.join("data/profiles", f"{log_file}.json"), "r").read()
                )
                profile.update(profile_dict)
            except:
                log.warning(f"Unable to load profile: {log_file}", exc_info=True)
        else:
            log.info(f"Creating new log for {log_file}")
            profile.update(asdict(self))
            profile.log_file = log_file
            profile.name = parse_name_from_log(log_file)
        self.update(asdict(profile))
        self.spells.sound_data = mp3_to_data(profile.spells.sound_file)

    def save(self) -> None:
        try:
            if self.name:
                log.info(f"Saving profile: {self.log_file}.")
                open(
                    os.path.join("data/profiles", f"{self.log_file}.json"), "w",
                ).write(self.json())
        except:
            log.warning(f"Unable to save profile: {self.name}", exc_info=True)

    def json(self):
        return json.dumps(asdict(self), indent=4, sort_keys=True)

    def update(self, dictionary: Dict[str, any], ref: Dict[str, any] = None):
        ref = self.__dict__ if ref is None else ref
        for k, v in dictionary.items():
            if k in ref:
                if isinstance(
                    ref[k], (ProfileMaps, ProfileSpells, ProfileText, ProfileTriggers)
                ):
                    self.update(v, ref[k].__dict__)
                else:
                    if k == "trigger_choices":
                        ref[k] = self.parse_trigger_choices(v)
                    else:
                        ref[k] = v

    def parse_trigger_choices(
        self, choice_list: List[Dict[str, any]]
    ) -> List[TriggerChoice]:
        choices = []
        for choice in choice_list:
            tc = TriggerChoice(
                name=choice["name"], enabled=choice["enabled"], type_=choice["type_"]
            )
            if tc.type_ == "group" and choice["group"]:
                tc.group = self.parse_trigger_choices(choice["group"])
            choices.append(tc)
        return choices

    def parse(self, timestamp: datetime, text: str) -> None:
        # parse level up
        r = searches.level.search(text)
        if r:
            self.spells.level = int(r.group(1))
