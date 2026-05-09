## Formats
Name | Extension(s) | Sample(s) | URLs | Extractor(s) | Comment
---- | ------------ | --------- | ---- | ------------ | -------
Web Archive ARC | .arc | ? | http://fileformats.archiveteam.org/wiki/ARC_(Internet_Archive)<br>https://archive.org/web/researcher/ArcFileFormat.php | https://github.com/ikreymer/webarchiveplayer |
Astrotite | ? | ? | http://fileformats.archiveteam.org/wiki/Astrotite | http://download.cnet.com/Astrotite-200X-and-AstroA2P/3000-2250_4-75064900.html |
B6Z | .b6z | ? | http://fileformats.archiveteam.org/wiki/B6Z | https://web.archive.org/web/20250906002136/http://b6zip.com/ |
SSB DT | ? | SSB Wii U/3DS | ? | https://github.com/Sammi-Husky/Sm4sh-Tools |
SSBU Arc 5.0.0 > v > 1.0.0 | .arc | SSBU | ? | https://github.com/jam1garner/smash-arc/blob/master/src/lookups.rs#L385<br>https://github.com/jam1garner/smash-arc/blob/master/src/arc_file.rs#L31<br>https://github.com/ultimate-research/UltimateModManager/blob/master/source/arcReader.h#L172<br>https://github.com/ultimate-research/UltimateModManager/blob/master/include/arcStructs.h#L218<br>https://github.com/Ploaj/ArcCross/blob/master/ArcCross/ARC.cs | needs custom
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
PS3 Theme | .p3t | ? | ? | https://github.com/hoshsadiq/ps3theme-p3t-extract/blob/master/src/P3TExtractor/Extractor.php | detected
HMM Encrypted Snapshot | ? | ? | https://github.com/thesupersonic16/HedgeModManager | https://github.com/thesupersonic16/HedgeModManager/blob/rewrite/HedgeModManager/CLI/Commands/CliCommandDecrypt.cs<br>https://github.com/thesupersonic16/HedgeModManager/blob/rewrite/HedgeModManager/CryptoProvider.cs#L76 | detected, needs private key
UltraCompressor 2 | .uc2 | ? | ? | ? | detected
ELI 5750 | ? | ? | ? | ? | detected
Transformers: Devastation BXM | .bxm | Transformers: Devastation | ? | ? | detected, json like
Gateshark2NTR Plugin | .plg | https://gbatemp.net/threads/yokai-watch-3-ntr-plug-in.525593/<br>https://gbatemp.net/threads/release-gateshark2ntr.436504/post-9252959 | https://gbatemp.net/threads/release-gateshark2ntr.436504/ | ? | detected
Super Smash Bros. N64 ROM | .z64 | SSB | ? | [splat64](https://pypi.org/project/splat64/) + [SSB decomp YAML](https://github.com/VetriTheRetri/ssb-decomp-re) | detected, waiting for crunch64 to support vpk0
PlayStation Encrypted File | .pfenc | PlayStation PC ports -> uds/\<store\>/uds00.ucp/* | ? | ? | detected, encrypted, no block size
PlayStation 5 SELF | * | https://www.playstation.com/en-us/support/hardware/ps5/system-software/ | ? | https://github.com/zecoxao/PS5FTP/blob/master/source/ftps4.c | detected
PlayStation 4 SELF | * | https://www.playstation.com/en-us/support/hardware/ps4/system-software/ | ? | https://github.com/zecoxao/PS5FTP/blob/master/source/ftps4.c | detected
SecuROM | .exe | https://archive.org/download/The_Great_Escape_USA | ? | https://www.cdmediaworld.com/hardware/cdrom/cd_utils_8.shtml#UnSecuromNT | detected
Warp | .exe | ? | https://github.com/dgiagio/warp | ? |
Pixar USD Crate | .usd .usdc | RTX Remix | https://openusd.org/ | https://openusd.org/release/toolset.html#usdcat | detected
CD-i Realtime File | .rti .rtf .rtr | CD-i games | [interview](#cd-i-rtf-dev-interview)<br>http://www.icdia.co.uk/docs/cdi_may94_r2.pdf<br>http://www.icdia.co.uk/sw_disc/index.html | https://github.com/ogarvey/OGLibCD-iRS |
Camelot ARC | ` ` | Mario Golf Super Rush | https://x.com/_Ninji/status/1408533891976204292 | ? | detected
Camelot Obfuscated NRO | ` ` | Mario Golf Super Rush | https://x.com/_Ninji/status/1408533891976204292 | https://gist.github.com/Treeki/d467b4d29c934f37afada6c7c41f5624 |
Natsume LZS | .paz | Kamen Rider Battle: Ganbaride Card Battle Taisen | ? | https://github.com/Nisto/lzsd/blob/master/lzsd_nds.c | detected
Eutechnyx Compressed ARC | .arc | Street Racing Syndicate GameCube | ? | ? | detected

## Other Todos
- Unreal ZenLoader: ZenTool -> [retoc](https://github.com/trumank/retoc)
- lib/file.py:crc_hash SipHash
- lib/file.py:crc_hash City/Farm Hash
- lib/file.py:crc_hash Blake3
- RE Engine PAK: ree.unpacker -> Custom

### CD-i RTF dev interview:
> Q: what is a .rtr file?
>
> A:
> The .rtr format is different from the rtf, it's basically a "script" to build an rtf and will not be found on any disc (although the extension .rtr is sometimes used, but the format will be rtf).<br>
> Try the rfd tool in MAC/TOOLS/rfd on the CDISC4 disc, the rfd.doc file talks about rtr files (you can open the disc image with IsoBuster).<br>
> There's also something called rrb which seems to be something similar. Never used either of those, we built our disc images using "master" and rtf files using "green" or "master -g" (which takes the same syntax), and these use textual script files (description is somewhere on ICDIA as well).

> Q: does the rtf format have any standards at all for file separation or is it completely up to the developers and whatever scripts they made? And if so, is there maybe some common/standard script?
> 
> A:
> Rtf is basically just raw disc sectors so only the green book restrictions apply, and for custom data formats you’re on your own. I do not think there is a standard script, we at least didn’t use one. There might be be some studio-specific common formats, e.g. the “blocks” format used by SPC, but those are invariably very flexible (otherwise they could not be “common”).<br>
> Green book suggests placing different “subfiles” in different channels within a record (terminated by an EOR bit in the submode byte), using the TRG bit for triggers and using the coding byte to indicate the data type. However, except for real-time played audio the coding byte is completely ignored by the system so developers often played games with it or didn’t properly set it. The submode, on the other hand, specifies actual behavior so is normally set correctly.
