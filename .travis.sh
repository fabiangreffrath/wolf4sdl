#!/bin/sh
if [ "$ANALYZE" = "true" ] ; then
	cppcheck -DO_BINARY=0 -DDEBUGKEYS -DARTSEXTERN -DDEMOSEXTERN -DPLAYDEMOLIKEORIGINAL \
	         -UUSE_FEATUREFLAGS -UUSE_SHADING -UUSE_DIR3DSPR -UUSE_FLOORCEILINGTEX -UUSE_HIRES \
	         -UUSE_PARALLAX -UUSE_CLOUDSKY -UUSE_STARSKY -UUSE_RAIN -UUSE_SNOW -UFIXRAINSNOWLEAKS \
	         -UGP2X -UGP2X_940 -U_arch_dreamcast -USPANISH -UNOTYET -U_MSC_VER -U__WATCOMC__ \
	         --error-exitcode=1 --force -Idosbox . 2> stderr.txt
	RET=$?
	if [ -s stderr.txt ]
	then
		cat stderr.txt
	fi
	exit $RET
else
	set -e

	export Q=""
	export CFLAGS="-Werror"

	echo "Wolf3d Full v1.4 GT/ID/Activision"
	make BINARY=wolf4sdl-wl6
	make clean

	echo "Wolf3d Full v1.4 Apogee (with ReadThis)"
	sed -e "s|^\(//\)\?\(#define GOODTIMES\)|//\2|" -i version.h
	make BINARY=wolf4sdl-wl6a
	make clean

	echo "Wolf3d Full v1.1 Apogee (with ReadThis)"
	sed -e "s|^\(//\)\?\(#define APOGEE_1_1\)|\2|" -i version.h
	make BINARY=wolf4sdl-wl6a1
	make clean

	echo "Wolf3d Shareware v1.4"
	sed -e "s|^\(//\)\?\(#define APOGEE_1_1\)|//\2|" -i version.h
	sed -e "s|^\(//\)\?\(#define UPLOAD\)|\2|" -i version.h
	make BINARY=wolf4sdl-wl1
	make clean

	echo "Spear of Destiny Full and Mission Disks (and GOODTIMES for no FormGen quiz)"
	sed -e "s|^\(//\)\?\(#define UPLOAD\)|//\2|" -i version.h
	sed -e "s|^\(//\)\?\(#define SPEAR\)|\2|" -i version.h
	sed -e "s|^\(//\)\?\(#define GOODTIMES\)|\2|" -i version.h
	make BINARY=wolf4sdl-sod
	make clean

	echo "Spear of Destiny Demo"
	sed -e "s|^\(//\)\?\(#define GOODTIMES\)|//\2|" -i version.h
	sed -e "s|^\(//\)\?\(#define SPEARDEMO\)|\2|" -i version.h
	make BINARY=wolf4sdl-sdm
	make clean

	sed -e "s|^\(//\)\?\(#define SPEAR\)|//\2|" -i version.h
	sed -e "s|^\(//\)\?\(#define SPEARDEMO\)|//\2|" -i version.h
	sed -e "s|^\(//\)\?\(#define GOODTIMES\)|\2|" -i version.h
fi
