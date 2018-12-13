import os
import requests
import datetime
from bs4 import BeautifulSoup
from pymongo import MongoClient

def Parse_patreon(user_id):
    result={}
    res=requests.get('https://www.patreon.com/'+user_id)
    if res.status_code==200:
        doc = BeautifulSoup(res.text, 'html.parser')
        rank_div=doc.select('div.sc-bZQynM.fJdsaR')
        if (rank_div[0].h6):
            result.update({'rank':rank_div[0].h6.text.replace(',','')})
        else:
            return False
        costP_div=doc.select('div.sc-bZQynM.fItbay')
        if (costP_div[0].h6):
            result.update({'cost':costP_div[0].h6.text[1:].replace(',','')})
        else:
            return False
    elif res.status_code==404:
        print('Patreon User_not_found')
        return False
    else:
        print('Patreon Request Error')
        return False
    return result

def ParseSubscribers(user_id):
    res=requests.get('https://socialblade.com/youtube'+user_id+'/realtime')
    if res.status_code==200:
        doc = BeautifulSoup(res.text, 'html.parser')
        count_p=doc.find("p", {"id": "rawCount"})
        if (count_p):
            return count_p.text
        else:
            return False
        
    elif res.status_code==404:
        print('ParseSubscibers Error - User_not_found')
        return False
    else:
        print('ParseSubscribers Error - Error')
        return False

def isMignight(offset):
    try:
        int_offset=int(offset)
    except:
        int_offset=0
    
    userTime= datetime.datetime.utcnow()+datetime.timedelta(hours=int_offset)
    if userTime.hour==0:
        return True
    elif userTime.hour==23:
        if userTime.minute>50:
            return True
    elif userTime.hour==1:
        if userTime.minute<10:
            return True
    else:
        return False

def processData():
    mongo_url=os.environ.get('MONGODB_URI',False)
    if not mongo_url:
        print('Python Script running in test mode')
        mongo_url='mongodb://heroku_d51wj820:9hvc7hpct55s3b7a89hf53n53v@ds127624.mlab.com:27624/heroku_d51wj820'
    client = MongoClient(mongo_url)
    db = client.heroku_zvgjdqnx
    users =db.users
    for user in users.find():
        patreon_login=user.get('patreonLogin',False)
        socialblade_login=user.get('socialbladeID',False)
        if patreon_login and socialblade_login:
            patreonData=Parse_patreon(patreon_login)
            if isMignight(user.get('timezone')):
                m_liveData=ParseSubscribers(socialblade_login)
                if patreonData and m_liveData:
                    users.update({'_id':user['_id']},{"$set": {'mignightSubscribers':m_liveData,
                                                               'patreonRank':patreonData['rank'],
                                                               'patreonCost':patreonData['cost']}})
                else:
                    print('Parse Error')
            else:
                if patreonData:
                    users.update({'_id':user['_id']},{"$set": {'patreonRank':patreonData['rank'],
                                                               'patreonCost':patreonData['cost']}})
        else:
            print('Batch Error! No Patreon Login Found')


processData()
