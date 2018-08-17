#!/usr/bin/python2.7

""" 
1.before run this script ,em and mng process should run,
2.run this script in mng node,
3.run like python supple.py
"""

import os
import logging
import argparse
import paramiko
import socket
import sys
import subprocess
import MySQLdb
import StringIO
import re
import time
import netifaces
from netaddr import IPNetwork
import netifaces as ni
from netaddr import *
import base64

sysCharType = sys.getfilesystemencoding()


root_user='root'
root_passwd='kx!@#890'
#root_passwd='ubuntu'
servers=['192.168.108.193','192.168.108.194','192.168.108.195']
#servers=['192.168.109.248','192.168.109.249','192.168.109.250','192.168.109.251','192.168.109.252','192.168.109.253']
#servers=['192.168.108.193','192.168.108.194','192.168.108.195']

mysql_server='127.0.0.1'
#clear_mysql=True 	#use for clear mysql tables, True or False
clear_mysql=True 	#use for clear mysql tables, True or False
cloud_ip=100 		#100 for cloud1 , 200 for cloud2 , 300 for cloud3....
goonie_user='goonie_db'
goonie_passwd='kx_goonie_#$%'
cetusfs_cloud = 'cluster1'




logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='/var/log/supple.log',
                    filemode='a')
LOG = logging.getLogger(__name__)



def remote_execute(cmd,ip):
    global root_user,root_passwd
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip,22,root_user,root_passwd,timeout=5)
    stdin,stdout,stderr=ssh.exec_command(cmd)
    ret={}
    ret['out']= stdout.read()
    ret['err']= stderr.read()
    ssh.close()
    return ret

