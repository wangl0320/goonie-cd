# goonie-cd

edit inventories hosts 
goonie-mng label hosts install  mysql goonie-mng goonie-em
goonie-em lable hosts install goonie-em

ansible-playbook -i inventories/test204 goonie.yml --tags install,importdb,uninstall,data

