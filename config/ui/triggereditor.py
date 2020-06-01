import os

from PyQt5.QtWidgets import QDialog, QFileDialog, QMessageBox
from PyQt5 import uic
from PyQt5.QtGui import QColor, QPalette, QRegExpValidator
from PyQt5.QtCore import QRegExp

from utils import (
    get_spell_icon,
    resource_path,
    sound,
    get_rgb,
    set_qcolor,
    create_regex_from,
    get_color,
)

from config.trigger import Trigger


class TriggerEditor(QDialog):
    def __init__(self, parent: any, trigger: Trigger):
        super().__init__(parent)
        uic.loadUi(resource_path("data/ui/triggereditor.ui"), self)
        self.trigger: Trigger = trigger
        self._set_values(self.trigger)

    # Events

    def startTimerTextLineEditChanged(self, new_text: str) -> None:
        self.startTimerExample.setText(new_text)

    def endTimerTextLineEditChanged(self, new_text: str) -> None:
        self.endTimerExample.setText(new_text)

    def startTimerIconSpinBoxChanged(self, icon_index: int) -> None:
        self.startTimerIconLayout.removeItem(self.startTimerIconLayout.itemAt(0))
        self.startTimerIconLayout.addWidget(get_spell_icon(icon_index))

    def endTimerIconSpinBoxChanged(self, icon_index: int) -> None:
        self.endTimerIconLayout.removeItem(self.endTimerIconLayout.itemAt(0))
        self.endTimerIconLayout.addWidget(get_spell_icon(icon_index))

    def startTimerBarColorButtonClicked(self) -> None:
        set_qcolor(
            self.startTimerExample,
            background=get_color(
                self, get_rgb(self.startTimerExample, QPalette.Background)
            ),
        )

    def endTimerBarColorButtonClicked(self) -> None:
        set_qcolor(
            self.endTimerExample,
            background=get_color(
                self, get_rgb(self.endTimerExample, QPalette.Background)
            ),
        )

    def startTimerTextColorButtonClicked(self) -> None:
        set_qcolor(
            self.startTimerExample,
            foreground=get_color(
                self, get_rgb(self.startTimerExample, QPalette.Foreground)
            ),
        )

    def endTimerTextColorButtonClicked(self) -> None:
        set_qcolor(
            self.endTimerExample,
            foreground=get_color(
                self, get_rgb(self.endTimerExample, QPalette.Foreground)
            ),
        )

    def startTextTextLineEditChanged(self, new_text: str) -> None:
        self.startTextExample.setText(self.startTextTextLineEdit.text())

    def endTextTextLineEditChanged(self, new_text: str) -> None:
        self.endTextExample.setText(self.endTextTextLineEdit.text())

    def startTextSizeSpinBoxChanged(self, new_value: int):
        f = self.startTextExample.font()
        f.setPointSize(new_value)
        self.startTextExample.setFont(f)

    def endTextSizeSpinBoxChanged(self, new_value: int):
        f = self.endTextExample.font()
        f.setPointSize(new_value)
        self.endTextExample.setFont(f)

    def startTextColorButtonClicked(self):
        set_qcolor(
            self.startTextExample,
            foreground=get_color(
                self, get_rgb(self.startTextExample, QPalette.Foreground)
            ),
        )

    def endTextColorButtonClicked(self):
        set_qcolor(
            self.endTextExample,
            foreground=get_color(
                self, get_rgb(self.endTextExample, QPalette.Foreground)
            ),
        )

    def startSoundPlayButtonClicked(self) -> None:
        if self.startSoundFileLabel.text():
            sound.play(
                self.trigger.package.audio_data.get(
                    self.startSoundFileLabel.text(), None
                ),
                self.startSoundVolumeSlider.value(),
            )

    def endSoundPlayButtonClicked(self) -> None:
        if self.endSoundFileLabel.text():
            sound.play(
                self.trigger.package.audio_data.get(
                    self.endSoundFileLabel.text(), None
                ),
                self.endSoundVolumeSlider.value(),
            )

    def startSoundFileButtonClicked(self) -> None:
        fd = QFileDialog(self)
        fd.setDirectory("./data/tts")
        f = fd.getOpenFileName(filter="*.mp3")
        name = self.trigger.package.add_audio(f[0])
        if f[0] and os.path.isfile(f[0]):
            self.trigger.start_action.sound.name = name
            self.startSoundFileLabel.setText(self.trigger.start_action.sound.name)

        fd.deleteLater()
        fd.setParent(None)

    def endSoundFileButtonClicked(self) -> None:
        fd = QFileDialog(self)
        fd.setDirectory("./data/tts")
        f = fd.getOpenFileName(filter="*.mp3")
        name = self.trigger.package.add_audio(f[0])
        if f[0] and os.path.isfile(f[0]):
            self.trigger.end_action.sound.name = name
            self.endSoundFileLabel.setText(self.trigger.end_action.sound.name)
        fd.deleteLater()
        fd.setParent(None)

    def startSoundVolumeSliderChanged(self, new_value: int) -> None:
        self.startSoundVolumeLabel.setText(f"{new_value}%")

    def endSoundVolumeSliderChanged(self, new_value: int) -> None:
        self.endSoundVolumeLabel.setText(f"{new_value}%")

    def _set_values(self, t: Trigger):
        # general
        self.triggerNameLineEdit.setText(t.name)
        self.triggerNameLineEdit.setValidator(QRegExpValidator(QRegExp(".+")))
        self.triggerDurationLineEdit.setText(t.duration)
        self.triggerDurationLineEdit.setValidator(
            QRegExpValidator(QRegExp("^(\\d\\d:)?(\\d\\d:)?\\d\\d$"))
        )

        # trigger
        if t.text:
            self.triggerTextRadio.setChecked(True)
            self.triggerTextLineEdit.setText(t.text)
        elif t.regex:
            self.triggerRegexRadio.setChecked(True)
            self.triggerRegexLineEdit.setText(t.regex)
        else:
            self.triggerTextRadio.setChecked(True)

        # start action
        self.startTimerTextLineEdit.setText(t.start_action.timer.text)
        self.startTimerEnabledCheckBox.setChecked(t.start_action.timer.enabled)
        self.startTimerDurationLineEdit.setText(t.start_action.timer.duration)
        self.startTimerIconSpinBox.setValue(t.start_action.timer.icon)
        set_qcolor(
            self.startTimerExample,
            QColor(*t.start_action.timer.text_color),
            QColor(*t.start_action.timer.bar_color),
        )
        self.startTimerIconSpinBoxChanged(self.startTimerIconSpinBox.value())

        self.startTextEnabledCheckBox.setChecked(t.start_action.text.enabled)
        self.startTextTextLineEdit.setText(t.start_action.text.text)
        self.startTextSizeSpinBox.setValue(t.start_action.text.text_size)
        set_qcolor(self.startTextExample, QColor(*t.start_action.text.color))

        self.startSoundEnabledCheckBox.setChecked(t.start_action.sound.enabled)
        self.startSoundFileLabel.setText(t.start_action.sound.name)
        self.startSoundVolumeSlider.setValue(t.start_action.sound.volume)

        # end action
        self.endTimerTextLineEdit.setText(t.end_action.timer.text)
        self.endTimerEnabledCheckBox.setChecked(t.end_action.timer.enabled)
        self.endTimerDurationLineEdit.setText(t.end_action.timer.duration)
        self.endTimerIconSpinBox.setValue(t.end_action.timer.icon)
        set_qcolor(
            self.endTimerExample,
            QColor(*t.end_action.timer.text_color),
            QColor(*t.end_action.timer.bar_color),
        )
        self.endTimerIconSpinBoxChanged(self.endTimerIconSpinBox.value())

        self.endTextEnabledCheckBox.setChecked(t.end_action.text.enabled)
        self.endTextTextLineEdit.setText(t.end_action.text.text)
        self.endTextSizeSpinBox.setValue(t.end_action.text.text_size)
        set_qcolor(self.endTextExample, QColor(*t.end_action.text.color))

        self.endSoundEnabledCheckBox.setChecked(t.end_action.sound.enabled)
        self.endSoundFileLabel.setText(t.end_action.sound.name)
        self.endSoundVolumeSlider.setValue(t.end_action.sound.volume)

    def get_trigger(self) -> Trigger:
        self.trigger.update(
            {
                "name": self.triggerNameLineEdit.text(),
                "duration": self.triggerDurationLineEdit.text(),
                "text": self.triggerTextLineEdit.text(),
                "regex": self.triggerRegexLineEdit.text(),
                "start_action": {
                    "timer": {
                        "enabled": self.startTimerEnabledCheckBox.isChecked(),
                        "persistent": self.startTimerPersistentCheckBox.isChecked(),
                        "text": self.startTimerTextLineEdit.text(),
                        "duration": self.startTimerDurationLineEdit.text(),
                        "icon": self.startTimerIconSpinBox.value(),
                        "bar_color": get_rgb(
                            self.startTimerExample, QPalette.Background
                        ),
                        "text_color": get_rgb(
                            self.startTimerExample, QPalette.Foreground
                        ),
                    },
                    "text": {
                        "enabled": self.startTextEnabledCheckBox.isChecked(),
                        "text": self.startTextTextLineEdit.text(),
                        "text_size": self.startTextSizeSpinBox.value(),
                        "color": get_rgb(self.startTextExample, QPalette.Foreground),
                    },
                    "sound": {
                        "enabled": self.startSoundEnabledCheckBox.isChecked(),
                        "volume": self.startSoundVolumeSlider.value(),
                    },
                },
                "end_action": {
                    "timer": {
                        "enabled": self.endTimerEnabledCheckBox.isChecked(),
                        "persistent": self.endTimerPersistentCheckBox.isChecked(),
                        "text": self.endTimerTextLineEdit.text(),
                        "duration": self.endTimerDurationLineEdit.text(),
                        "icon": self.endTimerIconSpinBox.value(),
                        "bar_color": get_rgb(self.endTimerExample, QPalette.Background),
                        "text_color": get_rgb(
                            self.endTimerExample, QPalette.Foreground
                        ),
                    },
                    "text": {
                        "enabled": self.endTextEnabledCheckBox.isChecked(),
                        "text": self.endTextTextLineEdit.text(),
                        "text_size": self.endTextSizeSpinBox.value(),
                        "color": get_rgb(self.endTextExample, QPalette.Foreground),
                    },
                    "sound": {
                        "enabled": self.endSoundEnabledCheckBox.isChecked(),
                        "volume": self.endSoundVolumeSlider.value(),
                    },
                },
            }
        )
        return self.trigger

    def accept(self) -> None:
        # validate that items can resolve before accepting
        if self.triggerRegexRadio.isChecked():
            try:
                create_regex_from(self.triggerRegexLineEdit.text())
                super().accept()
            except Exception as e:
                QMessageBox(
                    QMessageBox.Warning,
                    "Regex Error",
                    "Could not compile regex: {}".format(e),
                    parent=self,
                ).exec()
                return
        self.setParent(None)
        self.deleteLater()
        super().accept()
