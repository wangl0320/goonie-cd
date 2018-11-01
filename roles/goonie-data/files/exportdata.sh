#!/bin/bash
#Virtual IP
vip="http://192.168.108.30:8090"
#first mng ip
mngip1="192.168.108.21"
#second mng ip
mngip2="192.168.108.22"

token=`curl -X POST -i $vip/mng/j_spring_security_check_kxapi  -H "Content-Type: application/x-www-form-urlencoded" -d "j_username=admin&j_password=c3284d0f94606de1fd2af172aba15bf3"|grep "X_AUTH_TOKEN:"|awk -F':' '{print $2}'`
curl -i -X POST $vip/mng/host/registToMng -H "X_AUTH_TOKEN: ${token}" -H 'Content-Type: application/json' -d "{ipAddress:'$mngip1',description:'some description'}"
curl -i -X POST $vip/mng/host/registToMng -H "X_AUTH_TOKEN: ${token}" -H 'Content-Type: application/json' -d "{ipAddress:'$mngip2',description:'some description'}"
