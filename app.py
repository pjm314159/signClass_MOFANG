import time
from threading import Thread
import Launch
import configparser

class runApp(Launch.Launch):
    def __init__(self):
        Launch.Launch.__init__(self)
        self.interval = 30 # 等待时间请求数据
        self.after = 30  # 发现之后多久签到
        self.ifLogin = False
        self.isEnd = False
        self.configPath = "config.ini"
        self.locationParams = None
        self.defaultLocation = {"lat":113.393119,"lng":23.039277}
    def main(self):
        if not self.ifLogin:
            return # login
        c = self.signClass.signData() # get data
        check,data = self.search(c) # if you need to sign
        while not(check["gps"] or check["password"] or check["qrcode"] or check["rollCall"]):
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
        config = configparser.ConfigParser(
            allow_no_value=False,  # 是否允许无值的键
            comment_prefixes=('#', ';'),  # 注释符号
            inline_comment_prefixes=('#', ';'),  # 允许行内注释
            strict=True,  # 是否禁止重复的节或键
        )
        if not config.read(self.configPath):
            return None
        if config.has_section("location"):
            params = {"lat":config.get("location","lat"),"lng":config.get("location","lng")}
            self.locationParams.append(params)
        if config.has_section("settings"):
            if config.has_option("settings", "after"):
                self.after = config.getint("settings", "after")
            if config.has_option("settings", "interval"):
                self.interval = config.getint("settings", "interval")
        if not self.locationParams: # if empty
            self.locationParams.append(self.defaultLocation)

        return self.locationParams

    def sign(self,data):
        for i in range(len(data)):
            for j in data[i]["data"]["gps"]:
                if j["status"] == 1:  # 未签
                    print(f"gps[signId:{j["id"]}]:" + self.signClass.gpsSign(j["params"], j["gpsUrl"]))
                if j["status"] == -1: #  可能你以签过但又被管理员设为未签，又或者这次gps不设范围
                    # 尝试签到
                    if not self.locationParams:
                        print("gps无数据加载")
                    for p in self.locationParams:
                        j["params"]["lat"] = p["lat"]
                        j["params"]["lng"] = p["lng"]
                        message = self.signClass.gpsSign(j["params"], j["gpsUrl"])
                        if message == "我已签到过啦":
                            print(f"gps signId[{j["id"]}]:你已签过但又被管理员设为未签")
                        elif message == "签到成功":
                            print(f"gps signId[{j["id"]}]:{message}")
                            break

            for pwd_each_data in data[i]["data"]["password"]:
                if pwd_each_data["status"] == 1:
                    result = self.signClass.passwordSign(pwd_each_data["pwdUrl"])
                    if result == -1:  # 说明
                        pwd_each_data["status"] = -1
                        print(f"password signId[{pwd_each_data["id"]}]:你已签过但又被管理员设为未签")
                    else:
                        print(f"password signId[{pwd_each_data["id"]}]:{result}")
            for qr_each_data in data[i]["data"]["qrcode"]: # 二维码签到
                if qr_each_data["status"] == 1:  # 未签
                    for qr_location in self.locationParams:
                        result = self.signClass.qrcodeSign(qr_location, qr_each_data["qrUrl"])
                        if result == "签到成功":
                            print(f"qrcode signId[{qr_each_data["id"]}]:{result}")
                            break
                        elif result == "我已签到过啦":
                            print(f"qrcode signId[{qr_each_data["id"]}]:你已签过但又被管理员设为未签")
                        else:
                            print(f"qrcode signId[{qr_each_data["id"]}]:{result}")
            for roll_call_each_data in data[i]["data"]["readName"]:
                if roll_call_each_data["status"] == 1:
                    for roll_call_location in self.locationParams:
                        result = self.signClass.rollCallSign(roll_call_location, roll_call_each_data["rollCallUrl"])
                        if result == "签到成功":
                            print(f"roll call signId:{roll_call_each_data["id"]}:{result}")
                            break
                        elif result == "我已签到过啦":
                            print(f"roll call signId:{roll_call_each_data["id"]},你已签过但又被管理员设为未签")
                        else:
                            print(f"roll call signId:{roll_call_each_data["id"]},{result}")


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
        check = {"gps":False,"password":False,"qrcode":False,"rollCall":False}
        for i in range(len(data)): #检测到一个就跳出
            for j in data[i]["data"]["gps"]:
                if j["status"] == 1:
                    check["gps"] = True
                    break
                elif j["status"] == -1:
                    check["gps"] = True
                    break
            for l in range(len(data[i]["data"]["password"])):
                if data[i]["data"]["password"][l]["status"] == 1:
                    check["password"] = True
                    break
            for p in data[i]["data"]["qrcode"]:
                if p["status"] == 1:
                    check["qrcode"] = True
                    break
            for s in data[i]["data"]["readName"]:
                if s["status"] == 1:
                    check["rollCall"] = True
                    break
        return check,data
if __name__ == "__main__":
    c = runApp()
    c.loadLocation()
    c.register()
    c.main()
