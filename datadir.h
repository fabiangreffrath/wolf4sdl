#ifndef DATADIR_H
#define DATADIR_H

#define MAXDATADIRS 16

// Directories that are searched for game files, in the order of priority.
extern const char *datadirs[MAXDATADIRS];
extern int numdatadirs;

// The directory the game files are taken from.
extern const char *datadir;

char *FileCaseExists (const char *path);
void BuildDataDirList (void);
bool DataSetComplete (const char *dir, const char *ext, const char *graphext);
char *DataFilePath (const char *name, const char *ext);

#endif
