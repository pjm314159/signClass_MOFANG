from datetime import datetime
import json
import re
from bs4 import BeautifulSoup as bs
from infrastructure.logger import info,warning,error
from config.config_manager import config
from models.sign_data import Class,Sign
class Spyder:
    def __init__(self,r):
        self.domain = config.urls["domain"]
        self.urlStudent = self.domain + "/student"
        self.r = r
    def signData(self):
        body_text = bs(self.r.get(self.urlStudent).text, "lxml")
        cards = body_text.find_all("div", class_="card mb-3 course")
        classList = []
        for card in cards:
            course_url = self.domain + card.find("a").get("href") + "/punchs?op=ing"
            classId_search = re.search(r'/student/course/(\d+)', card.find("a").get("href"))
            if classId_search:
                classId = classId_search.group(1)
            else:
                error("not find classId")
                raise Exception
            classId = card.find("a").get("href")[16:]
            #class_detail
            signList = []
            clv = Class(class_id=classId,name=card.find("h5",class_="course_name").text,signs=signList)
            classPage = bs(self.r.get(course_url).text, "lxml")
            for count,signCard in enumerate(classPage.find_all("div", class_="card-body")):
                form = signCard.find("div",class_="punch-meta")
                if form:
                # 说明是普通的框
                    typeMessage = signCard.find("div",class_="punch-meta").find("span").text.strip()
                    deadline = signCard.find("span",class_="countdown").get("ct")
                    status = signCard.find("div",class_="punch-status").text

                    start_time = signCard.find("div",class_="mt-2 font-weight-bold").text.strip()
                    start_time = self.convert_to_timestamp(start_time) #时间戳格式

                    if "正在进行" in status:
                        status = 1
                    elif "已签到" in status:
                        status = 0
                    result = Sign(start_time=start_time, class_id=classId, sign_type=typeMessage, status=status,
                                  deadline=deadline)
                    if status == 0:
                        continue
                    if "二维码" in typeMessage:
                        # 无法获取signId
                        pass
                    elif "GPS" in typeMessage:
                        signId = re.search(r'/student/punchs/course/\d+/(\d+)', signCard.find("a").get("href"))
                        if not signId:
                            error("not find signId")
                            raise Exception("not find signId")
                        try:
                            signId = int(signId.group(1))
                        except ValueError:
                            error("not find signId")
                            raise Exception("not find signId")
                        signUrl = f"{self.domain}/student/punchs/course/{classId}/{signId}"
                        result.sign_id = signId
                        result.sign_url = signUrl

                        gpsPage = bs(self.r.get(signUrl).text, "lxml")
                        info_text = gpsPage.find_all("script", type="text/javascript")[1].text.strip()
                        value = re.search(r'var\s+gpsranges\s*=\s*(.*?);', info_text)
                        if value:
                            value = value.group(1)

                            if value == "null": #不含gps数据
                               pass
                            else:
                                exact_data = json.loads(value)[0]
                                params = {"lat": exact_data[0], "lng": exact_data[1], "acc": "1", "res": "",
                                          "gps_addr": ""}

                                result.params = params

                    elif "密码" in typeMessage:
                        # 下一个框获取signId
                        pass
                    elif "点名" in typeMessage:
                        # 无法获取signId
                        pass

                    signList.append(result)
                else:
                    #说明是密码签到的框
                    t = signCard.find("form").get("action")
                    signId = re.search(r'/student/punch/course/\d+/(\d+)',t)
                    if not signId:
                        error("not find signId")
                        raise Exception("not find signId")
                    signId = int(signId.group(1))
                    signUrl = f"{self.domain}{t}"
                    signList[count-1].sign_id = signId
                    signList[count-1].sign_url = signUrl
            classList.append(clv)
        return classList

    def convert_to_timestamp(self,time_str):
        # 获取当前年份
        current_year = datetime.now().year

        # 解析时间字符串，格式为"月-日 时:分"
        time_obj = datetime.strptime(f"{current_year}-{time_str}", "%Y-%m-%d %H:%M")

        # 转换为时间戳
        timestamp = time_obj.timestamp()

        return int(timestamp)


if __name__ == "__main__":
    from service.login.QRApp import QRLoginApp
    QRApp = QRLoginApp()
    QRApp.run()

    sign = Spyder(QRApp.login.r)
    f = sign.signData()
    print(f)