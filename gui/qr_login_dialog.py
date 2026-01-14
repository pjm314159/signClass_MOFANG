import wx
import qrcode
import threading
from io import BytesIO
import queue


class QRLoginDialog(wx.Dialog):
    def __init__(self, parent, url, title="二维码登录",
                 check_callback=None, refresh_callback=None):
        """
        url: 要编码成二维码的URL字符串
        check_callback: 一个函数，用于检测登录线程是否结束
        refresh_callback: 一个函数，用于刷新二维码，返回新的URL字符串
        """
        super().__init__(parent, title=title, size=(500, 600))

        self.login_success = False
        self.cookies = None
        self.login_obj = None  # 将存储Login对象引用

        # 保存参数
        self.url = url
        self.check_callback = check_callback
        self.refresh_callback = refresh_callback
        self.aspect_ratio = 1.0
        self.original_image = None
        self.image_queue = queue.Queue()  # 用于线程间传递图片数据

        # 初始化界面
        self.init_ui()

        # 居中显示
        self.Centre()

        # 绑定窗口大小改变事件以重绘图片
        self.Bind(wx.EVT_SIZE, self.on_resize)

        # 绑定关闭事件
        self.Bind(wx.EVT_CLOSE, self.on_dialog_close)

        # 设置定时器，检查登录状态和图片队列
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer_event, self.timer)
        self.timer.Start(100)  # 每100ms检查一次

        # 生成并加载二维码
        self.generate_qr_code()

    def init_ui(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # 1. 文本标签
        font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.label = wx.StaticText(panel, label="请扫描二维码登录,登录后自动关闭")
        self.label.SetFont(font)
        self.label.SetForegroundColour('#333333')

        vbox.Add(self.label, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 20)

        # 2. 刷新按钮
        self.refresh_btn = wx.Button(panel, label="刷新二维码")
        self.refresh_btn.Bind(wx.EVT_BUTTON, self.on_refresh)
        vbox.Add(self.refresh_btn, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        # 3. 加载提示
        self.loading_label = wx.StaticText(panel, label="")
        vbox.Add(self.loading_label, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 10)

        # 4. 图片区域（初始为空）
        self.bmp = wx.StaticBitmap(panel, -1, wx.Bitmap(1, 1))
        vbox.Add(self.bmp, 1, wx.EXPAND | wx.ALL, 10)

        # 5. 取消按钮
        btn_cancel = wx.Button(panel, label="取消登录")
        btn_cancel.Bind(wx.EVT_BUTTON, self.on_cancel)
        vbox.Add(btn_cancel, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 10)

        panel.SetSizer(vbox)
        self.panel = panel

    def generate_qr_code(self):
        """生成二维码图片"""
        if self.url:
            self.set_loading_text("正在生成二维码...")
            threading.Thread(target=self._generate_qr_from_url, args=(self.url,), daemon=True).start()

    def _generate_qr_from_url(self, url):
        """从URL生成二维码"""
        try:
            # 创建QRCode对象
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )

            # 添加数据
            qr.add_data(url)
            qr.make(fit=True)

            # 创建二维码图片
            img = qr.make_image(fill_color="black", back_color="white")

            # 将PIL图像转换为wx.Image
            img_bytes = BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)

            # 创建wx.Image
            wx_img = wx.Image(img_bytes, wx.BITMAP_TYPE_PNG)

            # 将图片放入队列，供主线程处理
            self.image_queue.put((wx_img, None))
        except Exception as e:
            self.image_queue.put((None, f"生成二维码失败: {str(e)}"))

    def on_timer_event(self, event):
        """定时器事件处理"""
        # 检查是否有新的图片数据
        self.check_image_queue()

        # 检查登录状态
        self.check_login_status()

    def check_image_queue(self):
        """检查图片队列，更新UI"""
        try:
            while True:
                img, error = self.image_queue.get_nowait()
                if error:
                    self.show_error(error)
                elif img and img.IsOk():
                    self.update_image(img)
                else:
                    self.show_error("二维码生成失败")
        except queue.Empty:
            pass

    def update_image(self, img):
        """更新显示的图片"""
        self.original_image = img
        self.aspect_ratio = img.GetWidth() / img.GetHeight()

        # 清除加载提示
        self.set_loading_text("")

        # 更新图片
        self.bmp.SetBitmap(wx.Bitmap(img))
        self.panel.Layout()

        # 触发一次resize事件以正确缩放图片
        wx.CallAfter(self.SendSizeEvent)

    def set_loading_text(self, text):
        """设置加载提示文本"""
        self.loading_label.SetLabel(text)
        if text:
            self.loading_label.SetForegroundColour(wx.BLUE)
            self.loading_label.Show()
            self.refresh_btn.Disable()
        else:
            self.loading_label.Hide()
            self.refresh_btn.Enable()
        self.panel.Layout()

    def show_error(self, error_msg):
        """显示错误信息"""
        self.loading_label.SetLabel(f"错误: {error_msg}")
        self.loading_label.SetForegroundColour(wx.RED)
        self.loading_label.Show()
        self.refresh_btn.Enable()
        self.panel.Layout()

    def on_resize(self, event):
        """处理窗口大小改变，保持图片比例缩放"""
        if self.original_image is None or not self.original_image.IsOk():
            event.Skip()
            return

        # 获取当前图片容器可用空间
        frame_width, frame_height = self.GetClientSize()
        text_height = self.label.GetSize()[1] + 40
        button_height = 40

        avail_w = frame_width - 20
        avail_h = frame_height - text_height - button_height - 20

        if avail_w > 10 and avail_h > 10:
            # 计算保持比例的新尺寸
            if avail_w / avail_h > self.aspect_ratio:
                new_h = avail_h
                new_w = int(new_h * self.aspect_ratio)
            else:
                new_w = avail_w
                new_h = int(new_w / self.aspect_ratio)

            # 缩放图片
            scaled_img = self.original_image.Scale(new_w, new_h, wx.IMAGE_QUALITY_HIGH)
            self.bmp.SetBitmap(wx.Bitmap(scaled_img))
            self.panel.Layout()

        event.Skip()

    def on_refresh(self, event):
        """刷新二维码"""
        if self.refresh_callback:
            self.set_loading_text("正在刷新二维码...")
            threading.Thread(target=self._refresh_qr_code, daemon=True).start()
        else:
            self.show_error("未提供刷新回调函数")

    def _refresh_qr_code(self):
        """在新线程中刷新二维码"""
        try:
            new_url = self.refresh_callback()
            if new_url:
                self.url = new_url
                self._generate_qr_from_url(new_url)
        except Exception as e:
            self.image_queue.put((None, f"刷新失败: {str(e)}"))

    def on_cancel(self, event):
        """取消登录"""
        if self.login_obj:
            self.login_obj.Y = True
        self.EndModal(wx.ID_CANCEL)

    def on_dialog_close(self, event):
        """对话框关闭事件"""
        if self.login_obj and not self.login_success:
            self.login_obj.Y = True
        self.timer.Stop()
        self.Destroy()

    def check_login_status(self):
        """检查登录状态"""
        if self.check_callback:
            try:
                is_alive = self.check_callback()
                if not is_alive and self.login_obj and self.login_obj.cookies:
                    # 登录成功
                    self.login_success = True
                    self.cookies = self.login_obj.cookies
                    self.timer.Stop()
                    self.EndModal(wx.ID_OK)
            except Exception as e:
                print(f"检查登录状态时出错: {e}")

    def set_login_obj(self, login_obj):
        """设置Login对象"""
        self.login_obj = login_obj

    def set_url(self, new_url):
        """设置新的URL并重新生成二维码"""
        self.url = new_url
        self.set_loading_text("正在更新二维码...")
        threading.Thread(target=self._generate_qr_from_url, args=(new_url,), daemon=True).start()


def show_qr_login(parent, login_obj, url, check_callback, refresh_callback,title:str="二维码登录"):
    """
    显示二维码登录对话框
    返回: (success, cookies)
    success: True 或 False
    cookies: 登录成功时的cookies，失败时为None
    """
    # 如果parent为None，尝试找到当前顶级窗口
    if parent is None:
        parent = wx.GetApp().GetTopWindow()

    dlg = QRLoginDialog(parent, url, title, check_callback, refresh_callback)
    dlg.set_login_obj(login_obj)

    result = dlg.ShowModal()
    dlg.Destroy()  # 确保对话框被销毁

    if result == wx.ID_OK:
        return True, dlg.cookies
    else:
        return False, None