def execute(cmdStr,executable='/bin/sh' ):
    # return out.code,out.stdout,out.stderr
    out=subprocess.Popen(cmdStr,shell=True,executable=executable,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    v_out=out.communicate()
    v_a=StringIO.StringIO()
    v_b=StringIO.StringIO()
    out_list=[]
    #for i in v_out:
    v_a.write(v_out[0])
    v_a.seek(0)
    out_list.append(v_a)
    v_b.write(v_out[1])
    v_b.seek(0)
    out_list.append(v_b)
    return out.poll(), out_list[0], out_list[1]


def mng_ip():
    _value,_out,_err=execute('ip addr')
    return _out.read()

def get_uuid(server):
    _cmd='cat /opt/goonie-EM/webapps/ROOT/WEB-INF/conf/em.properties'
    _result=remote_execute(_cmd,server)
    uuid=re.findall('^uuid=.*',_result['out'],re.M)[0].split('=')[1]
    return uuid

def get_license(server):
    _cmd='/usr/local/sbin/neucli3 license get'
    _result=remote_execute(_cmd,server)
    _result_list=_result['out'].split('\n')
    key_str=_result_list[5]
    _time=_result_list[1]
    e_time=_time[:4]+'-'+_time[4:6]+'-'+_time[6:8]+' '+_time[9:11]+':'+_time[11:13]+':'+_time[13:]
    expiration_time=e_time
    return key_str,expiration_time

def get_diskids(server):
    _cmd='/usr/local/sbin/neucli3 disk usablelist'
    _result=remote_execute(_cmd,server)
    _result_list=_result['out'].split('\n')
    disks_list=_result_list[1:]
    if len(disks_list)>0: 
        disks_idlist=[] 
        disksid_list=[i.split()[0] for i in disks_list if len(i.split())> 1] 
        for i in disksid_list:
            v_cmd='/usr/local/sbin/neucli3 volume diskCheck volType=1 disk=%s' %str(i)
            _result=remote_execute(v_cmd,server)
            if _result['out'].split()[0]=='true':
                disks_idlist.append(i)
    else:
        disks_idlist=[]
    return disks_idlist

def get_device_info(server):
    _cmd='/usr/local/sbin/neucli3 device info'
    _result=remote_execute(_cmd,server)
    _result_list=_result['out'].split('\n')
    hostname=_result_list[8]
    capacity_total=_result_list[3]
    capacity_used=_result_list[4]
    ipmi_ip=_result_list[7]
    hardware_identity=_result_list[6]
    sn=_result_list[5]
    return hostname,capacity_total,capacity_used,ipmi_ip,hardware_identity,sn

def clear_tables(tables_list):
    global goonie_passwd
    mydb = MySQLdb.connect(mysql_server, goonie_user,goonie_passwd,'goonie_prod')
    LOG.info(mydb)
    for i in tables_list:
        cur1 = mydb.cursor()
        delete_sql="delete from %s " %i
        _result=cur1.execute(delete_sql)
        cur1.close()
        mydb.commit()
    mydb.close()
    return True

def insert_db(table,value_dict):
    global goonie_passwd
    mydb = MySQLdb.connect(mysql_server, goonie_user,goonie_passwd,'goonie_prod')
    LOG.info(mydb)
    cur1 = mydb.cursor()
    insert="INSERT INTO %s (" %table
    values=" VALUES ("
    for i in value_dict.keys():
        insert=insert+str(i)+', '
        values=values+str(value_dict[i])+', '
    insert_sql=insert[:-2]+') '+values[:-2]+');'
    LOG.info(insert_sql)
    print insert_sql
    _result=cur1.execute(insert_sql)
    cur1.close()
    mydb.commit()
    mydb.close()
    return True

def update_db(table, dict1, dict1_value, condition_dict, condition_dict_value):
    global goonie_passwd
    mydb = MySQLdb.connect(mysql_server, goonie_user,goonie_passwd,'goonie_prod')
    LOG.info(mydb)
    cur1 = mydb.cursor()
    update_sql = "update %s set %s=\"%s\" where %s=%d" %(table, dict1, dict1_value, condition_dict, condition_dict_value) 
    _result=cur1.execute(update_sql)
    cur1.close()
    mydb.commit()
    mydb.close()
    return True

def update_sequence():
    global goonie_passwd
    mydb = MySQLdb.connect(mysql_server, goonie_user,goonie_passwd,'goonie_prod')
    LOG.info(mydb)
    cur1 = mydb.cursor()
    update_sql='update sequence set `current_value`=11000;'
    _result=cur1.execute(update_sql)
    cur1.close()
    mydb.commit()
    mydb.close()
    return True

def select_h_device_ids():
    global goonie_passwd
    mydb = MySQLdb.connect(mysql_server, goonie_user,goonie_passwd,'goonie_prod')
    cur1 = mydb.cursor()
    select_sql='select id from h_device;'
    _result=cur1.execute(select_sql)
    results=cur1.fetchall()
    mydb.close()
    return [i[0] for i in results]

def select_h_device_ips():
    global goonie_passwd
    mydb = MySQLdb.connect(mysql_server, goonie_user,goonie_passwd,'goonie_prod')
    cur1 = mydb.cursor()
    select_sql='select id,ip_address from h_device;'
    _result=cur1.execute(select_sql)
    results=cur1.fetchall()
    mydb.close()
    return results

def select_c_cluster_node(_node_id):
    global goonie_passwd
    mydb = MySQLdb.connect(mysql_server, goonie_user,goonie_passwd,'goonie_prod')
    cur1 = mydb.cursor()
    select_sql='select cluster_id from c_cluster_node where node_id=%s;' %_node_id
    _result=cur1.execute(select_sql)
    results=cur1.fetchall()
    mydb.close()
    if len(results)>0:
        return int([i[0].to_eng_string() for i in results][0])
    else:
        return False

def select_nodeid_cluster_node():
    global goonie_passwd
    mydb = MySQLdb.connect(mysql_server, goonie_user,goonie_passwd,'goonie_prod')
    cur1 = mydb.cursor()
    select_sql='select node_id from c_cluster_node;'
    _result=cur1.execute(select_sql)
    results=cur1.fetchall()
    print results
    mydb.close()
    if len(results)>0:
        return [int(i[0].to_eng_string()) for i in results]
    else:
        return []



class supple():
    def update_c_storage(self):
        cluster_id=select_c_cluster_node(cloud_ip)
        if cloud_ip%100==0 and cluster_id==False:
            _id=cloud_ip+5
            c_storage={     'id':_id,
                            'cluster_name':'"'+cetusfs_cloud+'"',
                            'cluster_type': 1,
                            'neustor_pool_type': 1,
                            'description':'"'+' '+'"',
                            'create_time':'"'+time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())+'"',
                            'update_time':'"'+time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())+'"',
                        }
            insert_db('c_storage',c_storage)
        return True
    def update_h_device(self):
        j=1
        _mng_ip=mng_ip()
        for i in servers:
            _id=cloud_ip+j
            j=j+1
            _uuid=get_uuid(i)
            if i in _mng_ip:
                device_role_num=3
            else:
                device_role_num=1
            hostname,capacity_total,memory_total,ipmi_ip,hardware_identity,sn=get_device_info(i)
            capacity_used=0
            h_device={  'id':                   _id,
                        'uuid':                 '"'+str(_uuid)+'"',
                        'hostname':             '"'+str(hostname)+'"',
                        'ip_address':            '"'+str(i)+'"',
                        'port':                 8091,
                        'model':                 '"'+str('-')+'"',
                        'chassis_type':         '"'+str( '-')+'"',
                        'capacity_total':        '"'+str(capacity_total)+'"',
                        'capacity_used':        capacity_used,
                        'memory_total':          '"'+str(memory_total)+'"', 
                        'device_status':         '"'+str('online')+'"', 
                        'online':               1, 
                        'compress':             1, 
                        'deduplication':        1, 
                        'thin':                 1, 
                        'description':           '"'+str(' ')+'"', 
                        'read_only':            0, 
                        'ipmi_ip':               '"'+str(ipmi_ip)+'"', 
                        'cabinet_id':           0, 
                        'cabinet_x':             '"'+str(' ')+'"', 
                        'cabinet_y':            0, 
                        'service_role':         0, 
                        'storage_role':         '1', 
                        'device_role_num':      device_role_num, 
                        'hardware_identity':     '"'+str(hardware_identity)+'"', 
                        'sn':                    '"'+str(sn)+'"', 
                        'data_ip':               '"'+str(i)+'"',
                    }
            insert_db('h_device',h_device)
        return True
    def update_c_cluster_node(self):
        for i in select_h_device_ids():
            if str(i)[:1]==str(cloud_ip)[:1]:
                _id=select_c_cluster_node(cloud_ip)
                if cloud_ip%100==0 and _id==False:
                    _id=cloud_ip+5
                if i not in select_nodeid_cluster_node():
                    c_cluster_node={'cluster_id':_id,
                                    'node_id':'"'+str(i)+'"',
                            }
                    insert_db('c_cluster_node',c_cluster_node)
        return True
    def update_c_stor_neus_pool(self):
        _id=cloud_ip+1
        cluster_id=cloud_ip+5
        #cluster_id=#select_c_cluster_node(cloud_ip)
        if cloud_ip%100==0:#and cluster_id==False:
            c_stor_neus_pool={  'id':_id, 
                                'pool_name':'"'+str('distributed filesystem storage pool')+'"', 
                                'pool_type':1, 
                                'cluster_id':cluster_id, 
                                'compress':0, 
                                'deduplication':0,
                                'thin':0, 
                                'red_mode':0,
                                'duplication_num':0, 
                                'total':0, 
                                'redundancy':0
                    }
            insert_db('c_stor_neus_pool',c_stor_neus_pool)
        return True
    def update_c_pool_disk(self):
        j=1
        for i in servers:
            _id=cloud_ip+j
            j=j+1
            d_id = _id
            for ip in select_h_device_ips():
                if i == ip[1]:
                    d_id = ip[0]
            disk_ids=get_diskids(i)
            for m in disk_ids:
                _id=cloud_ip+1
                c_pool_disk={   'pool_id':_id, 
                                'device_id':'"'+str(d_id)+'"', 
                                'disk_id':'"'+str(m)+'"', 
                                'status':0, 
                                'create_time':'"'+str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))+'"', 
                                'update_time':'"'+str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))+'"',
                        }
                insert_db('c_pool_disk',c_pool_disk)
        return True
    def update_h_license(self):
        j=1
        for i in servers:
            _id=cloud_ip+j
            j=j+1
            key_str,expiration_time=get_license(i)
            h_license={ 'id':'"'+str(_id)+'"', 
                        'device_id':'"'+str(_id)+'"', 
                        'key_str':'"'+str(key_str)+'"', 
                        'expiration_time':'"'+str(expiration_time)+'"', 
                        'device_feature':7, 
                        'service_feature':3, 
                        'storage_feature':3
                    }
            insert_db('h_license',h_license)
        return True
    def update_sequence(self):
        update_sequence()
        return True

    def close_performance(self):
        update_db('customconf', 'configvalue', 'false', 'id', 520)

    @classmethod
    def supple(cls):
        tables_list=['c_storage','c_stor_neus_pool','h_device','c_cluster_node','c_pool_disk','h_license']
        if clear_mysql:
            clear_tables(tables_list)
        cls().update_c_storage()
        cls().update_h_device()
        cls().update_c_cluster_node()
        cls().update_c_stor_neus_pool()
        cls().update_c_pool_disk()
        cls().update_h_license()
        cls().update_sequence()
        cls().close_performance()
        return True


if __name__=='__main__':
    supple.supple()
