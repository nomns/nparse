from PyQt5.QtWidgets import QDialog, QColorDialog, QFileDialog
from PyQt5 import uic
from PyQt5.QtGui import QColor

from gtts import gTTS
import pygame
import os

from parsers.spells import get_spell_icon
from helpers import resource_path


class TriggerEditor(QDialog):

    def __init__(self, trigger_name, trigger_data):
        super().__init__()

        uic.loadUi(resource_path('data/ui/triggereditor.ui'), self)
        self._value = {
            'name': trigger_name,
            'data': trigger_data
        }

        self.timerIconSpinBox.valueChanged.connect(self._load_timer_icon)
        self.timerBarColorButton.clicked.connect(self._choose_timer_bar_color)
        self.timerTextColorButton.clicked.connect(self._choose_timer_text_color)
        self.nameLineEdit.textChanged.connect(self._name_changed)
        self.textTextLineEdit.textChanged.connect(self._text_text_changed)
        self.textSizeSpinBox.valueChanged.connect(self._text_size_changed)
        self.textColorButton.clicked.connect(self._choose_text_text_color)
        self.soundFileButton.clicked.connect(self._choose_sound_file)
        self.soundPlayButton.clicked.connect(self._play_sound_file)
        self.ttsCreateButton.clicked.connect(self._create_tts_file)
        self.ttsPlayButton.clicked.connect(self._play_tts_file)

        self._set_values()
    
    def _create_tts_file(self, _):
        # ensure data/tts directory exists, otherwise create
        if not os.path.exists('data/tts'):
            os.makedirs('data/tts')

        try:
            text = self.ttsTextLineEdit.text()
            text_save_location = 'data/tts/{}.mp3'.format(text)
            if text:
                gTTS(text).save(text_save_location)
                self.ttsFileLabel.setText(text_save_location)
        except:
            pass

    def _play_tts_file(self, _):
        try:
            pygame.mixer.music.load(self.ttsFileLabel.text())
            pygame.mixer.music.play()
        except:
            pass

    def _play_sound_file(self, _):
        try:
            pygame.mixer.music.load(self.soundFileLabel.text())
            pygame.mixer.music.play()
        except:
            pass
    
    def _choose_sound_file(self, _):
        fd = QFileDialog(self)
        f = fd.getOpenFileName(filter='*.mp3')
        if f[0]:
            self.soundFileLabel.setText(f[0])
    
    def _load_timer_icon(self, icon_index):
        try:
            self.timerIconLayout.itemAt(0).widget().setParent(None)
        except:
            pass
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
        cd = QColorDialog(parent=self)
        color = cd.getColor()
        w = self.textExample
        p = w.palette()
        p.setColor(w.foregroundRole(), color)
        w.setPalette(p)

    def _choose_timer_bar_color(self, _):
        cd = QColorDialog(parent=self)
        color = cd.getColor()
        w = self.timerExample
        p = w.palette()
        p.setColor(w.backgroundRole(), color)
        w.setPalette(p)

    def _choose_timer_text_color(self, _):
        cd = QColorDialog(parent=self)
        color = cd.getColor()
        w = self.timerExample
        p = w.palette()
        p.setColor(w.foregroundRole(), color)
        w.setPalette(p)

    def _set_values(self):
        v = self._value
        d = v['data']

        # general
        self.nameLineEdit.setText(v['name'])
        self.enabledCheckBox.setChecked(d['__enabled__'])

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
                w = self.timerExample
                p = w.palette()
                bc = a['timer']['bar_color']
                tc = a['timer']['text_color']
                p.setColor(w.backgroundRole(), QColor.fromRgb(*bc))
                p.setColor(w.foregroundRole(), QColor.fromRgb(*tc))
                w.setPalette(p)
            if a.get('text', None):
                self.textCheckBox.setChecked(True)
                self.textTextLineEdit.setText(a['text']['text'])
                self.textSizeSpinBox.setValue(a['text']['text_size'])
                w = self.textExample
                p = w.palette()
                tc = a['text']['color']
                p.setColor(w.foregroundRole(), QColor.fromRgb(*tc))
                w.setPalette(p)
            if a.get('sound', None):
                self.soundCheckBox.setChecked(True)
                self.soundFileLabel.setText(a['sound'])
            if a.get('tts', None):
                self.ttsCheckBox.setChecked(True)
                self.ttsTextLineEdit.setText(a['tts'])
        except:
            pass

    def value(self):
        d = {}
        d['name'] = self.nameLineEdit.text()

        data = {}
        data['__enabled__'] = self.enabledCheckBox.isChecked()

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
            bc = w.palette().color(w.backgroundRole()).getRgb()
            tc = w.palette().color(w.foregroundRole()).getRgb()
            a['timer']['bar_color'] = bc[0:-1]
            a['timer']['text_color'] = tc[0:-1]
        if self.textCheckBox.isChecked():
            a['text'] = {}
            a['text']['text'] = self.textTextLineEdit.text()
            a['text']['text_size'] = self.textSizeSpinBox.value()
            w = self.textExample
            tc = w.palette().color(w.foregroundRole()).getRgb()
            a['text']['color'] = tc[0:-1]
        if self.soundCheckBox.isChecked():
            a['sound'] = self.soundFileLabel.text()
        if self.ttsCheckBox.isChecked():
            a['tts'] = self.ttsTextLineEdit.text()

        data['trigger'] = t
        data['action'] = a
        d['data'] = data
        return d
    