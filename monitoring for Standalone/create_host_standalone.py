#!/usr/bin/python
#-*- coding: utf-8 -*-

'''
'@file create_host_standalone.py
'@author liyunting
'@version 1
'@lastModify: 2019-01-13 19:44
'
'''

import json
import sys
import getopt
import requests


'''
'function: zabbix_call
'description: call zabbix web api by json-rpc
'parameter: payload        dict   the parameter to be passed  
'           zabbix_server  string the ip of zabbix server  
'return: the request response object  
'''
def zabbix_call(payload, zabbix_server):
	url = "http://" + zabbix_server + "/zabbix/api_jsonrpc.php"
	headers = {'content-type': 'application/json'}
	response = requests.post(url, data=json.dumps(payload), headers=headers).json()
	return response


'''
'function: zabbix_auth
'description: connect to zabbix server and authenticate
'parameter: user           string   the zabbix server username
'           pwd            string   the zabbix server password 
'           zabbix_server  string the ip of zabbix server  
'return: the authentication token
'''
def zabbix_auth(user, pwd, zabbix_server):
	auth = ''
	payload = {
	    "method": "user.login",
	    "params": {
	    	"user": user,
	    	"password": pwd
	    },
	    "jsonrpc": "2.0",
	    "id": 1,
	    "auth": None
	}
	res = zabbix_call(payload, zabbix_server) 
	if 'result' in res :
		auth = res['result']
	else:
		print(res['error'])
	return auth


'''
'function: zabbix_create_group
'description: connect to zabbix server and create host group
'parameter: auth           string   your authentication token
'           groupname      string   the name of the hostgroup
'           zabbix_server  string the ip of zabbix server  
'return:the host group id 
'''
def zabbix_create_group(auth, groupname, zabbix_server):
	host_group_id = ''
	if auth != '':
		#create host group
		payload = {
    		"jsonrpc": "2.0",
    		"method": "hostgroup.create",
    		"params": {
    		    "name": groupname
    		},
   	 		"auth": auth,
    		"id": 1
		}
		res = zabbix_call(payload, zabbix_server)
		if 'result' in res :
			host_group_id = res['result']['groupids'][0]
			print('Create hostgroup successfully')
		else:
			print(res['error'])
	return host_group_id


'''
'function: zabbix_import_template
'description: connect to zabbix server and import template
'parameter: auth          string   your authentication token
'           filepath      string   the whole path of the xml file(e.g. './example.xml')
'           zabbix_server string the ip of zabbix server  
'''
def zabbix_import_template(auth, filepath, zabbix_server):
	if auth != '':
		with open(filepath,'r') as f:
			content = f.read()
		payload = {
    		"jsonrpc": "2.0",
    		"method": "configuration.import",
    		"params": {
    		    "format": "xml",
    		    "rules": {
    		    	"applications": {
               			"createMissing": True,
               			"deleteMissing": False
           			},
    		        "templates": {
    		            "createMissing": True,
    		            "updateExisting": True
    		        },
    		        "screens": {
    		            "createMissing": True,
    		            "updateExisting": True
    		        },    		        
    		        "valueMaps": {
                		"createMissing": True,
                		"updateExisting": False
           			},
					"graphs": {
               			"createMissing": True,
               			"updateExisting": True,
               			"deleteMissing": True
           			},    			        
    		        "triggers": {
               			"createMissing": True,
               			"updateExisting": True,
               			"deleteMissing": True
           			},
    		        "items": {
               			"createMissing": True,
               			"updateExisting": True,
               			"deleteMissing": True
           			}
    		    },
    		    "source": content
    		},
    		"auth": auth,
    		"id": 1
		}
		res = zabbix_call(payload, zabbix_server)
		if 'result' in res :
			if res['result']:
				print('template import successfully')
		else:
			print(res['error'])


