import threading
import wx
import wx.adv
from os import path
from datetime import datetime
from wx import ArtProvider, ART_INFORMATION, ART_OTHER

from core.scheduler import Scheduler
from infrastructure.logger import warning
from config.config_manager import config
from service.login.QRApp import QRLoginApp  # 导入QRLoginApp


class TaskBarIcon(wx.adv.TaskBarIcon):
    def __init__(self, frame):
        super().__init__()
        self.frame = frame

        self.ICON = config.icon_path
        self.setup_icon()
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DCLICK, self.on_double_click)

    def setup_icon(self):
        """设置窗口图标，如果文件不存在则使用默认图标"""
        try:
            if path.exists(self.ICON):
                # 文件存在，加载指定图标
                icon = wx.Icon(self.ICON)
            else:
                # 获取系统图标
                warning("no find ico,use system ico")
                icon = ArtProvider.GetIcon(ART_INFORMATION, ART_OTHER, (32, 32))
            self.SetIcon(icon, "自动签到助手")
        except:
            warning("no find system ico")
            # 创建默认图标（一个简单的彩色方块）

    def CreatePopupMenu(self):
        menu = wx.Menu()

        show_item = menu.Append(wx.ID_ANY, "显示主界面")
        self.Bind(wx.EVT_MENU, self.on_show, show_item)

        menu.AppendSeparator()

        start_item = menu.Append(wx.ID_ANY, "开始监听")
        stop_item = menu.Append(wx.ID_ANY, "停止监听")

        menu.AppendSeparator()

        student_login_item = menu.Append(wx.ID_ANY, "学生登录")
        teacher_login_item = menu.Append(wx.ID_ANY, "教师登录")
        exit_item = menu.Append(wx.ID_EXIT, "退出程序")

        self.Bind(wx.EVT_MENU, self.frame.start_monitoring, start_item)
        self.Bind(wx.EVT_MENU, self.frame.stop_monitoring, stop_item)
        self.Bind(wx.EVT_MENU, lambda e: self.frame.on_login(e, "student"), student_login_item)
        self.Bind(wx.EVT_MENU, lambda e: self.frame.on_login(e, "teacher"), teacher_login_item)
        self.Bind(wx.EVT_MENU, self.frame.on_exit, exit_item)

        # 根据条件动态显示/隐藏教师登录菜单项
        if not self.frame.show_teacher_login:
            teacher_login_item.Enable(False)
            teacher_login_item.SetItemLabel("教师登录(未启用)")

        # 动态禁用/启用菜单项
        if self.frame.scheduler.running:
            start_item.Enable(False)
        else:
            stop_item.Enable(False)

        return menu

    def on_show(self, event):
        self.frame.Show()
        self.frame.Raise()

    def on_double_click(self, event):
        self.on_show(event)


class MainFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="自动签到助手", size=(600, 450))
        self.ICON = config.icon_path
        self.setup_icon()
        # 初始化时检查是否显示教师登录按钮
        self.show_teacher_login = False
        try:
            # 尝试读取配置，如果配置存在且type为1，则显示教师登录按钮
            if config.not_find_signId.get("type") == 1:
                self.show_teacher_login = True
        except Exception as e:
            warning(f"读取配置失败: {e}")

        self.init_ui()
        # 初始化 Scheduler
        self.scheduler = Scheduler(
            log_callback=self.append_log,
            input_callback=self.get_input_safe  # 传入此方法
        )

        self.task_bar_icon = TaskBarIcon(self)

        # 绑定关闭事件为隐藏
        self.Bind(wx.EVT_CLOSE, self.on_close)

        self.Centre()

        # 更新登录状态显示
        self.update_login_status()
        self.auto_start()
    def auto_start(self):
        if not config.user.get("student") or not config.settings.get("auto_start"):
            return
        wx.CallAfter(self.start_monitoring,None)
    def setup_icon(self):
        """设置窗口图标，如果文件不存在则使用默认图标"""
        try:
            if path.exists(self.ICON):
                # 文件存在，加载指定图标
                icon = wx.Icon(self.ICON)
            else:
                # 获取系统图标
                warning("no find ico,use system ico")
                icon = ArtProvider.GetIcon(ART_INFORMATION, ART_OTHER, (32, 32))

            self.SetIcon(icon)
        except:
            warning("no find system ico")
            # 创建默认图标（一个简单的彩色方块）
    def init_ui(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # 顶部按钮区
        hbox_ctrl = wx.BoxSizer(wx.HORIZONTAL)

        self.btn_start = wx.Button(panel, label="开始监听")
        self.btn_stop = wx.Button(panel, label="停止监听")
        self.btn_student_login = wx.Button(panel, label="学生登录")
        self.btn_teacher_login = wx.Button(panel, label="教师登录")

        self.btn_stop.Disable()  # 初始状态禁用停止
        if not config.user.get("student"):
            self.btn_start.Disable()
        # 根据条件显示或隐藏教师登录按钮
        if not self.show_teacher_login:
            self.btn_teacher_login.Hide()
            self.btn_teacher_login.Enable(False)

        self.btn_start.Bind(wx.EVT_BUTTON, self.start_monitoring)
        self.btn_stop.Bind(wx.EVT_BUTTON, self.stop_monitoring)
        self.btn_student_login.Bind(wx.EVT_BUTTON, lambda e: self.on_login(e, "student"))
        self.btn_teacher_login.Bind(wx.EVT_BUTTON, lambda e: self.on_login(e, "teacher"))

        hbox_ctrl.Add(self.btn_start, 0, wx.ALL, 5)
        hbox_ctrl.Add(self.btn_stop, 0, wx.ALL, 5)
        hbox_ctrl.Add(self.btn_student_login, 0, wx.ALL, 5)
        hbox_ctrl.Add(self.btn_teacher_login, 0, wx.ALL, 5)

        # 登录状态显示
        self.login_status_text = wx.StaticText(panel, label="登录状态: 正在检查...")
        self.login_status_text.SetForegroundColour(wx.Colour(255, 140, 0))  # 橙色
        vbox.Add(self.login_status_text, 0, wx.ALL, 5)

        # 日志区域
        self.log_text = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)
        self.log_text.SetFont(wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))

        # 布局
        vbox.Add(hbox_ctrl, 0, wx.EXPAND | wx.ALL, 5)
        vbox.Add(wx.StaticText(panel, label="运行日志:"), 0, wx.LEFT, 10)
        vbox.Add(self.log_text, 1, wx.EXPAND | wx.ALL, 10)

        panel.SetSizer(vbox)

    def get_input_safe(self, prompt):
        """
        【新增】线程安全的输入对话框。
        被后台线程调用，会阻塞后台线程直到 UI 返回结果。
        """
        result_holder = {"value": None}
        event = threading.Event()

        def _show_dialog_on_main_thread():
            # 只有在主线程才能安全操作 GUI
            dlg = wx.TextEntryDialog(self, prompt, "手动补充信息")
            if dlg.ShowModal() == wx.ID_OK:
                result_holder["value"] = dlg.GetValue()
            dlg.Destroy()
            # 唤醒后台线程
            event.set()

        # 请求主线程执行弹窗
        wx.CallAfter(_show_dialog_on_main_thread)

        # 阻塞当前后台线程，等待主线程处理完毕
        event.wait()

        return result_holder["value"]

    def append_log(self, msg):
        """线程安全的日志追加"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        wx.CallAfter(self.log_text.AppendText, f"[{timestamp}] {msg}\n")

    def update_login_status(self):
        """更新登录状态显示"""
        status_text = "登录状态: "

        # 检查是否有学生cookies
        has_student = False
        has_teacher = False

        try:
            config.init_config()  # 重新加载配置
            if config.user.get("student"):
                has_student = True
            if config.user.get("teacher"):
                has_teacher = True
        except:
            pass

        if has_student and has_teacher:
            status_text += "学生和教师已登录"
            color = wx.Colour(0, 128, 0)  # 绿色
        elif has_student:
            status_text += "学生已登录"
            color = wx.Colour(0, 128, 0)  # 绿色
        elif has_teacher:
            status_text += "教师已登录"
            color = wx.Colour(0, 128, 0)  # 绿色
        else:
            status_text += "未登录"
            color = wx.RED

        wx.CallAfter(self.login_status_text.SetLabel, status_text)
        wx.CallAfter(self.login_status_text.SetForegroundColour, color)

    def start_monitoring(self, event):
        self.scheduler.start()
        self.btn_start.Disable()
        self.btn_stop.Enable()
        self.append_log(">>> 指令: 开启监听")

    def stop_monitoring(self, event):
        self.scheduler.stop()
        self.btn_start.Enable()
        self.btn_stop.Disable()
        self.append_log(">>> 指令: 停止监听")

    def on_login(self, event, method="student"):
        """处理登录，包括学生和教师登录"""
        # 暂停监听
        was_running = self.scheduler.running
        if was_running:
            self.stop_monitoring(None)

        self.append_log(f">>> 正在启动{method}登录...")

        try:
            # 在主线程中直接运行登录，避免跨线程GUI问题
            success = self.do_login(method)

            if success:
                self.append_log(f">>> {method}登录成功")
            else:
                self.append_log(f">>> {method}登录失败或取消")

        except Exception as e:
            self.append_log(f">>> {method}登录异常: {e}")

        # 更新登录状态显示
        self.update_login_status()

        # 如果之前正在运行，重新启动
        if was_running:
            self.start_monitoring(None)

    def do_login(self, method="student"):
        """执行登录逻辑（在主线程中运行）"""
        try:
            if method == "teacher" and not config.not_find_signId.get("class_id"):
                self.append_log("[WARNING]没有找到class_id,请前往config.yaml配置")
                return False
            # 创建QRLoginApp实例
            qr_app = QRLoginApp(method=method)

            # 运行登录
            qr_app.run()

            # 检查登录结果
            if qr_app.login.cookies is None:
                return False

            # 保存cookies到配置文件
            if method == "student":
                self.btn_start.Enable()
            self.scheduler.save_user_cookies(qr_app.login.cookies)
            # 更新scheduler的session
            self.scheduler.r.cookies.update(qr_app.login.cookies)

            return True

        except Exception as e:
            self.append_log(f"登录过程出错: {e}")
            return False

    def on_close(self, event):
        """点击关闭按钮时隐藏窗口而不是退出"""
        self.Hide()
        # 气泡提示 (Windows有效)
        try:
            self.task_bar_icon.ShowBalloon("自动签到", "程序仍在后台运行，双击托盘图标打开")
        except:
            pass  # 某些平台不支持气泡提示

    def on_exit(self, event):
        """完全退出程序"""
        self.scheduler.stop()
        self.task_bar_icon.RemoveIcon()
        self.task_bar_icon.Destroy()
        self.Destroy()
        wx.GetApp().ExitMainLoop()


def run_gui():
    app = wx.App()
    frame = MainFrame()
    frame.Show()
    app.MainLoop()