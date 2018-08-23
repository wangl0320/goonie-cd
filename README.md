# goonie-cd

edit inventories hosts 
goonie-mng label hosts install  mysql goonie-mng goonie-em
goonie-em lable hosts install goonie-em

ansible-playbook -i inventories/test204 goonie.yml -e @inventories/test204/group_vars/goonie.yml goonie.yml --tags install,importdb

