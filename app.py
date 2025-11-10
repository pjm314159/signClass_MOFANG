import time
from random import uniform
from threading import Thread
import Launch

class runApp(Launch.Launch):
    def __init__(self):
        Launch.Launch.__init__(self)
        self.interval = 30 # 等待时间请求数据
        self.after = uniform(30,50)# 发现之后多久登录
        self.ifLogin = False
        self.isEnd = False
    def main(self):
        if not self.ifLogin:
            self.register() # login
        c = self.signClass.signData() # get data
        check,data = self.search(c) # if you need to sign
        while not(check["gps"] or check["password"]):
            print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),"check:NONE")
            if self.isEnd:
                print("end")
                return
            time.sleep(self.interval)
            c = self.signClass.signData()
            check, data = self.search(c)
        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "check:find data")
        time.sleep(self.after)
        self.sign(data)

    def sign(self,data):
        gpsNumber = 0
        passwordNumber = 0
        for i in range(len(data)):
            for j in data[i]["data"]["gps"]:
                if j["status"] == 1:  # 未签
                    gpsNumber += 1
                    print("gps:" + self.signClass.gpsSign(j["params"], j["gpsUrl"]))
            for l in range(len(data[i]["data"]["password"])):
                if data[i]["data"]["password"][l]["status"] == 1:
                    passwordNumber += 1
                    result = self.signClass.passwordSign(data[i]["data"]["password"][l]["pwdUrl"])
                    if result == -1:  # 说明
                        data[i]["data"]["password"][l]["status"] = -1
                    else:
                        print("password:" + self.signClass.passwordSign(data[i]["data"]["password"][l]["pwdUrl"]))
        if gpsNumber == 0:
            print("gps无可签到")
        if passwordNumber == 0:
            print("password无可签到")

    def register(self):
        self.signClass.createSession()
        self.signClass.saveQrcode()
        self.p = Thread(target=self.signClass.login)
        self.p.start()
        self.showUI()
        if self.p.is_alive():
            print("you don't have permission")
            return None
        self.ifLogin = True

    def search(self,data):
        check = {"gps":False,"password":False}
        for i in range(len(data)):
            for j in data[i]["data"]["gps"]:
                if j["status"] == 1:
                    check["gps"] = True
            for l in range(len(data[i]["data"]["password"])):
                if [i]["data"]["password"][l]["status"] == 1:
                    result = self.signClass.passwordSign(data[i]["data"]["password"][l]["pwdUrl"])
                    if result == -1:
                        data[i]["data"]["password"][l]["status"] = -1
                    else:
                        check["password"] = True
        return check,data
if __name__ == "__main__":
    c = runApp()
    c.register()
    c.main()
