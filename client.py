#!/usr/bin/env python  
#encoding=utf8
import threading
import time
from socket import *

import demjson as demjson

HOST = '192.168.1.101'
PORT = 9999
s = socket(AF_INET, SOCK_DGRAM)# AF_INET:ipv4  SOCK_DGRAM：UDP连接方式
s.connect((HOST, PORT)) #连接对方

messageList=[]
class TextMessage(object):
    def __init__(self,sendtime,type,content,fromuserid,touserid):
        self.fromuserid=fromuserid
        self.sendtime=sendtime #发送时间 用于区别
        self.type=type  #发送类型
        self.content=content #发送内容
        self.touserid=touserid

def sendMessage(message):
    if len(message)>0:
        s.sendall(message) #发送消息到服务器
    else:
        print("消息不能为空")

def recMessage():
    while True:
        data = s.recv(1024)
        data = str(data, encoding="utf8")
        jsonData = demjson.decode(data)
        if jsonData["type"]=="state":
            if jsonData["state"]=="overtime":
                print(jsonData["content"]+"发送超时")
            else:
                for messageItem in messageList:
                    if messageItem.sendtime==jsonData["time"]:
                        print(str(messageItem.content)+"   已发送成功")
                        # print(messageList)
                        messageList.remove(messageItem) #发送成功后将成功的消息从消息队列里面删除
                    # print(messageList)
        elif jsonData['type']=="login":
            print("登录成功")
        elif jsonData['type']=="text":
            print(jsonData["content"])
            sendContent = {}
            sendContent["fromuserid"] = 2
            sendContent["time"] = jsonData["time"]
            sendContent["type"] = "reply"
            sendContent["content"] = "success"
            sendContent["touserid"] = 1
            sendMessage(bytes(str(sendContent), encoding="utf8"))
        elif jsonData["type"]=="back":#被退回的消息
            print(jsonData["content"]+"发送失败")

def writeMessage():
    while True:
        message = input('send message:>>')
        textMessage = TextMessage(sendtime=int(time.time()), type="text", content=message, touserid=1,fromuserid=2)
        messageList.append(textMessage)
        sendContent={}
        sendContent["fromuserid"]=textMessage.fromuserid
        sendContent["time"]=textMessage.sendtime
        sendContent["type"]=textMessage.type
        sendContent["content"]=textMessage.content
        sendContent["touserid"]=textMessage.touserid
        sendMessage(bytes(str(sendContent),encoding="utf8"))

def login():
    sendContent = {}
    sendContent["fromuserid"] = 2
    sendContent["time"] =int(time.time())
    sendContent["type"] = "login"
    sendContent["content"] = "login"
    sendContent["touserid"] = 0
    sendMessage(bytes(str(sendContent), encoding="utf8"))

def startServer():
    login()
    writeThread=threading.Thread(target=writeMessage,name="writeThread",args=())
    writeThread.start()
    recThread=threading.Thread(target=recMessage,name="recThread",args=())
    recThread.start()

# s.close()
if __name__ == '__main__':
    startServer()