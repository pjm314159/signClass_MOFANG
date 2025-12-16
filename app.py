from time import time
from threading import Thread,Event
import Launch
import configparser
from logger import info, warning, error, debug

class runApp(Launch.Launch):
    def __init__(self):
        Launch.Launch.__init__(self)
        self.interval = 30 # 等待时间请求数据
        self.after = 30  # 发现之后多久签到
        self.ifLogin = False
        self.stop_event = Event()
        self.configPath = "config.ini"
        self.configPathEncoding = "utf-8"
        self.locationParams = None
        self.defaultLocation = {"lat":113.393119,"lng":23.039277}
    def main(self):
        if not self.ifLogin:
            return # login
        c = self.signClass.signData() # get data
        check,data = self.search(c) # if you need to sign
        while not(check["gps"] or check["password"] or check["qrcode"] or check["rollCall"]):
            info("check:NONE")
            if self.stop_event.wait(self.interval):
                info("end")
                return
            c = self.signClass.signData()
            check, data = self.search(c)
        info("check:find data")
        if self.stop_event.wait(self.after):
            warning("force quit in waiting for sign")
            return
        self.sign(data)
    def readConfig(self):
        config = configparser.ConfigParser(
            allow_no_value=False,  # 是否允许无值的键
            comment_prefixes=('#', ';'),  # 注释符号
            inline_comment_prefixes=('#', ';'),  # 允许行内注释
            strict=True,  # 是否禁止重复的节或键
            interpolation=None #禁用插值
        )
        with open('config.ini', 'r', encoding=self.configPathEncoding) as file:
            content = file.read()
            config.read_string(content)
        return config
    def loadLocation(self,config):
        self.locationParams = []

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
    def save_cookies(self, cookies,config):
        info("save user login data")
        if not config.has_section("user"):
            config.add_section('user')
        for cookie in cookies:
            if "remember_student" in cookie.name:
                config.set("user", cookie.name,cookie.value)
                config.set("user","expires",str(cookie.expires))
        with open(self.configPath, "w", encoding=self.configPathEncoding) as f:
            config.write(f)
    def sign(self,data):
        for i in range(len(data)):
            for j in data[i]["data"]["gps"]:
                if j["status"] == 1:  # 未签
                    result = self.signClass.gpsSign(j["params"], j["gpsUrl"])
                    info(f"gps[signId:{j['id']}]:{result}")
                if j["status"] == -1: #  可能你以签过但又被管理员设为未签，又或者这次gps不设范围
                    # 尝试签到
                    if not self.locationParams:
                        warning("gps无数据加载")
                    for p in self.locationParams:
                        j["params"]["lat"] = p["lat"]
                        j["params"]["lng"] = p["lng"]
                        message = self.signClass.gpsSign(j["params"], j["gpsUrl"])
                        if message == "我已签到过啦":
                            info(f"gps signId[{j['id']}]:你已签过但又被管理员设为未签")
                        elif message == "签到成功":
                            info(f"gps signId[{j['id']}]:{message}")
                            break

            for pwd_each_data in data[i]["data"]["password"]:
                if pwd_each_data["status"] == 1:
                    result = self.signClass.passwordSign(pwd_each_data["pwdUrl"])
                    if result == -1:  # 说明
                        pwd_each_data["status"] = -1
                        info(f"password signId[{pwd_each_data['id']}]:你已签过但又被管理员设为未签")
                    else:
                        info(f"password signId[{pwd_each_data['id']}]:{result}")
            for qr_each_data in data[i]["data"]["qrcode"]: # 二维码签到
                if qr_each_data["status"] == 1:  # 未签
                    for qr_location in self.locationParams:
                        result = self.signClass.qrcodeSign(qr_location, qr_each_data["qrUrl"])
                        if result == "签到成功":
                            info(f"qrcode signId[{qr_each_data['id']}]:{result}")
                            break
                        elif result == "我已签到过啦":
                            info(f"qrcode signId[{qr_each_data['id']}]:你已签过但又被管理员设为未签")
                        else:
                            info(f"qrcode signId[{qr_each_data['id']}]:{result}")
            for roll_call_each_data in data[i]["data"]["readName"]:
                if roll_call_each_data["status"] == 1:
                    for roll_call_location in self.locationParams:
                        result = self.signClass.rollCallSign(roll_call_location, roll_call_each_data["rollCallUrl"])
                        if result == "签到成功":
                            info(f"roll call signId:{roll_call_each_data['id']}:{result}")
                            break
                        elif result == "我已签到过啦":
                            info(f"roll call signId:{roll_call_each_data['id']},你已签过但又被管理员设为未签")
                        else:
                            info(f"roll call signId:{roll_call_each_data['id']},{result}")

    def origin_register(self,config):
        info("init register")
        self.signClass.saveQrcode()
        self.p = Thread(target=self.signClass.login)
        self.p.start()
        self.showUI()
        if self.p.is_alive():
            warning("you don't have permission")
            self.signClass.Y = True
            return None
        self.save_cookies(config=config, cookies=self.signClass.r.cookies)
    def register(self,config):

        self.signClass.createSession()
        if config.has_section("user"):
            for i in config.items("user"):
                if "remember_student" in i[0]:
                    name = i[0]
                    value = i[1]
                if "expires" == i[0]:
                    if time() >int(i[1]):
                        if not self.origin_register(config):
                            info("cookie expired outdate")
                            self.ifLogin = True
                            return
            info("find user login data")
            self.signClass.r.cookies.update({name:value})
        else:
            if not self.origin_register(config):
                info("create user login data")
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
    config = c.readConfig()
    c.loadLocation(config)
    c.register(config)
    c.main()
