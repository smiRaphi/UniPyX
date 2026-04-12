## Formats
Name | Extension(s) | Sample(s) | URLs | Extractor(s) | Comment
---- | ------------ | --------- | ---- | ------------ | -------
Web Archive ARC | .arc | ? | http://fileformats.archiveteam.org/wiki/ARC_(Internet_Archive)<br>https://archive.org/web/researcher/ArcFileFormat.php | https://github.com/ikreymer/webarchiveplayer |
Astrotite | ? | ? | http://fileformats.archiveteam.org/wiki/Astrotite | http://download.cnet.com/Astrotite-200X-and-AstroA2P/3000-2250_4-75064900.html |
B6Z | .b6z | ? | http://fileformats.archiveteam.org/wiki/B6Z | https://web.archive.org/web/20250906002136/http://b6zip.com/ |
SSB DT | ? | SSB Wii U/3DS | ? | https://github.com/Sammi-Husky/Sm4sh-Tools |
SSBU Arc v > 1.0.0 | .arc | SSBU | ? | https://github.com/jam1garner/smash-arc/blob/master/src/lookups.rs#L385<br>https://github.com/jam1garner/smash-arc/blob/master/src/arc_file.rs#L31<br>https://github.com/ultimate-research/UltimateModManager/blob/master/source/arcReader.h#L172<br>https://github.com/ultimate-research/UltimateModManager/blob/master/include/arcStructs.h#L218<br>https://github.com/Ploaj/ArcCross/blob/master/ArcCross/ARC.cs | needs custom
Playdate Container | ? | ? | ? | https://github.com/rarenight/pdx-decrypt/blob/main/pdx-decrypt.py | detected
Denuvo | .exe | https://store.steampowered.com/curator/26095454-Denuvo-Watch/ | ? | hypervisor? | detected
Crinkler | .exe | https://github.com/InkboxSoftware/smallEXE | https://github.com/runestubbe/Crinkler | https://github.com/runestubbe/Crinkler/blob/master/source/Crinkler/Crinkler.cpp#L485 | detected
d0lLZ 3 | .dol | ? | https://wiibrew.org/wiki/Dollz | https://wiibrew.org/w/images/e/ef/Dollz3.zip | detected
VMProtect | .exe | ? | ? | ? | detected
Atomik Cruncher | ? | ? | ? | http://aminet.net/package/util/pack/xfdmaster | detected
HAL YAML | ? | Kirby/HAL games | ? | https://github.com/firubii/KirbyLib/blob/main/KirbyLib/Yaml.cs | detected
Encrypted Rclone Config | .conf | ARMGDDN | https://github.com/rclone/rclone/blob/847734d421d219f1b12b144fcb0d08a6556e1485/fs/config/obscure/obscure.go#L19<br>https://github.com/rclone/rclone/blob/847734d421d219f1b12b144fcb0d08a6556e1485/fs/config/crypt.go#L74 | ? | detected
The Binding of Isaac Resource | ? | TBOI(Re) | ? | ? | detected
Atari Masterpieces VPXH | ? | Atari Masterpieces | ? | ? | detected
Metropolis Software ZAP | .zap | ? | ? | ? | detected
Specnaz UFF/BFS | ? | ? | ? | ? | detected
Metroid Prime 4 Save | ? | MP4 | ? | ? | detected
Import Tuner Challenge TOC+DAT | .toc+.dat | Import Tuner Challenge Xbox 360 | ? | ? | detected, custom, need to figure out UCL diviation
PS3 Theme | .p3t | ? | ? | https://github.com/hoshsadiq/ps3theme-p3t-extract/blob/master/src/P3TExtractor/Extractor.php | detected
HMM Encrypted Snapshot | ? | ? | https://github.com/thesupersonic16/HedgeModManager | https://github.com/thesupersonic16/HedgeModManager/blob/rewrite/HedgeModManager/CLI/Commands/CliCommandDecrypt.cs<br>https://github.com/thesupersonic16/HedgeModManager/blob/rewrite/HedgeModManager/CryptoProvider.cs#L76 | detected, needs private key
Batman AC Resource | .exe | Batman AC | https://wiki.osdev.org/NE | ? | detected
UltraCompressor 2 | .uc2 | ? | ? | ? | detected
ELI 5750 | ? | ? | ? | ? | detected
Transformers: Devastation BXM | .bxm | Transformers: Devastation | ? | ? | detected, json like
Gateshark2NTR Plugin | .plg | https://gbatemp.net/threads/yokai-watch-3-ntr-plug-in.525593/<br>https://gbatemp.net/threads/release-gateshark2ntr.436504/post-9252959 | https://gbatemp.net/threads/release-gateshark2ntr.436504/ | ? | detected
Super Smash Bros. N64 ROM | .z64 | SSB | ? | [splat64](https://pypi.org/project/splat64/) + [SSB decomp YAML](https://github.com/VetriTheRetri/ssb-decomp-re) | detected, waiting for crunch64 to support vpk0
PlayStation Encrypted File | .pfenc | PlayStation PC ports -> uds/\<store\>/uds00.ucp/* | ? | ? | detected, encrypted, no block size
PlayStation 5 SELF | * | https://www.playstation.com/en-us/support/hardware/ps5/system-software/ | ? | https://github.com/zecoxao/PS5FTP/blob/master/source/ftps4.c | detected
PlayStation 4 SELF | * | https://www.playstation.com/en-us/support/hardware/ps4/system-software/ | ? | https://github.com/zecoxao/PS5FTP/blob/master/source/ftps4.c | detected

## Other Todos
- Unreal ZenLoader: ZenTool -> [retoc](https://github.com/trumank/retoc)
- F-Zero G/AX LZ: gxpand -> [gfz-cli](https://github.com/RaphaelTetreault/gfz-cli)
