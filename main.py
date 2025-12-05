import requests
from bs4 import BeautifulSoup as bs
import qrcode
import  json
class signClass:
    def __init__(self):
        self.headers = {"Referer":"https://login.b8n.cn/",
    "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"}
        self.r = None
        self.loginStudentUrl = "https://login.b8n.cn/qr/weixin/student/2"
        self.checkLoginUrl = "https://login.b8n.cn/qr/weixin/student/2?op=checklogin"
        self.cookies = {}
        self.domain = "http://bj.k8n.cn"
        self.urlStudent = self.domain + "/student"
        self.imgPath = "qrcode.png"  #图片保存路径
        self.Y = False # 是否停止请求登录
    def createSession(self):
        session = requests.Session()
        session.headers.update(self.headers)
        self.r = session
    def saveQrcode(self):
        rLogin = self.r.get(self.loginStudentUrl)
        bsLogin = bs(rLogin.text, "lxml")
        wxJs = bsLogin.find_all(type="text/javascript")[-1].text
        wxUrl = wxJs[wxJs.find('"') + 1:wxJs.find(';') - 1]
        img = qrcode.make(wxUrl)
        img.save(self.imgPath)
    def login(self):
        print("Waiting for login.....")
        Login = self.r.get(self.checkLoginUrl)
        while json.loads(Login.text)["status"] == False:
            Login = self.r.get(self.checkLoginUrl)
            if self.Y:
                return None
        getCookiesUrl = json.loads(Login.text)["url"][:24] + "/uidlogin" + json.loads(Login.text)["url"][24:]
        self.r.get(getCookiesUrl)
        self.cookies = self.r.cookies
        return True
    def signData(self):
        m = bs(self.r.get(self.urlStudent).text, "lxml").find_all("div", class_="card mb-3 course")
        signList = []
        for i in range(len(m)):
            p = bs(self.r.get("http://bj.k8n.cn" + m[i].find("a").get("href") + "/punchs?op=ing").text, "lxml")
            classId = m[i].find("a").get("href")[16:]
            signList.append({"name":m[i].find("h5").text,"classId":classId,"data":{"gps":[],"password":[],"qrcode":[],"readName":[]}}) #data
            for j in p.find_all("div", class_="card-body"):
                idType = j.get("id")
                if idType:
                    signId = idType[10:]
                    aData = {"id": signId,"status": None}
                    typeMessage = j.find(class_="subtitle")
                    if typeMessage.text.find("未签")>=0:
                        aData["status"] = 1
                    elif typeMessage.text.find("已签")>=0:
                        aData["status"] = 0
                    if typeMessage.text.find("位置") >= 0: #gpsid
                        fatherNode = p.find(id="punch_gps_frm_" + signId)
                        if fatherNode:
                            if fatherNode.find("input", id="punch_gps_inrange_" + signId).get("value") == "1": # 含gps数据
                                location = fatherNode.find("input", id="punch_gps_ranges_" + signId).get("value")[2:-2].split(",")
                                for l in range(len(location)):
                                    location[l] = location[l].replace('"', '')
                                params = {
                                    "lat": location[0], "lng": location[1], "acc": "1", "res": "", "gps_addr": ""
                                }
                                gpsUrl = self.domain + fatherNode.find("form").get("action")
                                aData["params"] = params
                                aData["gpsUrl"] = gpsUrl
                            else:# 不含gps数据，说明可能是简单位置上报或已签到又被老师设为未签到
                                params = {
                                    "lat": "", "lng": "", "acc": "1", "res": "", "gps_addr": ""
                                }
                                gpsUrl = self.domain + fatherNode.find("form").get("action")
                                aData["gpsUrl"] = gpsUrl
                                aData["params"] = params
                                aData["status"] = -1
                        signList[i]["data"]["gps"].append(aData)
                    elif typeMessage.text.find("点名")>=0:
                        aData["rollCallUrl"] = f"{self.domain}/student/punchs/course/{classId}/{signId}"
                        signList[i]["data"]["readName"].append(aData)
                    elif typeMessage.text.find("扫码") >= 0:
                        aData["qrUrl"] = f"{self.domain}/student/punchs/course/{classId}/{signId}"
                        signList[i]["data"]["qrcode"].append(aData)
                    elif typeMessage.text.find("密码") >= 0:
                        aData["pwdUrl"] = self.domain + f"/student/punchs/course/{signList[i]['classId']}/{signId}"
                        signList[i]["data"]["password"].append(aData)
        return signList
    def gpsSign(self,location,gpsUrl):
        params = {
            "lat": location["lat"], "lng": location["lng"], "acc": "1", "res": "", "gps_addr": ""
        }
        result = bs(self.r.post(gpsUrl,data=params).text,"lxml").find(id="title").text
        return result
    def passwordSign(self,pwdUrl):
        pwd = 0
        data = {"pwd":"0"*(4-len(str(pwd)))+str(pwd)}
        response = bs(self.r.post(pwdUrl,data=data).text,"lxml")
        result = response.find(id="title").text
        while result != "签到成功":
            if pwd >9999:
                break
            if result=="我已签到过啦":
                return -1
            pwd += 1
            result = bs(self.r.post(pwdUrl, data=data).text, "lxml").find(id="title").text
            print(result,pwd)
            data["pwd"]="0"*(4-len(str(pwd)))+str(pwd)
        return {"result":result,"pwd":"0"*(4-len(str(pwd)))+str(pwd)}
    def qrcodeSign(self,location,qrcodeUrl):
        """网站代码太蠢，可以用gps的签二维码签到"""
        return self.gpsSign(location,qrcodeUrl)
    def rollCallSign(self,location,rollCallUrl):
        return self.gpsSign(location,rollCallUrl)
if __name__ == "__main__":
    sign = signClass()
    sign.createSession()
    sign.saveQrcode()
    sign.login()
    c = sign.signData()
    params = {"lat":"","lng":""}
    qr_url = "http://bj.k8n.cn/student/punchs/course/128358/"+c[1]["data"]["readName"][0]["id"]
    print(sign.gpsSign(params,qr_url))

    # for i in range(len(c)):
    #     for j in c[i]["data"]["gps"]:
    #         if j["status"] == 1:
    #            print(sign.gpsSign(j["params"],j["gpsUrl"]))
    #     for l in range(len(c[i]["data"]["password"])):
    #         if c[i]["data"]["password"][l]["status"] == 1:
    #             result = sign.passwordSign(c[i]["data"]["password"][l]["pwdUrl"])
    #             if result==-1:
    #                 c[i]["data"]["password"][l]["status"] = -1
    #             print(sign.passwordSign(c[i]["data"]["password"][l]["pwdUrl"]))