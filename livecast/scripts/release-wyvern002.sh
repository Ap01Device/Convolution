#!/usr/bin/env bash
#==============================================================================
#     FileName: release-wyvern002.sh
#         Desc: release wyvern002
#      License: GPL
#       Author: Aurio Pinto 
#        Email: auriopinto@outlook.com 
#      Version: 0.0.2
#   LastChange: 2019-09-28 09:35:11
#    CreatedAt: 2019-07-16 09:12:23
#==============================================================================

# functions
function confirm () {
    # call with a prompt string or use a default
    read -r -p "${1:-Are you sure? [y/N]} " response
    case $response in
        [yY][eE][sS]|[yY])
            true
            ;;
        *)
            false
            ;;
    esac
}

function release() {
    # restart wyvern
    supervisorctl restart wyvern

    # restart workers
    supervisorctl restart wyvern_celerywork_qcard_2
    # supervisorctl restart wyvern:wyvern_celerywork_qcard
    # supervisorctl restart wyvern:wyvern_celerywork_wenwen
    # supervisorctl restart wyvern:wyvern_celerywork_xqcircle

    # restart heartbeat
    # supervisorctl restart wyvern:wyvern_celerybeat
}

function migrage() {
    # make migrations
    echo 'source venv/bin/activate'
    echo 'python manage.py makemigrations --settings=wyvern.settings.prod'
    echo 'python manage.py migrate --settings=wyvern.settings.prod'
}

function run() {
    release
}

run
