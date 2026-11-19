cmake_minimum_required(VERSION 3.13)

# Automatically installs dependencies.
set(X_VCPKG_APPLOCAL_DEPS_INSTALL ON)

project(
    "Intenseflow"
    VERSION 20261115
    LANGUAGES C CXX
)

string(TOLOWER ${PROJECT_NAME} PROJECT_LOWERNAME)

# --- Options ---------------------------------------------------------------

# Name of the executable.
set(BINARY intenseflow CACHE STRING "Name of the executable")

option(WARNINGS_AS_ERRORS "Treat all compiler warnings as errors" OFF)

# Features that are switched on or off at build time.
option(ARTSEXTERN "Take the help and end texts from the graphics file" ON)
option(DEBUGKEYS "Enable the Tab debug keys" ON)
option(DEMOSEXTERN "Take the demos from the graphics file" ON)
option(FIXRAINSNOWLEAKS "Fix leaking ceilings, only needed for maps with rain or snow and ceilings" OFF)
option(PLAYDEMOLIKEORIGINAL "Do not apply bug fixes while playing or recording demos" ON)
option(USE_CLOUDSKY "Enable cloud sky support (wl_cloudsky.cpp)" OFF)
option(USE_DIR3DSPR "Enable directional 3D sprites (wl_dir3dspr.cpp)" OFF)
option(USE_FEATUREFLAGS "Enable the level feature flags (see the bottom of wl_def.h)" OFF)
option(USE_FLOORCEILINGTEX "Enable floor and ceiling textures in the third map plane (wl_floorceiling.cpp)" OFF)
option(USE_HIRES "Enable high resolution textures and sprites (128x128)" OFF)
option(USE_RAIN "Enable rain support (wl_atmos.cpp)" OFF)
option(USE_SHADING "Enable shading support (wl_shade.cpp)" OFF)
option(USE_SNOW "Enable snow support (wl_atmos.cpp)" OFF)
option(USE_STARSKY "Enable star sky support (wl_atmos.cpp)" OFF)
set(USE_PARALLAX "" CACHE STRING "Enable the parallax sky with this many textures per sky, for example 16")

# Default to -O2 -g unless a build type or configuration is given.
if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    add_compile_options(-O2 -g)
endif()

# --- Sources ---------------------------------------------------------------

set(SRCS
    datadir.cpp
    id_ca.cpp
    id_in.cpp
    id_pm.cpp
    id_sd.cpp
    id_us_1.cpp
    id_vh.cpp
    id_vl.cpp
    layouts_gen.cpp
    opl3/opl3.c
    signon.cpp
    states.cpp
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
)

# Files that only belong to a feature.
if(USE_CLOUDSKY)
    list(APPEND SRCS wl_cloudsky.cpp)
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
if(USE_RAIN OR USE_SNOW OR USE_STARSKY)
    list(APPEND SRCS wl_atmos.cpp)
endif()
if(USE_SHADING)
    list(APPEND SRCS wl_shade.cpp)
endif()

list(TRANSFORM SRCS PREPEND src/)

# --- Target ----------------------------------------------------------------

add_executable(intenseflow ${SRCS})

set_target_properties(intenseflow PROPERTIES
    OUTPUT_NAME ${BINARY}
    C_STANDARD 99
    C_EXTENSIONS ON
)

target_include_directories(intenseflow PRIVATE src src/opl3)

# Names and features for the preprocessor.
target_compile_definitions(intenseflow PRIVATE
    PROJECT_NAME="${PROJECT_NAME}"
    PROJECT_VERSION="${PROJECT_VERSION}"
    PROJECT_STRING="${PROJECT_NAME} ${PROJECT_VERSION}"
    PROJECT_LOWERNAME="${PROJECT_LOWERNAME}"
)

foreach(flag IN ITEMS
        ARTSEXTERN DEBUGKEYS DEMOSEXTERN FIXRAINSNOWLEAKS PLAYDEMOLIKEORIGINAL
        USE_CLOUDSKY USE_DIR3DSPR USE_FEATUREFLAGS USE_FLOORCEILINGTEX USE_HIRES
        USE_RAIN USE_SHADING USE_SNOW USE_STARSKY)
    if(${flag})
        target_compile_definitions(intenseflow PRIVATE ${flag})
    endif()
