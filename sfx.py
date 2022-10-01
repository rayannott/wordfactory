from utils import SFX_DIR
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
