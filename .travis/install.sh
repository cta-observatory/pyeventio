#!/bin/bash

if [[ $TRAVIS_OS_NAME == 'osx' ]]; then
	curl -o miniconda.sh https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
	bash miniconda.sh -p $HOME/miniconda -b
	. $HOME/miniconda/etc/profile.d/conda.sh
	conda activate
	conda create --yes -n travis python=$PYTHON
	conda activate travis
fi
