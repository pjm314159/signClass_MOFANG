from wx import App, Frame, Icon, EVT_MENU, Menu, Timer, EVT_TIMER
from wx.adv import TaskBarIcon
from app import runApp
from threading import Thread
class MyTaskBarIcon(TaskBarIcon):
    ICON = "favicon.ico"
    TITLE = "signMoFang"
    ID_EXIT = 100
    ID_START = 200
    ID_STOP = 300
    def __init__(self):
        self.app = runApp()
        self.app.register()
        self.p = Thread(target=self.app.main)
        TaskBarIcon.__init__(self)
        self.timer = Timer(self)
        self.SetIcon(Icon(self.ICON), self.TITLE)
        self.Bind(EVT_TIMER, self.onTimer, self.timer)
        self.Bind(EVT_MENU, self.onExit, id=self.ID_EXIT)
        self.Bind(EVT_MENU, self.start, id=self.ID_START)
        self.Bind(EVT_MENU, self.stop, id=self.ID_STOP)
        self.timer.Start(30)
    def start(self, event):
        self.app.isEnd = False
        if not self.p.is_alive():
            self.p = Thread(target=self.app.main)
            self.p.start()
        else:
            self.p.start()
    def stop(self, event):
        self.app.isEnd = True
        while self.p.is_alive():
            pass
    def onExit(self, event):
        self.stop(event)
        self.Destroy()
    def CreatePopupMenu(self):
        menu = Menu()
        for mentAttr in self.getMenuAttrs():
            menu.Append(mentAttr[1], mentAttr[0])
        return menu
    def onTimer(self,event):
        if not self.p.is_alive() and not self.app.isEnd:
            self.start(event)

    def getMenuAttrs(self):
        return [('开始', self.ID_START),
                ('结束', self.ID_STOP),
                ('退出', self.ID_EXIT)]
class MyFrame(Frame):
    def __init__(self):
        Frame.__init__(self)
        MyTaskBarIcon()

class MyApp(App):
    def OnInit(self):
        MyFrame()
        return True
if __name__ == '__main__':
    app = MyApp()
    app.MainLoop()