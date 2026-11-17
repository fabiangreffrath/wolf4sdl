// Locates the game files: a list of directories to look in and a file lookup
// that tolerates the usual case variations of the file names.

#include "wl_def.h"

#include <sys/stat.h>

#ifdef _WIN32
#include <direct.h>
#define DIR_SEPARATOR_S "\\"
#define PATH_SEPARATOR ';'
#else
#define DIR_SEPARATOR_S "/"
#define PATH_SEPARATOR ':'
#endif

const char *datadirs[MAXDATADIRS];
int numdatadirs;
const char *datadir = ".";

// Returns a newly allocated string with the N strings of S joined, the program ends if one of them is NULL.
static char *joinstrings (const char *const s[], size_t n)
{
    size_t length = 1;      // start with 1 for the null terminator

    for (size_t i = 0; i < n; i++)
    {
        if (s[i] == NULL)
            Quit("Argument %d of a string join is NULL", (int) i + 1);

        length += strlen(s[i]);
    }

    char *const result = (char *) malloc(length);
    if (result == NULL)
        Quit("Out of memory");

    char *end = result;
    for (size_t i = 0; i < n; i++)
    {
        const size_t len = strlen(s[i]);

        memcpy(end, s[i], len);
        end += len;
    }
    *end = '\0';

    return result;
}

// Joins directory, name and extension to a newly allocated path.
static char *joinpath (const char *dir, const char *name, const char *ext)
{
    const char *const parts[] = { dir, DIR_SEPARATOR_S, name, ext };

    return joinstrings(parts, sizeof(parts) / sizeof(parts[0]));
}

// Returns true if the path exists and is not a directory.
static bool fileexists (const char *path)
{
    struct stat statbuf;

    return stat(path, &statbuf) == 0 && !S_ISDIR(statbuf.st_mode);
}

// Returns the file name part of a path, nothing is allocated.
static const char *filepart (const char *path)
{
    const char *last = strrchr(path, '/');

#ifdef _WIN32
    const char *const backslash = strrchr(path, '\\');

    if (backslash != NULL && (last == NULL || backslash > last))
        last = backslash;
#endif

    return last != NULL ? last + 1 : path;
}

// Changes a string to lowercase, only the letters A to Z are affected.
static void lowerstring (char *s)
{
    for (; *s; s++)
        if (*s >= 'A' && *s <= 'Z')
            *s += 'a' - 'A';
}

// Changes a string to uppercase, only the letters a to z are affected.
static void upperstring (char *s)
{
    for (; *s; s++)
        if (*s >= 'a' && *s <= 'z')
            *s -= 'a' - 'A';
}

// Check if a file exists by probing for common case variations of its filename.
// Returns a newly allocated string that the caller is responsible for freeing.
char *FileCaseExists (const char *path)
{
    char *const dup = strdup(path);
    if (dup == NULL)
        Quit("Out of memory");

    // 0: actual path
    if (fileexists(dup))
        return dup;

    char *const filename = (char *) filepart(dup);

    // 1: lowercase filename, e.g. vswap.wl6
    lowerstring(filename);
    if (fileexists(dup))
        return dup;

    // 2: uppercase filename, e.g. VSWAP.WL6
    upperstring(filename);
    if (fileexists(dup))
        return dup;

    // 3: uppercase basename with lowercase extension, e.g. VSWAP.wl6
    char *const ext = strrchr(dup, '.');
    if (ext != NULL && ext > filename)
    {
        lowerstring(ext + 1);
        if (fileexists(dup))
            return dup;
    }

    // 4: lowercase filename with uppercase first letter, e.g. Vswap.wl6
    if (strlen(filename) > 1)
    {
        lowerstring(filename + 1);
        if (fileexists(dup))
            return dup;
    }

    // 5: no luck
    free(dup);
    return NULL;
}

// Adds a directory to the list unless it is empty, known already or the list is full.
static void adddir (const char *dir)
{
    if (dir == NULL || *dir == '\0' || numdatadirs == MAXDATADIRS)
        return;

    for (int i = 0; i < numdatadirs; i++)
        if (!strcmp(datadirs[i], dir))
            return;

    char *const copy = strdup(dir);
    if (copy == NULL)
        Quit("Out of memory");

    datadirs[numdatadirs++] = copy;
}

#ifndef _WIN32

// Adds the directories of a list separated by PATH_SEPARATOR, each one with the suffix appended.
static void adddirs (const char *paths, const char *suffix)
{
    char *const copy = strdup(paths);
    if (copy == NULL)
        Quit("Out of memory");

    for (char *dir = copy, *next; dir != NULL; dir = next)
    {
        next = strchr(dir, PATH_SEPARATOR);
        if (next != NULL)
            *next++ = '\0';

        if (*dir != '\0')
        {
            const char *const parts[] = { dir, suffix };
            char *const path = joinstrings(parts, sizeof(parts) / sizeof(parts[0]));

            adddir(path);
            free(path);
        }
    }

    free(copy);
}

// Returns the home directory of the user, or NULL if it is not known.
static const char *homedir (void)
{
    const char *const home = getenv("HOME");

    return home != NULL && *home != '\0' ? home : NULL;
}

// Adds the locations of the XDG base directory specification, see freedesktop.org.
static void addxdgdirs (void)
{
    const char *const datahome = getenv("XDG_DATA_HOME");
    const char *const home = homedir();

    // $XDG_DATA_HOME defaults to $HOME/.local/share
    if (datahome != NULL && *datahome != '\0')
    {
        const char *const parts[] = { datahome, "/games/wolf3d" };
        char *const path = joinstrings(parts, sizeof(parts) / sizeof(parts[0]));

        adddir(path);
        free(path);
    }
    else if (home != NULL)
    {
        const char *const parts[] = { home, "/.local/share/games/wolf3d" };
        char *const path = joinstrings(parts, sizeof(parts) / sizeof(parts[0]));

        adddir(path);
        free(path);
    }

    // $XDG_DATA_DIRS defaults to /usr/local/share:/usr/share
    const char *dirs = getenv("XDG_DATA_DIRS");
    if (dirs == NULL || *dirs == '\0')
        dirs = "/usr/local/share:/usr/share";

    adddirs(dirs, "/games/wolf3d");
}

