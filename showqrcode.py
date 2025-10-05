import tkinter as tk
from PIL import Image, ImageTk


class QRLoginApp:
    def __init__(self, root, image_path):
        self.root = root
        self.root.title("二维码登录")

        # 加载原始图片
        self.original = Image.open(image_path)
        self.aspect_ratio = self.original.width / self.original.height

        # 主容器
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

        # 添加提示文本
        self.label_text = tk.Label(
            self.main_frame,
            text="请扫描二维码登录,登录后退出",
            font=('Microsoft YaHei', 16, 'bold'),
            fg='#333333'
        )
        self.label_text.pack(pady=(0, 20))

        # 图片显示区域
        self.label_image = tk.Label(self.main_frame)
        self.label_image.pack(expand=True)

        # 绑定窗口变化事件
        self.root.bind("<Configure>", self.resize_image)
        self.resize_image()

    def resize_image(self, event=None):
        container_width = self.main_frame.winfo_width()
        container_height = self.main_frame.winfo_height() - 50  # 减去文本区域高度

        if container_width > 10 and container_height > 10:
            # 保持宽高比计算
            if container_width / container_height > self.aspect_ratio:
                new_width = int(container_height * self.aspect_ratio)
                new_height = container_height
            else:
                new_width = container_width
                new_height = int(container_width / self.aspect_ratio)

            resized = self.original.resize(
                (new_width, new_height),
                Image.LANCZOS
            )
            self.image = ImageTk.PhotoImage(resized)
            self.label_image.config(image=self.image)


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("500x600")
    app = QRLoginApp(root, 'qrcode.png')
    root.mainloop()
