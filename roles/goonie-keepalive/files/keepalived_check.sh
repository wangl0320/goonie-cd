#!/bin/bash

CHECK_TIME=3
  
#mysql slave is working MYSQL_OK is 1 , mysql down or slave not running MYSQL_OK is 0
  
MYSQL_OK=1

  
function check_mysql_helth (){
    slave_res=`mysql -e "show slave status\G;"| egrep 'Slave_IO_Running|Slave_SQL_Running'| grep Yes`
    if [ -n "${slave_res}" ] 
    then
        MYSQL_OK=1
    else
        MYSQL_OK=0
    fi
    return $MYSQL_OK
}

currstate=`grep MASTER /var/run/keepalived.state`
if [ -n "${currstate}" ]
then
    gooniestate=`systemctl status goonie-mng | grep running`
    if [ -z "${gooniestate}" ]
    then
        systemctl start goonie-mng
    fi
fi

while [ $CHECK_TIME -ne 0 ]
do
    let "CHECK_TIME -= 1"
    check_mysql_helth
    if [ $MYSQL_OK == 1 ]
    then
        CHECK_TIME=0
    exit 0
fi
if [ $MYSQL_OK -eq 0 ] &&  [ $CHECK_TIME -eq 0 ]
then
    service keepalived stop
    /usr/local/bin/keepalived_backup.sh
    exit 1
fi
sleep 1
done

