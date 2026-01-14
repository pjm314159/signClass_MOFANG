from config.config_manager import config
from infrastructure.logger import info,warning,error
from bs4 import BeautifulSoup as bs

from models.sign_data import Sign


class Signer:
    """签到器类

    负责执行各种类型的签到操作
    支持密码签到、GPS签到、二维码签到、点名签到等类型
    """

    def __init__(self, r):
        """初始化签到器

        Args:
            r: HTTP会话对象(requests.Session)
        """
        self.r = r
    def password_signer(self, signUrl:str)->str:
        """密码签到

        通过暴力破解4位数字密码进行签到
        密码范围从0000到9999

        Args:
            signUrl: 签到URL

        Returns:
            str: 签到结果信息，包含成功状态和正确密码
        """
        pwd = 0
        # 构造初始密码数据(4位数字，不足补0)
        data = {"pwd": "0" * (4 - len(str(pwd))) + str(pwd)}
        response = bs(self.r.post(signUrl, data=data).text, "lxml")
        result = response.find("h2",class_="weui-msg__title").text

        # 循环尝试密码直到成功或超过最大尝试次数
        while result != "签到成功":
            # 超过最大密码值则退出
            if pwd > 9999:
                break

            # 如果已经签到过则返回
            if result == "我已签到过啦":
                warning(f"{result}, password={pwd}")
                return -1

            # 尝试下一个密码
            pwd += 1
            result = bs(self.r.post(signUrl, data=data).text, "lxml").find("h2",class_="weui-msg__title").text
            info(f"{result}, password={pwd}")
            # 更新密码数据
            data["pwd"] = "0" * (4 - len(str(pwd))) + str(pwd)

        return result + "密码："+"0" * (4 - len(str(pwd))) + str(pwd)
    def gps_signer(self,location:dict,signUrl:str)->str:
        """GPS位置签到

        通过提交经纬度坐标进行位置签到

        Args:
            location: 位置信息字典，包含lat(纬度)和lng(经度)
            signUrl: 签到URL

        Returns:
            str: 签到结果信息
        """
        # 构造位置参数
        params = {
            "lat": location["lat"], "lng": location["lng"], "acc": "1", "res": "", "gps_addr": ""
        }
        # 发送签到请求
        response = self.r.post(signUrl, data=params)
        # 解析响应结果
        result = bs(response.text, "lxml").find(id="title").text
        return result
    def rollCall_signer(self,location:dict,signUrl:str)->str:
        
        return self.gps_signer(location,signUrl)
    def qrcode_signer(self,location:dict,signUrl:str)->str:
        return self.gps_signer(location,signUrl)

    def mix_signer(self, sign: Sign, default_location: dict[str, str]) -> str:
        if "密码" in sign.sign_type:
            result = self.password_signer(sign.sign_url)
        elif "二维码" in sign.sign_type:
            result = self.qrcode_signer(location=default_location, signUrl=sign.sign_url)
        elif "GPS" in sign.sign_type:
            if sign.params:
                result = self.gps_signer(location=sign.params, signUrl=sign.sign_url)
            else:
                result = self.gps_signer(location=default_location, signUrl=sign.sign_url)
        elif "点名" in sign.sign_type:
            result = self.rollCall_signer(location=default_location, signUrl=sign.sign_url)
        return result
    def salt_signer(self,sign:Sign,default_location: dict[str, str])->str:
        count = 0
        sign.sign_id = sign.salt
        while True:
            count += 1
            sign.sign_id -= 1
            sign.sign_url = f"{config.urls["domain"]}/student/punchs/course/{sign.class_id}/{sign.sign_id}"
            result = self.mix_signer(sign,default_location)
            if count >= config.not_find_signId["max_try"] or "成功" in result:
                break
        return result