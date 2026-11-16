# Changes since 20251124

## Rename

- Wolf4SDL is now called Intenseflow, the executable is called `intenseflow`.
- The default directory of the configuration file and the saved games on
  Linux like systems is now `$HOME/.intenseflow` instead of `$HOME/.wolf4sdl`.
  Existing files have to be moved by hand.
- The manual page, the desktop file and the icon are part of the repository
  and are installed by CMake.

## Build system

- Converted the build system from a Makefile to CMake (#43). `version.h` and
  `config.default` are gone, the remaining feature flags are CMake options.
- Silenced `-Wcast-align` errors on macOS (#44).
- Fixed some build warnings.

## Game versions and data files

- One binary runs all versions of the game (#41). The version is detected at
  runtime from the data files, `--game` chooses one explicitly.
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
