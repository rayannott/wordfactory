import PyInstaller.__main__

PyInstaller.__main__.run([
    'gui.py',
    '-i icon.ico'
    '--onefile',
    '--add-data=theme.json;.'
])