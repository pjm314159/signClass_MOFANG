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
        c = self.signClass.signData()
        gpsNumber = 0
        passwordNumber = 0
        for i in range(len(c)):
            for j in c[i]["data"]["gps"]:
                if j["status"] == 1:
                    gpsNumber += 1
                    print(self.signClass.gpsSign(j["params"], j["gpsUrl"]))
            for l in range(len(c[i]["data"]["password"])):
                if c[i]["data"]["password"][l]["status"] == 1:
                    passwordNumber += 1
                    result = self.signClass.passwordSign(c[i]["data"]["password"][l]["pwdUrl"])
                    if result == -1:
                        c[i]["data"]["password"][l]["status"] = -1
                    print(self.signClass.passwordSign(c[i]["data"]["password"][l]["pwdUrl"]))
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
        self.root.mainloop()

if __name__ == "__main__":
    app = Launch()
    app.launch()
    system("pause")