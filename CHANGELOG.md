# 2026.11.21 (2026-11-21)

This is the first release under the new name *Intenseflow*. The last Wolf4SDL release is `20251124`.

## Rename

- Wolf4SDL is now called Intenseflow, the executable is called `intenseflow`.
- Added a new icon. It is installed as a 128x128 PNG and built into the Windows
  executable.
- The configuration file is called `intenseflow.cfg` for all games instead of
  `config.<extension>`. A file of Wolf4SDL can be renamed to use it.
- The configuration file and the saved games are stored in the directory given
  by `--configdir`. The default is the user data directory of SDL, for example
  `$HOME/.local/share/intenseflow`, or the directory of the executable on
  Windows if it is writable. Existing files of Wolf4SDL have to be moved by hand
  (e.g. from `~/.wolf4sdl`).
- The manual page, the desktop file and the icon are part of the repository
  and are installed by CMake.
- The files are sorted into `src`, `src/opl3`, `dist`, `doc` and `tools`.

## Build system

- Converted the build system from a Makefile to CMake (#43). `version.h` and
  `config.default` are gone, the remaining feature flags are CMake options.
- Silenced `-Wcast-align` errors on macOS (#44).
- Fixed some build warnings.

## Game versions and data files

- One binary runs all versions of the game (#41). The version is detected at
  runtime from the data files, `--game` chooses one explicitly.
- The `--mission` parameter implies `--game sod`.
- A suffix of the executable name like `intenseflow-sod` selects the game as
  well.
- The data files are searched in a list of directories that is built at
  startup (#45): the current directory, the XDG data directories and, on
  Windows, the directory of the executable.

## Audio

- Updated the OPL3 emulator to Nuked-OPL3-fast v1.8-fast.3.

## Fixes

- Fixed the broken HUD at the original resolution (#40).
- Fixed the placement of static objects with the info plane codes 70 to 72.
- Saved games are named after the level (`E1M1` or `MAP01`) if the name was
  left empty or already is a level name.

## Diagnostics

- Added the `--version` option.
- The startup log shows the config file, the data directory and the game
  layout.
- Improved the error message for missing data files, it lists the searched
  directories.
- `Quit()` prints errors to stderr and shows a message box if stdout is not
  a terminal. Removed the unused DOS text screen code.
