from main import signClass
from os import system
from threading import Thread
from showqrcode import QRLoginApp
import tkinter as tk
from logger import info, warning, error
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
            warning("you don't have permission")
            self.signClass.Y = True
            return None
        c = self.signClass.signData()
        gpsNumber = 0
        passwordNumber = 0
        for i in range(len(c)):
            for j in c[i]["data"]["gps"]:
                if j["status"] == 1: # 未签
                    gpsNumber += 1
                    info("gps:"+self.signClass.gpsSign(j["params"], j["gpsUrl"]))
                if j["status"] == -1:
                    info("gps:可能你以签过但又被管理员设为已签，又或者这次gps不设范围")
            for l in range(len(c[i]["data"]["password"])):
                if c[i]["data"]["password"][l]["status"] == 1:
                    passwordNumber += 1
                    result = self.signClass.passwordSign(c[i]["data"]["password"][l]["pwdUrl"])
                    if result == -1: # 说明
                        c[i]["data"]["password"][l]["status"] = -1
                    else:
                        info("password:"+self.signClass.passwordSign(c[i]["data"]["password"][l]["pwdUrl"]))
        if gpsNumber == 0:
            info("gps无可签到")
        if passwordNumber == 0:
            info("password无可签到")
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
        error(f"程序异常: {e}", exc_info=True)
    #system("pause")