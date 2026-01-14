"""
配置文件管理器
用于管理应用程序的配置设置，包括：
- 系统设置（间隔时间、自动启动等）
- 位置设置（默认经纬度）
- 日志配置
- URL配置
- 用户登录信息
"""

import yaml
from os import path
from typing import Dict,Any



class ConfigManager:
    """配置管理器类，负责加载、保存和管理应用程序配置"""
    # 配置文件路径和编码
    config_path:str = "config.yaml"
    config_encoding:str = "utf-8"
    icon_path:str = "assets/favicon.ico"

    # 配置文件的节(section)列表
    sections:list[str] = ["settings","location","logging","urls","not_find_signId"]

    # 系统设置: after=签到任务发现后等待时间(秒), interval=检查间隔(秒), auto_start=是否自动启动监听
    settings: Dict[str, int] = {"after":1,"interval":30,"auto_start":0}

    # 默认地理位置: 用于GPS签到
    location: Dict[str,float] = {"default_lat":23.038849,"default_lng":113.398469}

    # 日志配置
    logging:Dict[str,Any] = {"level":"INFO","console":True,"file_enabled":True,"file":"app.log",
                             "max_file_size":1048750,"backup_count":5}

    # 找不到sign_id时的处理配置: type=处理类型(0=学生模式,1=教师模式), class_id=老师课程ID, max_try=最大尝试次数
    not_find_signId:Dict[str,int]= {"type":0,"class_id":None,"max_try":100}

    # URL配置: 登录和API相关URL
    urls:Dict[str,str] = {"student_login":"https://login.b8n.cn/qr/weixin/student/2",
                          "student_login_check":"https://login.b8n.cn/qr/weixin/student/2?op=checklogin",
                          "teacher_login":"https://login.b8n.cn/qr/weixin/teacher/2",
                          "teacher_login_check": "https://login.b8n.cn/qr/weixin/teacher/2?op=checklogin",
                          "domain":"https://bj.k8n.cn"
                          }
    # 用户登录数据: 存储学生和教师的cookies
    user:Dict[str,Dict[str,Dict[str,Any]]] = {"student":{},"teacher":{}}

    # HTTP请求头
    headers = {"Referer":"https://login.b8n.cn/",
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"}
    def init_config(self):
        """初始化配置文件

        如果配置文件不存在则创建默认配置文件，
        如果存在则加载配置文件中的设置
        """
        # 检查配置文件是否存在，不存在则创建默认配置
        if not path.exists(self.config_path):
            self.creat_config()
            return

        # 加载配置文件
        data = None
        with open(self.config_path, "r",encoding=self.config_encoding) as f:
            data = yaml.safe_load(f)

        # 如果配置文件为空也创建默认配置
        if data is None:
            self.creat_config()
            return

        # 遍历配置节，更新配置项
        for section in self.sections:
            if section in data:
                for key,value in data[section].items():
                    # 检查配置项是否存在，不存在则警告
                    if  not key in getattr(self,section):
                        print(f"{section} section doesn't exist key {key}")
                        continue
                    # 更新配置项的值
                    getattr(self, section)[key] = value

        # 加载用户登录数据(cookies)
        if "user" in data:
            self.user = data["user"]

    def creat_config(self):
        """创建默认配置文件

        根据类中定义的默认配置创建配置文件
        """
        data = {}
        # 遍历所有配置节，收集默认配置
        for section in self.sections:
            data[section] = getattr(self, section)
        # 写入配置文件
        with open(self.config_path, "w",encoding=self.config_encoding) as f:
            yaml.safe_dump(data, f,allow_unicode=True)
    def load_config(self)->Dict[str,Dict]:
        """加载当前内存中的配置

        返回包含所有配置节的字典

        Returns:
            Dict[str,Dict]: 包含所有配置节的字典
        """
        data = {}
        # 遍历所有配置节，收集当前配置
        for section in self.sections:
            data[section] = getattr(self, section)
        return data
    def get(self,section,key,fallback=None):
        """获取指定配置项的值

        Args:
            section: 配置节名称
            key: 配置项键名
            fallback: 默认返回值，当配置项不存在时返回

        Returns:
            配置项的值或默认值
        """
        try:
            return getattr(self, section)[key]
        except:
            return fallback
    def save(self,new_data:Dict[str,Dict]) -> None:
        """保存配置到文件

        Args:
            new_data: 新的配置数据字典
        """
        # 加载当前配置
        data = self.load_config()
        data["user"] = config.user

        # 遍历新数据并更新配置
        for key in new_data.keys():
            # 处理用户数据(登录cookies)
            if key == "user":
                for identity in new_data[key].keys():
                    if "teacher" == identity or "student" == identity:
                        data[key][identity] = new_data[key][identity]
                        getattr(self,key)[identity] = new_data[key][identity]

            # 处理配置节数据
            elif key in self.sections:
                getattr(self, key).update(new_data[key])
                data[key].update(new_data[key])
            else:
                print("error ")

        # 写入配置文件
        with open(self.config_path,"w",encoding=self.config_encoding) as f:
            f.write(yaml.safe_dump(data,allow_unicode=True))

config = ConfigManager()

