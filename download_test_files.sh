# env var DL cred is set by .travis.yml from secure key
set -e

URL1="https://www.mpi-hd.mpg.de/personalhomes/bernlohr/cta-raw/Prod-3/data-demo2/Paranal/Sector/Gamma-clean-1/gamma_20deg_180deg_run1187___cta-prod3-demo_desert-2150m-Paranal-demo2sect_cone10.simtel-clean3.gz"
URL2="https://www.mpi-hd.mpg.de/personalhomes/bernlohr/cta-raw/Prod-3/data-demo2/Paranal/Sector/Gamma-clean-1/gamma_20deg_180deg_run1187___cta-prod3-demo_desert-2150m-Paranal-demo2sect_cone10.simtel.gz"

if [[ $TRAVIS_OS_NAME != 'osx' ]]; then
    mkdir test_files
    cd test_files
    export TEST_FILE_DIR=`pwd -P`
    echo $TEST_FILE_DIR
    curl --fail -o test.simtel-clean3.gz -u $DL_CRED $URL1
    curl --fail -o  test.simtel_10MB_part.gz -u $DL_CRED --range 0-10000000 $URL2
    cd ..
fi

