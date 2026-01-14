from gui.main_ui import run_gui
from config.config_manager import config

if __name__ == '__main__':
    # 初始化配置文件
    config.init_config()
    # 启动图形用户界面
    run_gui()