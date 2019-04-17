# root@python 513]# cat serverudp.py
# !/usr/bin/env python
import json
import threading
import time
from socket import *
import demjson
import simplejson as simplejson

HOST = '192.168.1.101'
PORT = 9999

s = socket(AF_INET, SOCK_DGRAM)
s.bind((HOST, PORT))
print('...waiting for message..')

OnlineUserList=[] #当前在线用户
MessageList=[] #消息列表

class Message(object):
    def __init__(self,sendtime,messagetime,fromuserid,touserid,type,content):
        self.sendtime=sendtime
        self.messagetime=messagetime
        self.fromuserid=fromuserid
        self.touserid=touserid
        self.content=content
        self.type=type

class OnlineUser(object):
    def __init__(self,userid,address):
        self.userid=userid
        self.address=address

def sendmeassage(message, address):
    s.sendto(message, address)

def sendMessageSate(state,time,address):
    responseContent = {}
    responseContent["type"] = state
    responseContent["time"] = time
    responseContent["state"] = "success"
    sendmeassage(bytes(str(responseContent), encoding="utf8"), address)

#判断用户id是否在线
def isUserOnline(userid):
    OnlineUserIDs=[]
    for OnlineUserItem in OnlineUserList:
        OnlineUserIDs.append(OnlineUserItem.userid)
    if userid in OnlineUserIDs:
        return True
    else:
        return False

def updateUserAddress(userid,address):
    for OnlineUserItem in OnlineUserList:
       if OnlineUserItem.userid==userid:
           OnlineUserItem.address=address

#根据用户id返回用户address
def getAddressByUserID(userid):
    #判断用户是否在线
    if isUserOnline(userid):
        for OnlineUserItem in OnlineUserList:
            if OnlineUserItem.userid == userid:
                return OnlineUserItem.address
    else:
        return False

#根据id将用户下线
def exitUser(userid):
    if isUserOnline(userid):
        for OnlineUserItem in OnlineUserList:
            if OnlineUserItem.userid == userid:
                OnlineUserList.remove(OnlineUserItem)

#判断消息发送后的时间延长机制
#1.将用户消息转发至对应用户之后计时 如果超时即代表对方未收到消息
def isMessageOverTime():#判断消息发送是否超时
    while True:
        time.sleep(3)
        nowTime=int(time.time())
        if len(MessageList)>0:
            for MessageItem in MessageList:
                if nowTime-MessageItem.sendtime>10:#超时 将消息反馈到发送的用户端
                    responseContent = {}
                    responseContent["type"] = "state"
                    responseContent["state"]="overtime"
                    responseContent["time"] = MessageItem.messagetime
                    responseContent["content"] = MessageItem.content
                    responseContent["touserid"]=MessageItem.touserid
                    exitUser(MessageItem.touserid)
                    sendmeassage(bytes(str(responseContent), encoding="utf8"),getAddressByUserID(MessageItem.fromuserid))  # 发送超时消息给用户
                    MessageList.remove(MessageItem)

#开启服务，接收客户端信息，并对消息进行转发和处理
def startServer():
    while True:
        data, address = s.recvfrom(1024) #接收客户端发送的数据
        data=str(data,encoding="utf8")
        sdata=demjson.decode(data)
        if sdata['type']=="login":
            #判断用户是否属于二次登录 需要更新缓存里面的address 不然会出现消息发出去无法接收的结果
            if isUserOnline(sdata["fromuserid"]):
                updateUserAddress(sdata["fromuserid"],address)
                print(str(sdata["fromuserid"]) + "更新了address")
            else:
                newUser=OnlineUser(sdata["fromuserid"],address)
                OnlineUserList.append(newUser) #将登录用户添加到在线用户列表
                print(str(sdata["fromuserid"])+"->登录成功")
                # print(OnlineUserList)
                sendMessageSate("login", sdata['time'], address)  # 回馈登录成功状态

        elif sdata["type"]=="exit":
            for OnlineUserItem in OnlineUserList:
                if OnlineUserItem.userid==sdata["fromuserid"]:
                    print(str(OnlineUserItem.userid)+"退出登录")
                    OnlineUserList.remove(OnlineUserItem)

        elif sdata["type"]=='reply': #来自客户端的消息确认信息
            print(str(sdata['fromuserid'])+"<-" +sdata["content"]+"发送成功")
            print(MessageList)
            for MessageItem in MessageList:
                if MessageItem.messagetime==sdata["time"]:
                    MessageList.remove(MessageItem)
            print(MessageList)
            sendMessageSate("state", sdata['time'], getAddressByUserID(sdata["touserid"]))  # 回馈此条消息发送状态

        else:
            #转发消息至对应的用户
            if sdata["touserid"] !=0: #发送给用户的消息
                if isUserOnline(sdata["touserid"]):
                    print("来自："+str(sdata["fromuserid"])+"的消息："+sdata["content"] +"发送至：" + str(sdata["touserid"]))
                    responseContent = {}
                    responseContent["type"] = sdata['type']
                    responseContent["time"] = sdata["time"]
                    responseContent["content"] = sdata["content"]
                    #将转发消息加入到消息队列，直到转发对象反馈接收成功消息或者超时
                    newMessage=Message(sendtime=int(time.time()),messagetime=sdata["time"],fromuserid=sdata["fromuserid"],touserid=sdata["touserid"],type=sdata["type"],content=sdata["content"])
                    MessageList.append(newMessage)
                    sendmeassage(bytes(str(responseContent), encoding="utf8"), getAddressByUserID(sdata["touserid"]))  # 发送消息给用户
                else:
                    responseContent = {}
                    responseContent["type"] ="state"
                    responseContent["state"] = "back"
                    responseContent["time"] = sdata["time"]
                    responseContent["content"] = sdata["content"]
                    sendmeassage(bytes(str(responseContent), encoding="utf8"),address)
                    print("来自：" + str(sdata["fromuserid"]) + "的消息：" + sdata["content"]+"发送失败：对方不在线")
    s.close()

if __name__ == '__main__':
    overtimeThread=threading.Thread(target=isMessageOverTime,name="overtimeThread",args=())
    overtimeThread.start()
    startServer() #启动服务




