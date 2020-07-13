#!/bin/sh
if [ "$ANALYZE" = "true" ] ; then
	cppcheck -DO_BINARY=0 -DDEBUGKEYS -DARTSEXTERN -DDEMOSEXTERN -DPLAYDEMOLIKEORIGINAL \
	         -UUSE_FEATUREFLAGS -UUSE_SHADING -UUSE_DIR3DSPR -UUSE_FLOORCEILINGTEX -UUSE_HIRES \
	         -UUSE_PARALLAX -UUSE_CLOUDSKY -UUSE_STARSKY -UUSE_RAIN -UUSE_SNOW -UFIXRAINSNOWLEAKS \
	         -UGP2X -UGP2X_940 -U_arch_dreamcast -USPANISH -UNOTYET \
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
	make
	echo "Wolf3d Full v1.4 Apogee (with ReadThis)"
	make clean
	sed -e "s|^\(//\)\?\(#define GOODTIMES\)|//\2|" -i version.h
	make
	echo "Wolf3d Full v1.1 Apogee (with ReadThis)"
	make clean
	sed -e "s|^\(//\)\?\(#define APOGEE_1_1\)|\2|" -i version.h
	make
	echo "Wolf3d Shareware v1.4"
	make clean
	sed -e "s|^\(//\)\?\(#define APOGEE_1_1\)|//\2|" -i version.h
	sed -e "s|^\(//\)\?\(#define UPLOAD\)|\2|" -i version.h
	make
	echo "Spear of Destiny Full and Mission Disks (and GOODTIMES for no FormGen quiz)"
	make clean
	sed -e "s|^\(//\)\?\(#define UPLOAD\)|//\2|" -i version.h
	sed -e "s|^\(//\)\?\(#define SPEAR\)|\2|" -i version.h
	sed -e "s|^\(//\)\?\(#define GOODTIMES\)|\2|" -i version.h
	make
	echo "Spear of Destiny Demo"
	make clean
	sed -e "s|^\(//\)\?\(#define GOODTIMES\)|//\2|" -i version.h
	sed -e "s|^\(//\)\?\(#define SPEARDEMO\)|\2|" -i version.h
	make
fi
