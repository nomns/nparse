from PyQt5.QtWidgets import (QDialog, QFileDialog,
                             QMessageBox)
from PyQt5 import uic
from PyQt5.QtGui import QColor, QPalette

from utils import (get_spell_icon, resource_path, sound,
                   get_rgb, set_qcolor, create_regex_from,
                   get_color)


class TriggerEditor(QDialog):

    def __init__(self, parent=None, trigger_name='', trigger_data: dict = dict):
        super().__init__(parent)

        uic.loadUi(resource_path('data/ui/triggereditor.ui'), self)
        self._data = trigger_data
        self._name = trigger_name

        self.timerIconSpinBox.valueChanged.connect(self._load_timer_icon)
        self.timerBarColorButton.clicked.connect(self._choose_timer_bar_color)
        self.timerTextColorButton.clicked.connect(self._choose_timer_text_color)
        self.nameLineEdit.textChanged.connect(self._name_changed)
        self.textTextLineEdit.textChanged.connect(self._text_text_changed)
        self.textSizeSpinBox.valueChanged.connect(self._text_size_changed)
        self.textColorButton.clicked.connect(self._choose_text_text_color)
        self.soundFileButton.clicked.connect(self._choose_sound_file)
        self.soundPlayButton.clicked.connect(self._play_sound_file)

        self._set_values()

    def _play_sound_file(self, _):
        sound.play(self.soundFileLabel.text())

    def _choose_sound_file(self, _):
        fd = QFileDialog(self)
        fd.setDirectory('./data/tts')
        f = fd.getOpenFileName(filter='*.mp3')
        if f[0]:
            self.soundFileLabel.setText(f[0])
        fd.setParent(None)

    def _load_timer_icon(self, icon_index):
        self.timerIconLayout.removeItem(
            self.timerIconLayout.itemAt(0)
        )
        self.timerIconLayout.addWidget(get_spell_icon(icon_index))

    def _text_size_changed(self, _):
        f = self.textExample.font()
        f.setPointSize(self.textSizeSpinBox.value())
        self.textExample.setFont(f)

    def _text_text_changed(self, _):
        self.textExample.setText(self.textTextLineEdit.text())

    def _name_changed(self, _):
        self.timerExample.setText(self.nameLineEdit.text())

    def _choose_text_text_color(self, _):
        set_qcolor(self.textExample, foreground=get_color(
            self, get_rgb(self.textExample, QPalette.Foreground)
        ))

    def _choose_timer_bar_color(self, _):
        set_qcolor(self.timerExample, background=get_color(
            self, get_rgb(self.timerExample, QPalette.Background)
        ))

    def _choose_timer_text_color(self, _):
        set_qcolor(self.timerExample, foreground=get_color(
            self, get_rgb(self.timerExample, QPalette.Foreground)
        ))

    def _set_values(self):
        d = self._data

        # general
        self.nameLineEdit.setText(self._name)
        self.enabledCheckBox.setChecked(d['enabled'])

        # trigger
        try:
            t = d['trigger']
            if 'text' in t:
                self.triggerTextRadio.setChecked(True)
                self.triggerTextLineEdit.setText(t['text'])
            elif 'regex' in t:
                self.triggerRegexRadio.setChecked(True)
                self.triggerRegexLineEdit.setText(t['regex'])
        except:
            self.triggerTextRadio.setChecked(True)

        # action
        try:
            a = d['action']
            if a.get('timer', None):
                self.timerCheckBox.setChecked(True)
                self.timerTimeLineEdit.setText(a['timer']['time'])
                self.timerIconSpinBox.setValue(a['timer']['icon'])
                # self._load_timer_icon(a['timer']['icon'])
                w = self.timerExample
                set_qcolor(w, QColor(*a['timer']['text_color']), QColor(*a['timer']['bar_color']))
            else:
                self._load_timer_icon(self.timerIconSpinBox.value())
            if a.get('text', None):
                self.textCheckBox.setChecked(True)
                self.textTextLineEdit.setText(a['text']['text'])
                self.textSizeSpinBox.setValue(a['text']['text_size'])
                set_qcolor(self.textExample, QColor(*a['text']['color']))
            if a.get('sound', None):
                self.soundCheckBox.setChecked(True)
                self.soundFileLabel.setText(a['sound'])
        except:
            pass

    def value(self):
        d = dict()
        d['name'] = self.nameLineEdit.text()

        data = dict()
        data['enabled'] = self.enabledCheckBox.isChecked()

        t = {}
        if self.triggerTextRadio.isChecked():
            t['text'] = self.triggerTextLineEdit.text()
        elif self.triggerRegexRadio.isChecked():
            t['regex'] = self.triggerRegexLineEdit.text()

        a = {}
        if self.timerCheckBox.isChecked():
            a['timer'] = {}
            a['timer']['time'] = self.timerTimeLineEdit.text()
            a['timer']['icon'] = self.timerIconSpinBox.value()
            w = self.timerExample
            a['timer']['bar_color'] = get_rgb(w, w.backgroundRole())
            a['timer']['text_color'] = get_rgb(w, w.foregroundRole())
        if self.textCheckBox.isChecked():
            a['text'] = {}
            a['text']['text'] = self.textTextLineEdit.text()
            a['text']['text_size'] = self.textSizeSpinBox.value()
            w = self.textExample
            a['text']['color'] = get_rgb(w, w.foregroundRole())

        if self.soundCheckBox.isChecked():
            a['sound'] = self.soundFileLabel.text()

        data['trigger'] = t
        data['action'] = a
        d['data'] = data
        return d

    def accept(self) -> None:
        if self.triggerRegexRadio.isChecked():
            try:
                create_regex_from(self.triggerRegexLineEdit.text())
                super().accept()
            except Exception as e:
                QMessageBox(text='Could not compile regex: {}'.format(e)).exec()
                return
        super().accept()
