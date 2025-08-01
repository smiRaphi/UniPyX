### UniPyX
#### Universal Python eXtractor
---
Usage: `python unipyx.py <input> [<output dir>]`

### ps3key.py
You need to provide the disc keys to extract PS3 ISOs, you can do so by making a folder called `ps3keys` in `bin/` containing `<game name>.dkey` files and afterwards running `ps3key.py` from the `bin/` folder.
### wiiudk.py
You need to provide disc keys to extract Wii U WUD/WUX files, you can do so by making a `keys.txt` file in `bin/` with one key per line formatted like this: `<key> # <game name>` and afterwards running `wiiudk.py` from the `bin/` folder.

## Included tools
* xbp.bms by [h3x3r](https://reshax.com/profile/183-h3x3r/) taken from https://reshax.com/topic/18058-ripping-sounds-from-fuzion-frenzy-xbox/
* self compiled [hac2l](https://github.com/Atmosphere-NX/hac2l)
* [ndssndext](https://gbatemp.net/download/nds-sound-extractor.28818/) because of httpcore weirdness with [catbox.moe](https://catbox.moe/)
* ps3key.py & wiiudk.py for managing Wii U & PS3 disc keys

## Notes
* Extracting Wii U WUD/WUX files requires java to be installed.
