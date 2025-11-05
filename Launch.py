from main import signClass
from os import system
from threading import Thread
from showqrcode import QRLoginApp
import tkinter as tk
class Launch:
    def __init__(self):
        self.signClass = signClass()
        self.size = "600x600"
        self.root = tk.Tk()
    def launch(self):
        self.signClass.createSession()
        self.signClass.saveQrcode()
        self.p = Thread(target=self.signClass.login)
        self.p.start()
        self.showUI()
        if self.p.is_alive():
            print("you don't have permission")
            return None
        c = self.signClass.signData()
        gpsNumber = 0
        passwordNumber = 0
        for i in range(len(c)):
            for j in c[i]["data"]["gps"]:
                if j["status"] == 1: # 未签
                    gpsNumber += 1
                    print("gps:"+self.signClass.gpsSign(j["params"], j["gpsUrl"]))
                if j["status"] == -1:
                    print("gps:可能你以签过但又被管理员设为已签，又或者这次gps不设范围")
            for l in range(len(c[i]["data"]["password"])):
                if c[i]["data"]["password"][l]["status"] == 1:
                    passwordNumber += 1
                    result = self.signClass.passwordSign(c[i]["data"]["password"][l]["pwdUrl"])
                    if result == -1: # 说明
                        c[i]["data"]["password"][l]["status"] = -1
                    else:
                        print("password:"+self.signClass.passwordSign(c[i]["data"]["password"][l]["pwdUrl"]))
        if gpsNumber == 0:
            print("gps无可签到")
        if passwordNumber == 0:
            print("password无可签到")
    def checkClose(self):
        if not self.p.is_alive():
            self.root.destroy()
        else:
            self.root.after(500, self.checkClose)

    def showUI(self):
        self.root.geometry(self.size)
        QRLoginApp(self.root, self.signClass.imgPath)
        self.root.after(500, self.checkClose)
        self.root.attributes("-topmost", True)
        self.root.mainloop()

if __name__ == "__main__":
    try:
        app = Launch()
        app.launch()
    except Exception as e:
        print(e)
    #system("pause")