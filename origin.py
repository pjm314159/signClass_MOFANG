import requests
from bs4 import BeautifulSoup as bs
import qrcode
import  json
headers = {"Referer":"https://login.b8n.cn/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"}
r = requests.Session()
r.headers.update(headers)
loginUrl = "https://login.b8n.cn/qr/weixin/student/2"
rLogin = r.get(loginUrl)
bsLogin = bs(rLogin.text, "lxml")
wxJs = bsLogin.find_all(type="text/javascript")[-1].text
wxUrl = wxJs[wxJs.find('"')+1:wxJs.find(';')-1]
img = qrcode.make(wxUrl)
img.save("qrcode.png")
checkLoginUrl = "https://login.b8n.cn/qr/weixin/student/2?op=checklogin"
Login = r.get(checkLoginUrl)
while json.loads(Login.text)["status"] == False:
    Login = r.get(checkLoginUrl)
getCookiesUrl = json.loads(Login.text)["url"][:24]+"/uidlogin" +json.loads(Login.text)["url"][24:]
r.get(getCookiesUrl)
urlStudent = "http://bj.k8n.cn/student"
m = bs(r.get(urlStudent).text, "lxml").find_all("div", class_="card mb-3 course")
for i in m:
    gpsIdList = []
    #print(i.find("h5").text)
    p = bs(r.get("http://bj.k8n.cn"+i.find("a").get("href")+"/punchs?op=ing").text, "lxml")
    for j in p.find_all("div", class_="card-body"):
        idType = j.get("id")
        if idType:
            for mes in j.find_all(class_="title"):
                print(mes.text.strip())
            #print(j.find(class_="subtitle").text.strip())
            if j.parent.get("onclick").find("punch_gps")>=0:
                gpsIdList.append(idType[10:])
    for j in gpsIdList:
        fatherNode = p.find(id="punch_gps_frm_"+j)
        if fatherNode:
            if fatherNode.find("input",id="punch_gps_inrange_"+j).get("value")=="1":
                location = fatherNode.find("input",id="punch_gps_ranges_"+j).get("value")[2:-2].split(",")
                for l in range(len(location)):
                    location[l] = location[l].replace('"','')
                params = {
                    "lat" : location[0],"lng" : location[1],"acc":"1","res":"","gps_addr":""
                }
                gpsUrl = "http://bj.k8n.cn"+fatherNode.find("form").get("action")
                result = r.post(gpsUrl, data=params)
                print(bs(result.text,"lxml").find(id="title").text)
            else:
                print(fatherNode.find("input").get("value"))