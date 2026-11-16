# Intenseflow

Intenseflow is an open-source source port of id Software's classic first-person shooters Wolfenstein 3D and Spear of Destiny to the cross-platform multimedia library [Simple DirectMedia Layer](https://www.libsdl.org) (SDL2). It is meant to keep the original feel while taking advantage of some improvements mentioned in the list below.

Intenseflow is the successor of Wolf4SDL, which was written by Moritz "Ripper" Kroll. It was renamed because the code base has changed a lot since the last Wolf4SDL release. The name is an anagram of "Wolfenstein".

The game data files are **not** part of Intenseflow. You need your own copy of Wolfenstein 3D and/or Spear of Destiny, the shareware versions work as well.

## Main features

- **Cross-platform:** Linux, BSD variants, macOS and Windows (MinGW). The continuous integration builds on Linux, macOS and Windows (MSYS2). Only little endian platforms like x86 and ARM are supported.
- **One binary for all game versions:** The version of the game is detected at runtime from the data files that are found. There is no need to build a separate binary for each version.
- **AdLib sounds and music:** This port includes the Nuked OPL3 emulator (Nuked-OPL3-fast), so you can hear the AdLib sounds and music without any AdLib-compatible sound card in near to perfect quality.
- **Multichannel digitized sounds:** Digitized sounds play on 8 channels, so in a fire fight you will always hear when a guard opens the door behind you.
- **Higher screen resolutions:** Aside from the original 320x200 resolution, any multiple of 320x200 is supported, the default being 640x400. Other resolutions of at least 320x200 can be forced, which may result in graphic errors. Intenseflow does *not* apply any bilinear or similar filtering, so the graphics are not blurred but pixelated just as we love it.
- **Fully playable with only a game controller:** Intenseflow can be played completely without a keyboard. At least two buttons are required (shoot/YES and open door/NO), but five or more are recommended (run, strafe, ESC).
- **Two additional view sizes:** One view size uses the full width of the screen and shows the status bar, like in Mac-enstein, and one view size fills the whole screen (press TAB to see the status bar).
- **(Nearly) unlimited sound and song lengths:** Mod developers are not restricted to 64kB for digitized sounds and IMF songs, so longer songs and digitized sounds with better quality are possible.
- **Resuming ingame music:** When you come back to the game from the menu or load a save game, the music is resumed where it was suspended.
- **Freely movable pushwalls:** Moving pushwalls can be viewed from all sides, allowing mod developers to place them with fewer restrictions. The player can also follow the pushwall directly instead of waiting until it has left a whole tile.
- **Optional integrated features for mod developers:** Shading, directional 3D sprites, floor and ceiling textures, high resolution textures and sprites, parallax sky, cloud sky and outside atmosphere (star sky, rain, snow). They are disabled by default and are enabled with CMake options, see [Building](#building).

## Supported game versions

The files of a game are identified by their extension:

| Extension | Game |
| --- | --- |
| `wl6` | Wolfenstein 3D, full version (v1.4 GT/ID/Activision, v1.4 Apogee, v1.1 Apogee) |
| `wl3` | Wolfenstein 3D, three episode Apogee release |
| `wl1` | Wolfenstein 3D, shareware version (v1.4) |
| `sod` | Spear of Destiny, full version |
| `sd1`, `sd2`, `sd3` | Spear of Destiny mission disks |
| `sdm` | Spear of Destiny, demo version |

## How to play

Copy the original data files (e.g. `*.WL6`) into one of the following directories, they are searched in this order:

1. the current directory
2. `$XDG_DATA_HOME/games/wolf3d` (default: `$HOME/.local/share/games/wolf3d`)
3. the directories of `$XDG_DATA_DIRS` with `/games/wolf3d` appended (default: `/usr/local/share:/usr/share`)

On Windows, the directory of the executable is searched instead of 2. and 3.

A game is only used if its data files are complete. If several games are found, the first one in this order is started: `wl6`, `sod`, `wl3`, `wl1`, `sdm`. Use the `--game` option to choose another one. The same happens if the name of the executable ends with a dash and the name of a game, for example when it is started through a symbolic link called `intenseflow-sod`.

On Windows, the SDL2 and SDL2_mixer DLLs must be available next to the executable.

The configuration file and the saved games are stored in `$HOME/.intenseflow` on Linux like systems and in the current directory on Windows. Their names carry the extension of the game that is played. The location can be changed with the `--configdir` option.

## Usage

Intenseflow supports the following command line options:

```
 --help                 This help page
 --version              Print version information and exit
 --tedlevel <level>     Starts the game in the given level
 --baby                 Sets the difficulty to baby for tedlevel
 --easy                 Sets the difficulty to easy for tedlevel
 --normal               Sets the difficulty to normal for tedlevel
 --hard                 Sets the difficulty to hard for tedlevel
 --nowait               Skips intro screens
 --demotest             Skips right into the demo loop
 --fullscreen           Starts the game in fullscreen mode
 --nograbmouse          Does not grab the mouse in windowed mode
 --res <width> <height> Sets the screen resolution
                        (must be multiple of 320x200)
 --resf <w> <h>         Sets any screen resolution >= 320x200
                        (which may result in graphic errors)
 --joystick <index>     Use the index-th joystick if available
                        (-1 to disable joystick, default: 0)
 --joystickhat <index>  Enables movement with the given coolie hat
 --samplerate <rate>    Sets the sound sample rate (given in Hz,
                        default: 44100)
 --audiobuffer <size>   Sets the size of the audio buffer (-> sound latency)
                        (given in bytes, default: 2048 / (44100 / samplerate))
 --ignorenumchunks      Ignores the number of chunks in VGAHEAD.*
                        (may be useful for some broken mods)
 --configdir <dir>      Directory where config file and save games are stored
                        (Windows default: current directory,
                        others: $HOME/.intenseflow)
 --game <name>          Data files to use: wl6, sod, wl3, wl1 or sdm
                        (default: the first one found, in that order)
 --mission <mission>    Mission number to play (0-3)
                        (default: 0 -> .sod, 1-3 -> .sd*,
                        Spear of Destiny only)
```

A manual page is installed as `intenseflow(6)`.

## Building

Intenseflow is built with CMake (version 3.13 or newer). It needs a C and a C++ compiler, pkg-config and the development files of SDL2 and SDL2_mixer.

```sh
cmake -B build
cmake --build build
```

The result is the executable `build/intenseflow`. Use `-DBINARY=<name>` to choose another name for it. `cmake --install build --strip` installs the executable, the manual page, the desktop file and the icon.

The following features are switched on or off with CMake options, for example `cmake -B build -DUSE_SHADING=ON`:

| Option | Default | Feature |
| --- | --- | --- |
| `DEBUGKEYS` | ON | The debug keys, enabled by `--goobers` or `--debugmode` and accessed with the TAB key |
| `ARTSEXTERN` | ON | Take the help and end texts from the graphics file |
| `DEMOSEXTERN` | ON | Take the demos from the graphics file |
| `PLAYDEMOLIKEORIGINAL` | ON | Do not apply bug fixes while playing or recording demos, so the demos stay in sync |
| `USE_FEATUREFLAGS` | OFF | Level feature flags, see the end of `wl_def.h` |
| `USE_SHADING` | OFF | Shading |
| `USE_DIR3DSPR` | OFF | Directional 3D sprites |
| `USE_FLOORCEILINGTEX` | OFF | Floor and ceiling textures in the third map plane |
| `USE_HIRES` | OFF | High resolution textures and sprites (128x128) |
| `USE_PARALLAX` | empty | Parallax sky, set to the number of textures per sky, for example 16 |
| `USE_CLOUDSKY`, `USE_STARSKY`, `USE_RAIN`, `USE_SNOW` | OFF | Cloud sky, star sky, rain and snow |
| `FIXRAINSNOWLEAKS` | OFF | Fix leaking ceilings, only needed for maps with rain or snow and ceilings |

## Troubleshooting

- If your frame rate is low, consider using the original screen resolution (`--res 320 200`) or lowering the sound quality (`--samplerate 22050`).
- If the game does not find your data files, the error message lists all directories that were searched. The first lines of the console output show the data directory and the game version that were detected.

## History

[CHANGELOG.md](CHANGELOG.md) lists the changes since the last tag. [Changes.txt](Changes.txt) holds the history of Wolf4SDL up to its last release.

## Credits

- Special thanks to id Software! Without the source code we would still have to pelt Wolfenstein 3D with hex editors and disassemblers ;D
- Moritz "Ripper" Kroll and Chaos-Software for Wolf4SDL, which this port is based on
- Nuke.YKT for Nuked OPL3 and Tony Gies for Nuked-OPL3-fast
- Many thanks to "Der Tron" for hosting the svn repository, making Wolf4SDL FreeBSD compatible, testing, bugfixing and cleaning up the code!
- Thanks to Chris Chokan for his improvements on Wolf4GW (base of Wolf4SDL)
- Thanks to Pickle for the GP2X support and help on 320x240 support
- Thanks to fackue for the Dreamcast support
- Thanks to Chris Ballinger for the Mac OS X support
- Thanks to Xilinx, Inc. for providing a list of maximum-length LFSR counters used for higher resolutions of fizzle fade

## Licenses

Intenseflow is maintained by Fabian Greffrath.

- Copyright (C) 1992 id Software, Inc.
- Copyright (C) 2007-2011 Moritz "Ripper" Kroll
- Copyright (C) 2010-2026 Fabian Greffrath

The source code of Wolfenstein 3D and of Intenseflow is available, at your choice, under [license-id.txt](license-id.txt) or [license-gpl.txt](license-gpl.txt).

The OPL3 emulator (`opl3.c`, `opl3.h`, `wf_rom.h`) is licensed under the GNU Lesser General Public License, version 2.1 or later, see the headers of the files.
