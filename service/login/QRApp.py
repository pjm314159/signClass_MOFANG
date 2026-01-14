from service.login.login import Login
from gui.qr_login_dialog import show_qr_login  # 导入新的对话框
from threading import Thread


class QRLoginApp:
    def __init__(self, method="student"):
        """
        重构后的QRLoginApp，不再创建独立的wx.App实例
        """
        self.login = Login(method=method)
        self.init()

    def init(self):
        self.login.creatSession()

    def run(self):
        """
        运行登录流程
        返回: True表示登录成功，False表示失败或取消
        """
        # 启动等待登录的线程
        t = Thread(target=self.login.waitLogin, daemon=True)
        origin = self.login.getLoginUrl()
        t.start()

        # 使用对话框显示二维码
        # show_qr_login会自动查找当前wx.App实例
        success, cookies = show_qr_login(
            parent=None,  # 使用None，对话框会自动找到顶级窗口
            login_obj=self.login,
            url=origin,
            check_callback=lambda: t.is_alive(),
            refresh_callback=self.login.getLoginUrl
        )

        if success:
            # 如果登录成功，确保cookies被设置
            if self.login.cookies is None:
                # 可能需要从login对象中提取cookies
                # 这里假设login对象已经有cookies属性
                pass
        else:
            # 用户取消登录，通知waitLogin线程结束
            self.login.Y = True

        return success