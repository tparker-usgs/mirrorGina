#!/bin/sh
set -x

export GIT_SSL_NO_VERIFY=true

for i in pyresample mpop posttroll pycoast pydecorate pyorbital pytroll-schedule pyspectral python-geotiepoints trollduction; do
	echo "+++ installing $i"
	git clone --progress --verbose git://github.com/pytroll/${i}.git
	cd $i
	if [ $i = "posttroll" ] ; then
		git checkout develop
	elif [ $i = "pyresample" ] ; then
		git checkout pre-master
	elif [ $i = "pyorbital" ] ; then
		git checkout develop
	elif [ $i = "pytroll-schedule" ] ; then
		git checkout develop
	elif [ $i = "pycoast" ] ; then
		git checkout pre-master
	elif [ $i = "python-geotiepoints" ] ; then
		git checkout develop
	fi

	python setup.py install
	cd ..
done

#git clone git://github.com/tparker-usgs/trollduction.git
#git clone git://github.com/pytroll/trollduction.git
#cd trollduction
#python setup.py install
