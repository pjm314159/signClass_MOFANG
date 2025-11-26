import time
from random import uniform
from threading import Thread
import Launch
import configparser

class runApp(Launch.Launch):
    def __init__(self):
        Launch.Launch.__init__(self)
        self.interval = 30 # 等待时间请求数据
        self.after = 0.1# uniform(30,50)# 发现之后多久登录
        self.ifLogin = False
        self.isEnd = False
        self.configPath = "config.ini"
        self.locationParams = None
    def main(self):
        if not self.ifLogin:
            return # login
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
    def loadLocation(self):
        self.locationParams = []
        config = configparser.ConfigParser()
        if config.read(self.configPath):
            for section in config.sections():
                params = {"lat":config[section]["lat"],"lng":config[section]["lng"]}
                self.locationParams.append(params)
                return self.locationParams
        else:
            return None
    def sign(self,data):
        for i in range(len(data)):
            for j in data[i]["data"]["gps"]:
                if j["status"] == 1:  # 未签
                    print(f"gps[signId:{j["id"]}]:" + self.signClass.gpsSign(j["params"], j["gpsUrl"]))
                if j["status"] == -1: #  可能你以签过但又被管理员设为未签，又或者这次gps不设范围
                    # 尝试签到
                    if not self.locationParams:
                        print("gps无数据加载")
                        self.locationParams = [{"lat":113.393119,"lng":23.039277}]
                    for p in self.locationParams:
                        j["params"]["lat"] = p["lat"]
                        j["params"]["lng"] = p["lng"]
                        message = self.signClass.gpsSign(j["params"], j["gpsUrl"])
                        if message == "我已签到过啦":
                            print(f"signId:{j["id"]},你已签过但又被管理员设为未签")
                        elif message == "签到成功":
                            print(f"signId:{j["id"]},{message}")
                            break

            for l in range(len(data[i]["data"]["password"])):
                if data[i]["data"]["password"][l]["status"] == 1:
                    result = self.signClass.passwordSign(data[i]["data"]["password"][l]["pwdUrl"])
                    if result == -1:  # 说明
                        data[i]["data"]["password"][l]["status"] = -1
                    else:
                        print("password:" + self.signClass.passwordSign(data[i]["data"]["password"][l]["pwdUrl"]))
    def register(self):
        self.signClass.createSession()
        self.signClass.saveQrcode()
        self.p = Thread(target=self.signClass.login)
        self.p.start()
        self.showUI()
        if self.p.is_alive():
            print("you don't have permission")
            self.signClass.Y = True
            return None
        self.ifLogin = True

    def search(self,data):
        check = {"gps":False,"password":False}
        for i in range(len(data)):
            for j in data[i]["data"]["gps"]:
                if j["status"] == 1:
                    check["gps"] = True
                elif j["status"] == -1:
                    check["gps"] = True
            for l in range(len(data[i]["data"]["password"])):
                if data[i]["data"]["password"][l]["status"] == 1:
                    result = self.signClass.passwordSign(data[i]["data"]["password"][l]["pwdUrl"])
                    if result == -1:
                        data[i]["data"]["password"][l]["status"] = -1
                    else:
                        check["password"] = True
        return check,data
if __name__ == "__main__":
    c = runApp()
    c.loadLocation()
    c.register()
    c.main()
