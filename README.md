# goonie-cd

edit inventories hosts 
goonie-mng label hosts install  mysql goonie-mng goonie-em
goonie-em lable hosts install goonie-em

ansible-playbook -i inventories/test204 goonie.yml -e "BACKUP=true" -e "INSTALL=true" -e "RESTART=true" -e "IMPORT_DB=false"
ansible-playbook -i inventories/test204 goonie.yml -e "ROLLBACK=true"

