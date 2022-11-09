#!/bin/bash

pushd `dirname $0` > /dev/null
SCRIPT_DIR=`pwd -P`
popd > /dev/null

ACTION=deploy
RESTART=1
ENVR=jp_new
HOST=prod
USER=ubuntu
PORT=22

usage()
{
    echo "Usage: `basename $0` [-b|f] [-p] [-r] [-h HOST] [-u] [-p] [-v]"
    exit 1
}

[ $# -eq 0 ] && usage

while getopts :b:v:frh:u:p: OPTION
do
    case $OPTION in
        b)
            ENVR=$OPTARG
            ;;
        f)
            ENVR=ua_newweb
            ;;
        r)
            RESTART=0
            ;;
        h)
            HOST=$OPTARG
            ;;
        u)
            USER=$OPTARG
            ;;
        p)
            PORT=$OPTARG
            ;;
        v)
            VERSION=$OPTARG
            ;;
        \?)
            usage
            ;;
    esac
done


(
    cd $SCRIPT_DIR
    echo $HOST
    echo $ENVR
    echo $VERSION

    fab dep:$HOST,$VERSION pro:$ENVR,$USER,$PORT $ACTION:$RESTART
)
