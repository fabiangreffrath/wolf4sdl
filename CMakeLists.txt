cmake_minimum_required(VERSION 3.13)

# Automatically installs dependencies.
set(X_VCPKG_APPLOCAL_DEPS_INSTALL ON)

project(
    "Intenseflow"
    VERSION 20261115
    LANGUAGES C CXX
)

# Name of the executable.
set(BINARY intenseflow CACHE STRING "Name of the executable")

# The Makefile used -O2 -g unless a configuration said otherwise.
if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    add_compile_options(-O2 -g)
endif()

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

set(SRCS
    opl3/opl3.c
    datadir.cpp
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

list(TRANSFORM SRCS PREPEND src/)

add_executable(intenseflow ${SRCS})

set_target_properties(intenseflow PROPERTIES
    OUTPUT_NAME ${BINARY}
    C_STANDARD 99
    C_EXTENSIONS ON
)

target_compile_options(intenseflow PRIVATE
    -Wall
    -Wpointer-arith
    -Wreturn-type
    -Wwrite-strings
    -Wcast-align
    $<$<COMPILE_LANGUAGE:C>:-Werror-implicit-function-declaration>
    $<$<COMPILE_LANGUAGE:C>:-Wimplicit-int>
    $<$<COMPILE_LANGUAGE:C>:-Wsequence-point>
)

if(MSVC)
    # silence warnings about POSIX functions
    target_compile_options(intenseflow PUBLIC -D_CRT_SECURE_NO_WARNINGS -D_CRT_NONSTDC_NO_WARNINGS)
    # silence unsigned/signed and integer truncation warnings
    target_compile_options(intenseflow PRIVATE /wd4267 /wd4244)
endif()

target_include_directories(intenseflow PRIVATE src src/opl3)

find_package(SDL2 REQUIRED CONFIG)
find_package(SDL2_mixer REQUIRED CONFIG)

target_link_libraries(intenseflow PRIVATE
    $<TARGET_NAME_IF_EXISTS:SDL2::SDL2main>
    $<IF:$<TARGET_EXISTS:SDL2::SDL2>,SDL2::SDL2,SDL2::SDL2-static>
    $<IF:$<TARGET_EXISTS:SDL2_mixer::SDL2_mixer>,SDL2_mixer::SDL2_mixer,SDL2_mixer::SDL2_mixer-static>
)

target_compile_definitions(intenseflow PRIVATE PROJECT_NAME="${PROJECT_NAME}")
target_compile_definitions(intenseflow PRIVATE PROJECT_VERSION="${PROJECT_VERSION}")
target_compile_definitions(intenseflow PRIVATE PROJECT_STRING="${PROJECT_NAME} ${PROJECT_VERSION}")

string(TOLOWER ${PROJECT_NAME} PROJECT_LOWERNAME)
target_compile_definitions(intenseflow PRIVATE PROJECT_LOWERNAME="${PROJECT_LOWERNAME}")

foreach(flag IN ITEMS
        DEBUGKEYS ARTSEXTERN DEMOSEXTERN PLAYDEMOLIKEORIGINAL
        USE_FEATUREFLAGS USE_SHADING USE_DIR3DSPR USE_FLOORCEILINGTEX USE_HIRES
        USE_CLOUDSKY USE_STARSKY USE_RAIN USE_SNOW FIXRAINSNOWLEAKS)
    if(${flag})
        target_compile_definitions(intenseflow PRIVATE ${flag})
    endif()
endforeach()

if(USE_PARALLAX)
    target_compile_definitions(intenseflow PRIVATE USE_PARALLAX=${USE_PARALLAX})
endif()

if(MINGW)
    target_link_options(intenseflow PRIVATE -static-libgcc)
endif()

# The Makefile installed the stripped binary with mode 555, use "cmake --install --strip".
include(GNUInstallDirs)
install(TARGETS intenseflow
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
    PERMISSIONS OWNER_READ OWNER_EXECUTE GROUP_READ GROUP_EXECUTE WORLD_READ WORLD_EXECUTE
)

# Desktop integration files.
if(NOT WIN32)
    install(FILES dist/intenseflow.desktop DESTINATION ${CMAKE_INSTALL_DATADIR}/applications)
    install(FILES dist/intenseflow.svg DESTINATION ${CMAKE_INSTALL_DATADIR}/icons/hicolor/scalable/apps)
    install(FILES dist/intenseflow.6 DESTINATION ${CMAKE_INSTALL_MANDIR}/man6)
endif()
