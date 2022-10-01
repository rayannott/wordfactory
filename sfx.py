from utils import MUSIC_DEFAULT_VOLUME, SFX_DIR
from pygame import mixer
import os
from random import random

mixer.init()
sfx_files = os.listdir(SFX_DIR)

sfx = {file[:-4]: mixer.Sound(os.path.join(SFX_DIR, file)) for file in sfx_files}

def play_sfx(name):
    if random() < 0.99:
        sfx[name].play()
    else:
        sfx['fart'].play()

def set_sfx_volume(vol):
    global sfx
    for s_effect in sfx.values():
        s_effect.set_volume(vol)
    
def play_bg_music():
    mixer.music.load(SFX_DIR + '/bg_music.mp3')
    bg_music_set_vol(MUSIC_DEFAULT_VOLUME)
    mixer.music.play(-1)

def bg_music_set_vol(vol):
    mixer.music.set_volume(vol)

def bg_music_play(play: bool):
    if play:
        mixer.music.unpause()
    else:
        mixer.music.pause()
