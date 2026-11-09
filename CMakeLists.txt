cmake_minimum_required(VERSION 3.13)
project(wolf4sdl C CXX)

# Name of the executable, like BINARY in the Makefile.
set(BINARY wolf3d CACHE STRING "Name of the executable")

# The Makefile used -O2 -g unless a configuration said otherwise.
if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    add_compile_options(-O2 -g)
endif()

# Directory with the game data, e.g. /usr/share/games/wolf3d/ for a distribution package.
set(DATADIR "" CACHE STRING "Directory with the game data, empty for the current directory")

# Features that were switched in version.h.
option(DEBUGKEYS "Enable the Tab debug keys" ON)
option(ARTSEXTERN "Take the help and end texts from the graphics file" ON)
option(DEMOSEXTERN "Take the demos from the graphics file" ON)
option(PLAYDEMOLIKEORIGINAL "Do not apply bug fixes while playing or recording demos" ON)

option(USE_FEATUREFLAGS "Enable the level feature flags (see the bottom of wl_def.h)" OFF)
option(USE_SHADING "Enable shading support (wl_shade.cpp)" OFF)
option(USE_DIR3DSPR "Enable directional 3D sprites (wl_dir3dspr.cpp)" OFF)
option(USE_FLOORCEILINGTEX "Enable floor and ceiling textures in the third map plane (wl_floorceiling.cpp)" OFF)
option(USE_HIRES "Enable high resolution textures and sprites (128x128)" OFF)
option(USE_CLOUDSKY "Enable cloud sky support (wl_cloudsky.cpp)" OFF)
option(USE_STARSKY "Enable star sky support (wl_atmos.cpp)" OFF)
option(USE_RAIN "Enable rain support (wl_atmos.cpp)" OFF)
option(USE_SNOW "Enable snow support (wl_atmos.cpp)" OFF)
option(FIXRAINSNOWLEAKS "Fix leaking ceilings, only needed for maps with rain or snow and ceilings" OFF)
set(USE_PARALLAX "" CACHE STRING "Enable the parallax sky with this many textures per sky, for example 16")

find_package(PkgConfig REQUIRED)
pkg_check_modules(SDL2 REQUIRED IMPORTED_TARGET sdl2 SDL2_mixer)

set(SRCS
    opl3.c
    id_ca.cpp
    id_in.cpp
    id_pm.cpp
    id_sd.cpp
    id_us_1.cpp
    id_vh.cpp
    id_vl.cpp
    layouts_gen.cpp
    signon.cpp
    wl_act1.cpp
    wl_act2.cpp
    wl_agent.cpp
    wl_debug.cpp
    wl_draw.cpp
    wl_game.cpp
    wl_inter.cpp
    wl_main.cpp
    wl_menu.cpp
    wl_play.cpp
    wl_state.cpp
    wl_text.cpp
    states.cpp
)

# Files that only belong to a feature.
if(USE_SHADING)
    list(APPEND SRCS wl_shade.cpp)
endif()
if(USE_DIR3DSPR)
    list(APPEND SRCS wl_dir3dspr.cpp)
endif()
if(USE_FLOORCEILINGTEX)
    list(APPEND SRCS wl_floorceiling.cpp)
endif()
if(USE_PARALLAX)
    list(APPEND SRCS wl_parallax.cpp)
endif()
if(USE_CLOUDSKY)
    list(APPEND SRCS wl_cloudsky.cpp)
endif()
if(USE_STARSKY OR USE_RAIN OR USE_SNOW)
    list(APPEND SRCS wl_atmos.cpp)
endif()

add_executable(wolf4sdl ${SRCS})

set_target_properties(wolf4sdl PROPERTIES
    OUTPUT_NAME ${BINARY}
    C_STANDARD 99
    C_EXTENSIONS ON
)

target_compile_options(wolf4sdl PRIVATE
    -Wall
    -Wpointer-arith
    -Wreturn-type
    -Wwrite-strings
    -Wcast-align
    $<$<COMPILE_LANGUAGE:C>:-Werror-implicit-function-declaration>
    $<$<COMPILE_LANGUAGE:C>:-Wimplicit-int>
    $<$<COMPILE_LANGUAGE:C>:-Wsequence-point>
)

target_link_libraries(wolf4sdl PRIVATE PkgConfig::SDL2)

foreach(flag IN ITEMS
        DEBUGKEYS ARTSEXTERN DEMOSEXTERN PLAYDEMOLIKEORIGINAL
        USE_FEATUREFLAGS USE_SHADING USE_DIR3DSPR USE_FLOORCEILINGTEX USE_HIRES
        USE_CLOUDSKY USE_STARSKY USE_RAIN USE_SNOW FIXRAINSNOWLEAKS)
    if(${flag})
        target_compile_definitions(wolf4sdl PRIVATE ${flag})
    endif()
endforeach()

if(USE_PARALLAX)
    target_compile_definitions(wolf4sdl PRIVATE USE_PARALLAX=${USE_PARALLAX})
endif()

if(DATADIR)
    target_compile_definitions(wolf4sdl PRIVATE "DATADIR=\"${DATADIR}\"")
endif()

if(MINGW)
    target_link_options(wolf4sdl PRIVATE -static-libgcc)
endif()

# The Makefile installed the stripped binary with mode 555, use "cmake --install --strip".
include(GNUInstallDirs)
install(TARGETS wolf4sdl
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
    PERMISSIONS OWNER_READ OWNER_EXECUTE GROUP_READ GROUP_EXECUTE WORLD_READ WORLD_EXECUTE
)
