import time
import threading
from requests import Session
from config.config_manager import config
from infrastructure.logger import info, warning, error

# 引入原有业务逻辑模块
import service.crawler.crawlSign
from models.sign_data import Sign
from service.pipeline.transformer import Transformer
from service.pipeline.extractors import extractor, sort_sign
from service.signer.signer_core import Signer
from service.login.QRApp import QRLoginApp


class Scheduler:
    """任务调度器类

    负责定时轮询签到任务并执行签到操作
    支持多种签到类型：GPS签到、密码签到、二维码签到、点名签到
    """
    def __init__(self, log_callback=None, input_callback=None):
        """初始化任务调度器

        Args:
            log_callback: 用于将日志传回GUI的回调函数 func(msg)
            input_callback: 用于从GUI获取用户输入的回调函数 func(prompt) -> str
        """
        # HTTP会话对象
        self.r = None
        # 调度器运行状态
        self.running = False
        # 监听线程
        self.thread = None
        # 日志回调函数
        self.log_callback = log_callback
        # 用户输入回调函数
        self.input_callback = input_callback

        # 初始化配置和HTTP会话
        config.init_config()
        self._init_session_from_config()

    def _log(self, msg, level="info"):
        """内部日志处理，同时打印到控制台和发送给GUI"""
        if level == "info":
            info(msg)
        elif level == "warning":
            warning(msg)
        elif level == "error":
            error(msg)

        if self.log_callback:
            self.log_callback(f"[{level.upper()}] {msg}")

    def _init_session_from_config(self):
        """初始化Session并尝试加载Cookies"""
        self.r = Session()
        self.r.headers.update(config.headers)

        # 尝试加载学生Cookies
        if config.user.get("student"):
            self.r.cookies.update(config.user["student"])
            self._log("已加载本地学生Cookies")
        else:
            self._log("未找到本地Cookies，请点击重新登录", "warning")

        # 尝试加载教师Cookies (用于辅助获取salt等)
        if config.not_find_signId.get("type") == 1:
            if config.user.get("teacher"):
                self._log("已加载本地老师Cookies")
                self.r.cookies.update(config.user["teacher"])
            else:
                self._log("未找到老师Cookies，请点击老师版登录", "warning")

    def login(self, method="student"):
        """处理登录逻辑，支持学生和教师两种模式"""
        self._log(f"开始 {method} 登录流程...")

        qr_app = QRLoginApp(method=method)

        # 在scheduler中直接运行，QRApp会使用当前的wx.App实例
        # 注意：这里需要在主线程中调用，但scheduler.login可能在后台线程被调用
        # 所以我们需要特殊处理，这里假设是通过GUI按钮调用的
        qr_app.run()

        if qr_app.login.cookies is None:
            self._log(f"{method}登录失败或取消", "warning")
            return False

        # 根据登录类型保存cookies
        section = "user"

        self.save_user_cookies(qr_app.login.cookies, section)
        self.r.cookies.update(qr_app.login.cookies)
        self._log(f"{method} 登录成功")


        return True

    def save_user_cookies(self, cookies, section="user"):
        """保存用户cookies到配置文件

        Args:
            cookies: cookies列表
            section: 配置节名称，默认为"user"
        """
        data = {section: {}}
        # 遍历cookies，根据名称分类保存学生或教师cookies
        for cookie in cookies:
            if "remember_student" in cookie.name:
                student = {cookie.name: cookie.value, "expire": str(cookie.expires)}
                data[section]["student"] = student
            elif "remember_teacher" in cookie.name:
                teacher = {cookie.name: cookie.value, "expire": str(cookie.expires)}
                data[section]["teacher"] = teacher
        # 保存到配置文件
        config.save(data)

    def start(self):
        """启动监听线程

        创建并启动后台线程执行主循环逻辑
        """
        # 防止重复启动
        if self.running:
            return

        # 设置运行状态并启动线程
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        self._log("监听服务已启动")

    def stop(self):
        """停止监听"""
        self.running = False
        self._log("正在停止监听服务...")

    def _loop(self):
        """主循环逻辑

        定时执行任务检查，间隔时间由配置文件中的interval决定
        循环直到running状态变为False
        """
        while self.running:
            try:
                # 执行单次任务检查
                self._run_task()
            except Exception as e:
                self._log(f"运行出错: {str(e)}", "error")

            # 等待 interval 时间，期间可被中断
            interval = config.settings.get("interval", 60)
            for _ in range(int(interval)):
                if not self.running: break
                time.sleep(1)

    def _run_task(self):
        """单次执行的任务逻辑

        执行完整的签到任务流程：
        1. 爬取签到数据
        2. 提取并分类签到任务
        3. 处理需要Salt的签到任务
        4. 等待指定时间后执行签到
        5. 执行各类签到操作
        """
        self._log("正在检查签到任务...")

        # 1. 爬取数据
        data = service.crawler.crawlSign.Spyder(self.r).signData()

        # 2. 提取并分类
        extracted_data = extractor(data)
        if not extracted_data:
            self._log("当前无签到任务")
            return

        signs = sort_sign(extracted_data)
        signer = Signer(self.r)
        default_location = {"lat": config.location["default_lat"], "lng": config.location["default_lng"]}

        # 处理需要 Salt 的情况 (教师模式下)
        if config.not_find_signId["type"] == 1 and signs["not_find_sign_id"]:
            try:
                self.add_salt(signs["not_find_sign_id"])
            except Exception as e:
                self._log(f"获取Salt失败: {e}", "error")

        # 3. 如果有需要签到的任务，执行“等待一次”逻辑
        all_tasks = signs["find_sign_id"] + signs["not_find_sign_id"]
        if all_tasks:
            wait_time = config.settings.get("after", 5)
            self._log(f"发现签到任务，等待 {wait_time} 秒后执行...")
            # 检查运行状态，允许在等待期间停止
            for _ in range(int(wait_time)):
                if not self.running: return
                time.sleep(1)

        # 4. 执行签到 (直接签到类 - 已知sign_id的签到)
        for sign in signs["find_sign_id"]:
            if not self.running: return
            result = signer.mix_signer(sign, default_location)
            self._log(f"签到结果(ID直签): {result}")

        # 5. 执行签到 (无ID/需Salt类 - 需要特殊处理的签到)
        for sign in signs["not_find_sign_id"]:
            if not self.running: return

            # 如果已有salt值，使用salt签到
            if sign.salt is not None:
                result = signer.salt_signer(sign, default_location)
                self._log(f"签到结果(Salt): {result}")
            else:
                # 否则需要用户手动输入sign_id
                sign_id_input = None

                # 如果有配置回调函数，则尝试请求输入
                if self.input_callback:
                    # 此时后台线程会暂停，等待用户在界面输入
                    self._log(f"课程 {sign.class_id} 需要手动输入 sign_id，等待用户操作...", "warning")
                    sign_id_input = self.input_callback(f"课程 {sign.class_id} 缺少 sign_id，请输入(整数):")

                if sign_id_input:
                    try:
                        # 转换为 int 并构建 URL
                        sign.sign_id = int(sign_id_input)

                        # 拼接 sign_url (参考原文件逻辑)
                        # 注意：这里假设 config.urls["domain"] 存在，如果不存在请检查 config_manager
                        domain = config.urls.get("domain", "https://v18.ketangpai.com")
                        sign.sign_url = f"{domain}/student/punchs/course/{sign.class_id}/{sign.sign_id}"

                        result = signer.mix_signer(sign, default_location)
                        self._log(f"手动签到结果: {result}")

                    except ValueError:
                        self._log(f"输入的 '{sign_id_input}' 不是有效的整数，已跳过", "error")
                else:
                    self._log(f"课程 {sign.class_id} 未输入 sign_id，已跳过", "warning")

    def add_salt(self, signs: list[Sign]):
        """为签到任务添加salt值

        在教师模式下，通过Transformer获取salt值并应用到签到任务中

        Args:
            signs: 需要添加salt值的签到任务列表
        """
        # 检查是否配置了class_id
        if not config.not_find_signId["class_id"]:
            raise Exception("not find class id")

        # 检查是否需要切换教师账号
        if config.user.get("teacher"):
            # 使用教师账号cookies
            self.r.cookies.update(config.user["teacher"])
        else:
            self._log("缺少教师账号Cookies用于获取Salt", "warning")

        # 通过Transformer获取salt值
        foo = Transformer()
        salt = foo.salt(self.r, config.not_find_signId["class_id"])

        # 为所有签到任务设置salt值
        for sign in signs:
            sign.salt = salt