endforeach()

if(USE_PARALLAX)
    target_compile_definitions(intenseflow PRIVATE USE_PARALLAX=${USE_PARALLAX})
endif()

# --- Compiler and linker settings ------------------------------------------

if(MSVC)
    # silence warnings about POSIX functions
    target_compile_options(intenseflow PUBLIC -D_CRT_SECURE_NO_WARNINGS -D_CRT_NONSTDC_NO_WARNINGS)
    # silence unsigned/signed and integer truncation warnings
    target_compile_options(intenseflow PRIVATE /wd4267 /wd4244)
else()
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
endif()

if(WARNINGS_AS_ERRORS)
    if(MSVC)
        target_compile_options(intenseflow PRIVATE /WX)
    else()
        target_compile_options(intenseflow PRIVATE -Werror)
    endif()
endif()

if(WIN32)
    target_sources(intenseflow PRIVATE dist/intenseflow.rc)

    if(MSVC)
        target_link_options(intenseflow PRIVATE
            "/MANIFEST:NO"
            "$<IF:$<OR:$<CONFIG:Debug>,$<CONFIG:RelWithDebInfo>>,/SUBSYSTEM:CONSOLE,/SUBSYSTEM:WINDOWS>"
        )
    else()
        target_link_options(intenseflow PRIVATE
            "$<IF:$<OR:$<CONFIG:Debug>,$<CONFIG:RelWithDebInfo>>,-mconsole,-mwindows>"
        )
    endif()
endif()

if(MINGW)
    target_link_options(intenseflow PRIVATE -static-libgcc)
endif()

# --- Dependencies ----------------------------------------------------------

find_package(SDL2 REQUIRED CONFIG)
find_package(SDL2_mixer REQUIRED CONFIG)

target_link_libraries(intenseflow PRIVATE
    $<TARGET_NAME_IF_EXISTS:SDL2::SDL2main>
    $<IF:$<TARGET_EXISTS:SDL2::SDL2>,SDL2::SDL2,SDL2::SDL2-static>
    $<IF:$<TARGET_EXISTS:SDL2_mixer::SDL2_mixer>,SDL2_mixer::SDL2_mixer,SDL2_mixer::SDL2_mixer-static>
)

# --- Installation ----------------------------------------------------------

include(GNUInstallDirs)

if(WIN32)
    if(CMAKE_VERSION VERSION_GREATER_EQUAL 3.21 AND NOT VCPKG_TOOLCHAIN)
        install(
            TARGETS intenseflow
            RUNTIME_DEPENDENCIES
            PRE_EXCLUDE_REGEXES "api-ms-" "ext-ms-"
            POST_EXCLUDE_REGEXES ".*system32/.*\\.dll"
            DIRECTORIES $<TARGET_FILE_DIR:intenseflow> $ENV{PATH}
            RUNTIME DESTINATION .
        )
    else()
        install(TARGETS intenseflow RUNTIME DESTINATION .)
    endif()
    install(FILES README.md DESTINATION .)
else()
    install(TARGETS intenseflow
        RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
        PERMISSIONS OWNER_READ OWNER_EXECUTE GROUP_READ GROUP_EXECUTE WORLD_READ WORLD_EXECUTE
    )
    install(FILES dist/intenseflow.desktop DESTINATION ${CMAKE_INSTALL_DATADIR}/applications)
    install(FILES dist/intenseflow.png DESTINATION ${CMAKE_INSTALL_DATADIR}/icons/hicolor/128x128/apps)
    install(FILES dist/intenseflow.6 DESTINATION ${CMAKE_INSTALL_MANDIR}/man6)
    install(FILES README.md DESTINATION ${CMAKE_INSTALL_DOCDIR})
endif()

# --- Packaging -------------------------------------------------------------

set(CPACK_GENERATOR ZIP)
set(CPACK_PACKAGE_NAME ${PROJECT_LOWERNAME})
set(CPACK_SOURCE_GENERATOR TGZ ZIP)
set(CPACK_SOURCE_IGNORE_FILES "/.git/;/cmake-build/;/build/;/.vs/;/out/;CMakeSettings.json")
set(CPACK_STRIP_FILES TRUE)
include(CPack)
