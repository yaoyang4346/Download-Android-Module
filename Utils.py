from urllib import request
from bs4 import BeautifulSoup
from retrying import retry
import os
import time
import random
class Utils(object):
    SUCCESS_CODE = 200
    ERROR = "err"
    BaseUrl = "https://www.androidos.net.cn"
    Size = '-'
    DEBUG = True

    @retry(stop_max_attempt_number = 3,wait_fixed = 3000)
    def opneUrl(self,url):
        with request.urlopen(url,None,10) as response:
            if response.getcode() == self.SUCCESS_CODE:
                return [True, url, response.read().decode('utf-8')]
            else:
                raise Exception

    def getHtml(self,url):
        try:
            return self.opneUrl(url)
        except Exception as e:
            self.err += 1
            self.log("Error! url = " + url + str(e))
            return [False, url, self.ERROR]

    def parase(self,html):
        if html[0]:
            try:
                soup = BeautifulSoup(html[2],"lxml")
                table = soup.find(self.getFileList)
                trs = table.find('tbody').find_all('tr')
                for tr in trs:
                    if len(tr.find_all('td')) > 2:
                        info = [True, tr.find(self.getName).a.string, tr.find(self.getSize).string != self.Size, self.BaseUrl+tr.find(self.getName).a['href']]
                        if info[2]:
                            info[3] = info[3].replace("xref","download")
                        self.stack.append(info)
            except Exception as e:
                self.err += 1
                self.log("Error! Parase fail ,url = " + html[1])
                self.stack.append([False,html[1]])
        else:
            self.stack.append([False,html[1]])

    def mkDirOrDownload(self):
        while len(self.stack) != 0:
            s = self.stack.pop()
            if s[0]:
                if s[2]:
                    filename = s[3].partition(self.module)[2]
                    self.log("download file : " + filename)
                    try:
                        self.download(s[3],filename)
                    except Exception as e:
                        self.err += 1
                        self.log("Error! download fail : url = " + s[3] + " " + str(e))
                else:
                    dirname = s[3].partition(self.module)[2]
                    self.log("mkdir : " + dirname)
                    os.mkdir(self.downDir + dirname)
                    self.parase(self.getHtml(s[3]))
        self.log("end!!! error = "+ str(self.err) + " time = " + str(time.time() - self.startTime))

    @retry(stop_max_attempt_number = 3,wait_fixed = 3000)
    def download(self,url,filename):
        with request.urlopen(url,None,10) as file:
            data = file.read()
            with open(self.downDir + filename, 'wb') as down:
                down.write(data)

    def getFileList(self,tag):
        return tag.name == 'table' and 'table' in tag['class'] and 'filelist' in tag['class'] and 'table-hover' in tag['class']

    def getName(self,tag):
        return tag.name == 'td' and 'content' in tag['class']

    def getSize(self,tag):
        return tag.name == 'td' and 'size' in tag['class']

    def log(self,info):
        if self.DEBUG:
            print(info)
            with open(self.downDir + self.logName, 'a') as log:
                log.write(info)
                log.write('\n')

    def run(self):
        self.parase(self.getHtml(self.url))
        self.mkDirOrDownload()

    def __init__(self,url,directory):
        self.startTime = time.time()
        self.err = 0
        self.stack = []
        self.url = url
        self.module = url.split('/').pop() + "/"
        self.downDir = directory + self.module
        self.logName = "log"+ str(random.uniform(10,20))[3:]
        try:
            os.mkdir(self.downDir)
        except Exception as e:
            print(e)
            exit(0)
