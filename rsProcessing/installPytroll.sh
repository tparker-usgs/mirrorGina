#!/bin/sh
set -x

export GIT_SSL_NO_VERIFY=true
#for i in pytroll-schedule pyresample mpop posttroll pycoast pydecorate pyorbital trollduction ; do
for i in pyresample mpop posttroll pycoast pydecorate pyorbital pytroll-schedule; do
	echo "+++ installing $i"
	git clone --progress --verbose git://github.com/pytroll/${i}.git
	cd $i
	if [ $i = "posttroll" ] ; then
		echo "+++ switching to branch develop"
		git checkout develop
	elif [ $i = "pytroll-schedule" ] ; then
		echo "+++ switching to branch develop"
		git branch
		git checkout develop
		git branch
	fi
	python setup.py install
	cd ..
done

git clone git://github.com/tparker-usgs/trollduction.git
cd trollduction
python setup.py install
