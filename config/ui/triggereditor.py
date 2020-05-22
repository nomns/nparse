from PyQt5.QtWidgets import QDialog, QFileDialog, QMessageBox
from PyQt5 import uic
from PyQt5.QtGui import QColor, QPalette, QRegExpValidator
from PyQt5.QtCore import QRegExp, QFile, QByteArray

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
    def __init__(self, parent=None, trigger: Trigger = None):
        super().__init__(parent)
        uic.loadUi(resource_path("data/ui/triggereditor.ui"), self)
        self._set_values(trigger)

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

    def startTimerBarColorChoose(self) -> None:
        set_qcolor(
            self.startTimerExample,
            background=get_color(
                self, get_rgb(self.startTimerExample, QPalette.Background)
            ),
        )

    def endTimerBarColorChoose(self) -> None:
        set_qcolor(
            self.endTimerExample,
            background=get_color(
                self, get_rgb(self.endTimerExample, QPalette.Background)
            ),
        )

    def startTimerTextColorChoose(self) -> None:
        set_qcolor(
            self.startTimerExample,
            foreground=get_color(
                self, get_rgb(self.startTimerExample, QPalette.Foreground)
            ),
        )

    def endTimerTextColorChoose(self) -> None:
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
        sound.play(self.startSoundFileLabel.text())

    def endSoundPlayButtonClicked(self) -> None:
        sound.play(self.endSoundFileLabel.text())

    def startSoundFileButtonClicked(self) -> None:
        fd = QFileDialog(self)
        fd.setDirectory("./data/tts")
        f = fd.getOpenFileName(filter="*.mp3")
        if f[0]:
            self.startSoundFileLabel.setText(f[0])
        fd.setParent(None)

    def endSoundFileButtonClicked(self) -> None:
        fd = QFileDialog(self)
        fd.setDirectory("./data/tts")
        f = fd.getOpenFileName(filter="*.mp3")
        if f[0]:
            self.endSoundFileLabel.setText(f[0])
        fd.setParent(None)

    def startSoundVolumeSliderChanged(self, new_value: int) -> None:
        self.startSoundVolumeLabel.setText(f"{new_value:.2%}")

    def endSoundVolumeSliderChanged(self, new_value: int) -> None:
        self.endSoundVolumeLabel.setText(f"{new_value:.2%}")

    def _set_values(self, t: Trigger):
        # set values and validators

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
        set_qcolor(self.startTextExample, QColor(t.start_action.text.color))

        self.startSoundEnabledCheckBox.setChecked(t.start_action.sound.enabled)
        self.startSoundFileLabel.setText(str(t.start_action.sound.data))

        # end action
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
        set_qcolor(self.endTextExample, QColor(t.end_action.text.color))

        self.endSoundEnabledCheckBox.setChecked(t.end_action.sound.enabled)
        self.endSoundFileLabel.setText(str(t.end_action.sound.data))

    def trigger(self) -> Trigger:
        # create Trigger object from settings and return it
        t: Trigger = Trigger()
        t.update(
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
                        "data": QFile(self.startSoundFileLabel.text()).readAll(),
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
                        "data": QFile(self.endSoundFileLabel.text()).readAll(),
                    },
                },
            }
        )
        return t

    def accept(self) -> None:
        # Validate
        if self.triggerRegexRadio.isChecked():
            try:
                create_regex_from(self.triggerRegexLineEdit.text())
                super().accept()
            except Exception as e:
                QMessageBox(text="Could not compile regex: {}".format(e)).exec()
                return
        super().accept()