#endif // _WIN32

// Builds the list of directories that are searched for game files.
void BuildDataDirList (void)
{
    if (numdatadirs > 0)
        return;

    // Look in the current directory. The engine always did this.
    adddir(".");

#ifdef _WIN32
    // On Windows the directory of the executable is a natural place as well.
    char *const base = SDL_GetBasePath();
    if (base != NULL)
    {
        adddir(base);
        SDL_free(base);
    }
#else
    addxdgdirs();
#endif
}

// Returns true if the directory has a file of this name, in any of the case variations.
static bool hasfile (const char *dir, const char *name, const char *ext)
{
    char *const path = joinpath(dir, name, ext);
    char *const found = FileCaseExists(path);
    const bool exists = found != NULL;

    free(found);
    free(path);
    return exists;
}

// Returns true if the directory has all files of a data set.
// The maps are in gamemaps.* or, without Carmack compression, in maptemp.*.
bool DataSetComplete (const char *dir, const char *ext, const char *graphext)
{
    static const char *const extfiles[] = { "vswap.", "maphead." };
    static const char *const graphfiles[] = { "vgahead.", "vgagraph.", "vgadict.", "audiohed.", "audiot." };

    if (!hasfile(dir, "gamemaps.", ext) && !hasfile(dir, "maptemp.", ext))
        return false;

    for (size_t i = 0; i < sizeof(extfiles) / sizeof(extfiles[0]); i++)
        if (!hasfile(dir, extfiles[i], ext))
            return false;

    for (size_t i = 0; i < sizeof(graphfiles) / sizeof(graphfiles[0]); i++)
        if (!hasfile(dir, graphfiles[i], graphext))
            return false;

    return true;
}

// Returns a newly allocated path of a file in the data directory, the caller has to free it.
// If the file exists under a different case, the path of that file is returned.
char *DataFilePath (const char *name, const char *ext)
{
    char *const path = joinpath(datadir, name, ext);
    char *const found = FileCaseExists(path);

    if (found == NULL)
        return path;

    free(path);
    return found;
}

// Returns a newly allocated string that lists the directories, each one in a line of its own.
char *DataDirListString (void)
{
    size_t length = 2;      // start with 2 for the \n and null terminator

    for (int i = 0; i < numdatadirs; i++)
        length += strlen(datadirs[i]) + 3;      // a newline and two spaces of indentation

    char *const result = (char *) malloc(length);
    if (result == NULL)
        Quit("Out of memory");

    char *end = result;
    *end = '\0';

    for (int i = 0; i < numdatadirs; i++)
        end += snprintf(end, result + length - end, "\n  %s", datadirs[i]);

    end += snprintf(end, result + length - end, "\n");

    return result;
}

#ifdef _WIN32

// Returns true if a file can be created in the directory.
static bool dirwritable (const char *dir)
{
    char *const path = joinpath(dir, CONFIGFILENAME, ".tmp");
    FILE *const file = fopen(path, "wb");
    const bool writable = file != NULL;

    if (writable)
    {
        fclose(file);
        remove(path);
    }

    free(path);
    return writable;
}

#endif // _WIN32

// Returns the default config directory without a trailing separator in a newly allocated string, or NULL if SDL does not know one.
// On Windows the directory of the executable is used if it is writable, otherwise the preferences directory of SDL like elsewhere.
static char *defaultconfigdir (void)
{
    char *sdlpath = NULL;

#ifdef _WIN32
    char *const base = SDL_GetBasePath();

    if (base != NULL && dirwritable(base))
        sdlpath = base;
    else
        SDL_free(base);
#endif

    if (sdlpath == NULL)
        sdlpath = SDL_GetPrefPath("", CONFIGDIRNAME);
    if (sdlpath == NULL)
        return NULL;

    char *const path = strdup(sdlpath);
    SDL_free(sdlpath);
    if (path == NULL)
        Quit("Out of memory");

    size_t length = strlen(path);
    while (length > 1 && (path[length - 1] == '/' || path[length - 1] == '\\'))
        path[--length] = '\0';

    return path;
}

// Sets the config directory unless --configdir gave one and creates it if it does not exist.
// The default is the preferences directory of SDL, see defaultconfigdir() for Windows.
void SetupConfigDir (void)
{
    if (configdir[0] == '\0')
    {
        char *const dir = defaultconfigdir();

        if (dir == NULL)
        {
            printf("The config directory is not known, using the current directory.\n");
        }
        else
        {
            if (strlen(dir) >= sizeof(configdir))
                Quit("The path of the config directory \"%s\" is too long.", dir);

            strcpy(configdir, dir);
            free(dir);
        }
    }

    if (configdir[0] != '\0')
    {
        struct stat statbuf;

        if (stat(configdir, &statbuf) != 0)
        {
#ifdef _WIN32
            if (_mkdir(configdir) != 0)
#else
            if (mkdir(configdir, 0755) != 0)
#endif
                Quit("The configuration directory \"%s\" could not be created.", configdir);
        }
    }
}

// Returns the path of the config file, which has the same name for all games.
// The string is allocated on the first call and must not be freed.
const char *ConfigFilePath (void)
{
    static char *path;

    if (path == NULL)
        path = joinpath(configdir[0] != '\0' ? configdir : ".", CONFIGFILENAME, "");

    return path;
}
