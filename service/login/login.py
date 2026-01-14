import json
from bs4 import BeautifulSoup as bs
from time import sleep

from requests import Session
from config.config_manager import config
from infrastructure.logger import info,error,warning
class Login:
    def __init__(self,method="student"):
        self.headers =  config.headers
        self.r = None
        self.cookies = None
        if method == "student":
            self.loginUrl = config.urls["student_login"]
            self.checkLoginUrl = config.urls["student_login_check"]
        else:
            self.loginUrl = config.urls["teacher_login"]
            self.checkLoginUrl = config.urls["teacher_login_check"]
        self.Y = False # 是否停止监听登录
    def creatSession(self):
        self.r = Session()
        self.r.headers.update(self.headers)
    def getLoginUrl(self):
        try:
            page = self.r.get(self.loginUrl)
        except Exception as e:
            warning(e)
            raise e
        bsLogin = bs(page.text, "lxml")
        wxJs = bsLogin.find_all(type="text/javascript")[-1].text
        wxUrl = wxJs[wxJs.find('"') + 1:wxJs.find(';') - 1]
        return wxUrl
    def waitLogin(self):
        info("Waiting for login.....")
        check_login = self.r.get(self.checkLoginUrl)
        while json.loads(check_login.text)["status"] == False:
            check_login = self.r.get(self.checkLoginUrl)
            sleep(1)
            if self.Y:
                info("listening login has stopped")
                return
        # 添加uidLogin参数
        getCookiesUrl = json.loads(check_login.text)["url"][:24] + "/uidlogin" + json.loads(check_login.text)["url"][24:]
        self.r.get(getCookiesUrl)
        self.cookies = self.r.cookies

