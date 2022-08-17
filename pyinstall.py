import PyInstaller.__main__

PyInstaller.__main__.run([
    'gui.py',
    '--onefile',
    '--add-data=theme.json;.'
])