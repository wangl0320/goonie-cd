#!/bin/bash


if [ "$1" == "INSTANCE" ]
then
    echo $3 > /var/run/keepalived.state
fi

