#!/bin/bash

#!/bin/bash
CHECK_TIME=3
  
#mysql slave is working MYSQL_OK is 1 , mysql down or slave not running MYSQL_OK is 0
  
MYSQL_OK=1
  
function check_mysql_helth (){
    slave_res=`mysql -e "show slave status\G;"| grep Slave_SQL_Running|awk '{print $2}'`
    if [ "${slave_res}" == "Yes" ] 
    then
        MYSQL_OK=1
    else
        MYSQL_OK=0
    fi
    return $MYSQL_OK
}

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
    pkill keepalived
    exit 1
fi
sleep 1
done

