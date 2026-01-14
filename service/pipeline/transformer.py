import re
from infrastructure.logger import info,debug,warning
from config.config_manager import config
from models.sign_data import Sign
class Transformer:
    def __init__(self):
        pass
    def add_sign_id(self,sign:Sign,id:int):
        sign.signId = id
        sign.sign_url = f"{config.urls["domain"]}/student/punchs/course/{sign.class_id}/{id}"
    def salt(self,r,class_id:str)->int:
        params = {"form[config][type]":"qr","form[config][qr_expires_in]":10,"valid_time":5   }
        f = r.post(f"{config.urls["domain"]}/teacher/course/{class_id}/punch",data=params)
        signId = re.search(config.urls["domain"]+r'/teacher/course/\d+/punch/result/(\d+)',f.url)
        if not signId:
            raise Exception("not find signId")
        else:
            signId = signId.group(1)
        try:
            return int(signId)
        except ValueError:
            raise Exception(f"error signId{signId}")