'''
'function: zabbix_get_template
'description: connect to zabbix server and get template
'parameter: auth          string   your authentication token
'           templatename  string   the name of the template
'           zabbix_server string the ip of zabbix server  
'return:the template id 
'''
def zabbix_get_template(auth, templatename, zabbix_server):
	template_id = ''
	if auth != '':
		payload = {
    		"jsonrpc": "2.0",
    		"method": "template.get",
    		"params": {
    		    "output": "extend",
    		    "filter": {
    		        "host": [
    		            templatename
    		        ]
    		    }
    		},
    		"auth": auth,
    		"id": 1
		}
		res = zabbix_call(payload, zabbix_server)
		if 'result' in res :
			template_id = res['result'][0]['templateid']
		else:
			print(res['error'])
	return template_id


'''
'function: zabbix_create_host
'description: create host and link template 
'parameter: auth          string    your authentication token
'           hostname      string    the name of the host
'           hostip        string    the ip of the host
'			host_group_id string    the id of group 
'			template_id   string    the id of template 
'           zabbix_server string the ip of zabbix server  
'''
def zabbix_create_host(auth, hostname, hostip, host_group_id, template_id, zabbix_server):
	host_id = ''
	if auth != '' and host_group_id != '':
		payload = {
		    "jsonrpc": "2.0",
		    "method": "host.create",
		    "params": {
		        "host": hostname,
		        "interfaces": [
		            {
		                "type": 1,
		                "main": 1,
		                "useip": 1,
		                "ip": hostip,
		                "dns": "",
		                "port": "10050"
		            }
		        ],
		        "groups": [
		            {
		                "groupid": host_group_id
		            }
		        ],
		        "templates": [
		            {
		                "templateid": template_id
		            }
		        ]		        
		    },
		    "auth": auth,
		    "id": 1
		}
		res = zabbix_call(payload, zabbix_server)
		if 'result' in res :
			host_id = res['result']['hostids'][0]
			print("create", hostname , "successfully")
		else:
			print(res['error'])


'''
'function: parseArg
'description: parse python command line arguments and return arguments
'parameter: argv   string  command line arguments 
'return: zabbix_server  string  the ip of zabbix server
'        zabbix_user    string  the user of zabbix, default: Admin
'        zabbix_pwd     string  password for user, default: zabbix
'        mongo_ip       string  the ip of mongo server
'''
def parseArg(argv):
	zabbix_user = 'Admin'
	zabbix_pwd = 'zabbix'
	zabbix_server = ''
	mongo_ip = ''
	try:
		opts, args = getopt.getopt(argv,"hz:u:p:m:",["help"])
	except getopt.GetoptError:
		print('invalid option\nplease use python create_host_standalone.py --help for more information\n')
		sys.exit(2)
	for opt, arg in opts:
		if opt in ('-h', '--help'):
			print('usage:\n  python create_host_standalone.py -z <zabbix_server_ip> -u <zabbix_user> -p <zabbix_password> -m <mongodb_ip>\n')
			print('  if no user and password input, then user:Admin and password:zabbix will be used by default')
			sys.exit()
		elif opt == '-z':
			zabbix_server = arg
		elif opt == '-u':
			zabbix_user = arg
		elif opt == '-p':
			zabbix_pwd = arg
		elif opt == '-m':
			mongo_ip = arg
	return zabbix_server, zabbix_user, zabbix_pwd, mongo_ip


# the main method
def main(argv):
	zabbix_server, user, pwd, mongo_ip = parseArg(argv)
	if zabbix_server == '' or mongo_ip == '':
		print('invalid input!\nplease check and use python create_host_standalone.py --help for more information\n')
		sys.exit(2)

	auth = zabbix_auth(user, pwd, zabbix_server)
	if auth == '':
		print('\nzabbix server authentication failed\n')
		sys.exit()

	#import template
	zabbix_import_template(auth, './mongo_standalone.xml', zabbix_server)
	template_id = zabbix_get_template(auth, 'Template DB MongoDB', zabbix_server)
	#create host group 'Mongodb Standalone'
	group_id = zabbix_create_group(auth, 'Mongodb Standalone', zabbix_server)
	if template_id != '' and group_id != '':
		#create host 'mongo_server' and link 'Template DB MongoDB'
		hostname = 'mongo_server'
		zabbix_create_host(auth, hostname, mongo_ip, group_id, template_id, zabbix_server)


if __name__ == '__main__':
	main(sys.argv[1:])
