import os
from dataclasses import dataclass, field, asdict
import json
import glob
from typing import List, Dict
from shutil import copyfile

from PyQt5.QtMultimedia import QMediaContent

from utils import logger, get_unique_str, mp3_to_data

from .trigger import Trigger, TriggerContainer


log = logger.get_logger(__name__)


@dataclass
class TriggerPackage:
    name: str = None
    type_: str = "package"
    items: List[any] = field(default_factory=lambda: [])

    def __post_init__(self):
        # create items that won't show up in as_dict
        self.location = os.path.join("data/triggers", self.name)
        self.audio_data: Dict[str, QMediaContent] = {}

        self.load()

    def load(self) -> None:
        if os.path.exists(self.location):
            data = None
            # load trigger data and convert to dataclasses
            if os.path.exists(os.path.join(self.location, "triggers.json")):
                with open(os.path.join(self.location, "triggers.json"), "r") as f:
                    data = json.loads(f.read())
                    for k, v in data.items():
                        if k == "items":
                            self.items = self._load(v)

                # load sound data into memory
                data_path = os.path.join(self.location, "data")
                mp3_files = [
                    os.path.basename(f)
                    for f in glob.glob(os.path.join(data_path, "*.mp3"))
                ]
                for mp3_file in mp3_files:
                    self.audio_data[mp3_file] = mp3_to_data(
                        os.path.join(data_path, mp3_file)
                    )
            else:
                self.save()
                self.load()
        else:
            os.mkdir(self.location)
            os.mkdir(os.path.join(self.location, "data"))
            self.save()

    def _load(self, items: List[any]) -> List[any]:
        converted = []
        for item in items:
            if item["type_"] == "container":
                container = TriggerContainer(
                    name=item["name"], items=self._load(item["items"])
                )
                converted.append(container)
            if item["type_"] == "trigger":
                trigger = Trigger()
                trigger.update(item)
                trigger.package = self
                converted.append(trigger)
        return converted

    def save(self) -> None:
        if not os.path.isdir(self.location):
            os.mkdir(self.location)

        with open(os.path.join(self.location, "triggers.json"), "w") as f:
            f.write(json.dumps(asdict(self), indent=4, sort_keys=True))

    def add_audio(self, mp3_location: str) -> str:
        # if name exists, and data is different, creates a unique name and returns it
        name = os.path.basename(mp3_location)
        if name in self.audio_data:
            data = mp3_to_data(os.path.join(self.location, "data", name))
            if self.audio_data[name] == data:
                return name
            else:
                filename, ext = os.path.splitext(name)
                filename = get_unique_str(
                    filename, [os.path.splitext(x)[0] for x in self.audio_data.keys()]
                )
                name = os.path.join(filename, ext)
        copyfile(mp3_location, os.path.join(self.location, "data", name))
        self.audio_data[name] = mp3_to_data(os.path.join(self.location, "data", name))
        return name

    def rename(self, name: str) -> None:
        try:
            os.rename(self.location, os.path.join(os.path.split[0], f"{name}.zip"))
        except:
            log.warning(
                f"Unable to rename file {self.location} to {name}.zip", exc_info=True
            )
