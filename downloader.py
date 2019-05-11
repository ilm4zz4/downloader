#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-
"""
Created on Sun May  5 12:12:44 2019

@author: mrosellini
"""

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def runReq(path):
    
    import requests

    url = 'https://' + host_name + path
    return requests.get(url, auth=(user_name, password), verify=True)
    
     

def getUsers():
    
    from lxml import html
    
    response = runReq('/')
    
    tree = html.fromstring(response.content)
    
    parsed = tree.xpath('////tr/td//a//text()')
    
    users = [x.strip().replace('/','') for x in parsed ]
   
    return users
    
def getUserFile(user,folder = ''):
    
    import re
    from lxml import html
    response = runReq('/' + user + '/' + folder)
    
    tree = html.fromstring(response.content)
    
    parsed = tree.xpath('////tr/td//text()')
   

    cleaned = [x.strip() for x in parsed if x != 'Parent Directory' and x.strip() != '-' and  x.strip() ]
  
    files = list()
    i = 0
    while i <  len(cleaned)-1:
        
        files.append(cleaned[i])
        files.append(cleaned[i+1])
        
        if re.search('/',cleaned[i]): #Is folder?
            i=i+2 #I have not file size
        else:
            i=i+3
        
        
    result_dict = {files[i]:files[i+1] for i in range(0, len(files), 2)}
    
    return result_dict


def findElems(user,elems):
    filesList = list()
    for elem in elems:
    
        import re
       
        if re.search('/', elem):
            #print('==> directory : ' + elem)
            filesDict = findElems(user, getUserFile(user, elem ))
            for dic in filesDict:
                for key in dic:
                    filesList.append({str(elem) + key: dic[key]})
                
            
        else:
            filesList.append({elem : elems[elem]})
            
    return filesList

def createPath(filename):
    import os
    import errno

    
    if not os.path.exists(os.path.dirname(filename)):
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

def download(output_path,request):
    import re

    if not re.search('mp4',request):
        file = runReq(request)
        with open (output_path, 'wb') as f:
            f.write(file.content)
    else:
        if mp4file:
            file = runReq(request)
            with open (output_path, 'wb') as f:
                f.write(file.content)
        else:
            print (bcolors.WARNING + "\t ===> The file " + request.split('/')[-1] + " has NOT been downloaded" + bcolors.ENDC)
# --------------------------
  
import argparse

parser = argparse.ArgumentParser(description='Downloader file')

parser.add_argument('-p',      action="store",      dest='password',  default=False,         help='passwor')
parser.add_argument('-u',      action="store",      dest='user_name', default=False,         help='user_name')
parser.add_argument('-H',      action="store",      dest='host_name', default=False,         help='host_name')
parser.add_argument('-o',      action="store",      dest='path',      default='MasterStuff', help='Destination folder')
parser.add_argument('--mp4',   action="store_true", dest='mp4',       default=False,         help='Enable download mp4 file')

parser.add_argument('--version',  action='version',version=' 1.0')

results = parser.parse_args()
print ('password             =', results.password)
print ('user_name            =', results.user_name)
print ('host_name            =', results.host_name)
print ('mp4 download         =', results.mp4)
print ('destination folder   =', results.path)  
print ("")
password = results.password
user_name = results.user_name
host_name = results.host_name
mp4file = results.mp4
path = results.path

#To Switch Multi user - Single user
###########################
usersFiles = dict()
people = getUsers()

#user = 'marco.avvenuti'
#elems = getUserFile(user)
#usersFiles[user] = findElems(user , elems)
##########################

for user in people:
    print ('######## ' + user + "###########")
    elems = getUserFile(user)
    usersFiles[user] = findElems(user , elems)



import json
with open('json-curr.json','w') as f:
    f.write(json.dumps(usersFiles))
    

last=''
try:
    file = 'json-last.json'
    with open(file, 'r') as l:
        last = eval(l.read())
except IOError:
        last = '{}'
        print ('The file:' + file  + ' is not present yet')
    
    
from jsondiff import diff

difftext = diff(last, usersFiles)
#print ("#===> " , json.dumps(str(difftext), indent=4, sort_keys=True))



for user in difftext: #update, inserted
    
    if str(user) == '$replace': #ADD content
        for user_ in difftext[user]:
            print ("Start Download for user: "  ,user_) 
            for r in difftext[user][user_]:
                
                filename = list(eval(str(r)).keys())[0]
                output_path = path + '/' + user_ + '/' + filename
                request = '/' + user_ + '/' + filename
                print ("\tDownload " + filename)
                createPath(output_path)
                download(output_path,request)
        continue
    
    else:
        print ("Start Download for user: "  ,user)     
        
    for ctrl in difftext[user]: #Update content
        if ctrl == 'insert':
           ctrl=difftext[user][ctrl][0][1]
       
        filename = list(eval(str(ctrl)).keys())[0]
        output_path = path + '/' + user + '/' + filename
        request = '/' + user + '/' + filename
        print ("\tDownload " + filename)
        createPath(output_path)
        file = runReq(request)
        download(output_path,request)
        
if difftext:
    
    with open('json-last.json','w') as f:
        f.write(json.dumps(usersFiles))
else:
    print ("No updates to be performed")
           
