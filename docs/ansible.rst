########
Ansible Support
########

Here's how to use NSoT as a dynamic inventory for Ansible.

Ansible works against multiple systems in your infrastructure at the same time. It does this by selecting portions of systems listed in Ansible’s inventory file, which defaults to being saved in the location /etc/ansible/hosts. You can specify a different inventory file using the -i <path> option on the command line.

Basic Example
#############

```bash
ansible -i nsot.py -u ubuntu us-east-1d -m ping
```

Here are some examples shown from just calling the command directly::


A sample mocked Yaml file can be found in contrib/ansible/inventory/nsot.yaml
 ```
$ NSOT_INVENTORY_CONFIG=$PWD/test.yaml ansible_nsot --list | jq '.'
   {
     "routers": {
       "hosts": [
         "test1.example.com"
       ],
       "vars": {
         "cool_level": "very",
         "group": "routers"
       }
     },
     "firewalls": {
       "hosts": [
         "test2.example.com"
       ],
       "vars": {
         "cool_level": "enough",
         "group": "firewalls"
       }
     },
     "_meta": {
       "hostvars": {
         "test2.example.com": {
           "make": "SRX",
           "site_id": 1,
           "id": 108
         },
         "test1.example.com": {
           "make": "MX80",
           "site_id": 1,
           "id": 107
         }
       }
     },
     "rtr_and_fw": {
       "hosts": [
         "test1.example.com",
         "test2.example.com"
       ],
       "vars": {}
     }
   }

```

In order to only het the host named "test1":

$ NSOT_INVENTORY_CONFIG=$PWD/test.yaml ansible_nsot --host test1 | jq '.'
   {
      "make": "MX80",
      "site_id": 1,
      "id": 107
   }