# -*- coding:utf-8 -*-
from PIL import ImageGrab, Image, ImageTk
import requests
import pyperclip

import base64
import json
from io import BytesIO
import platform

ocr_url = "http://yourOCRserver/predict/ocr_system"

sys_platform = platform.platform().lower()


def isWin():
    if "windows" in sys_platform:
        return True
    else:
        return False


def isMac():
    if "macos" in sys_platform:
        return True
    else:
        return False

# ocr识别


def ocrs(data):
    image = str(base64.b64encode(data), encoding='utf-8')
    data = '{"images":["' + image + '"]}'
    txt = requests.post(ocr_url, data=data,
                        headers={'Content-Type': 'application/json'})
    return txt.content.decode("utf-8")

def grabPic(pos = None):
    buffer = BytesIO()
    pic = ImageGrab.grab(bbox=pos)
    pic.save(buffer, format='PNG')
    return buffer

class MacCapture():
    def __init__(self):
        import os
        #调用系统截图, 存放到剪贴板
        os.system('screencapture -c -i')
        # 从剪贴板读取图片
        img = ImageGrab.grabclipboard()
        if isinstance(img, Image.Image):
            img_bytes = BytesIO()
            img.save(img_bytes, 'png')
            res = json.loads(ocrs(img_bytes.getvalue()))
            img_bytes.close()
            print('============================')
            print(res)
            print('============================')
            r = '\n'.join(obj['text'] for obj in res['results'][0])
            print(r)
            pyperclip.copy(r)


class WinCapture:
    def __init__(self):
        import tkinter
        import tkinter.filedialog
        import ctypes
        from time import sleep
        # 创建tkinter主窗口
        root = tkinter.Tk()
        # 指定主窗口位置与大小
        # root.geometry('200x80+400+300')
        # 隐藏工具栏
        root.overrideredirect(True)
        # 不显示主窗口
        root.config(bg='')
        # 不允许改变窗口大小
        root.resizable(False, False)
        root.bind('<Escape>', lambda x: root.destroy())
        root.bind('<Button-3>', lambda x: root.destroy())
        # 使用程序自身DPI(仅win可用)
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        # 调用api获得当前的缩放因子(仅win可用)
        ScaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0)
        # print("Scale: "+str(ScaleFactor))#125
        # 设置缩放因子
        root.tk.call('tk', 'scaling', ScaleFactor/75)
        
        # 变量X和Y用来记录鼠标左键按下的位置
        self.X = tkinter.IntVar(value=0)
        self.Y = tkinter.IntVar(value=0)

        self.selectPosition = None
        # 屏幕尺寸
        screenWidth = int(root.winfo_screenwidth() * ScaleFactor / 100)
        # print(screenWidth)
        screenHeight = int(root.winfo_screenheight() * ScaleFactor / 100)
        # print(screenHeight)

        # 创建顶级组件容器
        self.top = tkinter.Toplevel(root, width=screenWidth, height=screenHeight)
        # 不显示最大化、最小化按钮
        self.top.overrideredirect(True)
        self.top.attributes('-topmost', True)

        # 绑定退出按键(右键 and Esc)
        self.top.bind('<Escape>', lambda x: root.destroy())
        self.top.bind('<Button-3>', lambda x: root.destroy())
        self.canvas = tkinter.Canvas(self.top, bg='white', width=screenWidth, height=screenHeight)
        self.canvas.config(highlightthickness=0)
        # 显示全屏截图，在全屏截图上进行区域截图
        buffer = grabPic()
        im = Image.open(buffer)
        self.fullpic = ImageTk.PhotoImage(im)
        self.canvas.create_image(
            screenWidth//2, screenHeight//2, image=self.fullpic)
        buffer.close()
        # 鼠标左键按下的位置

        def onLeftButtonDown(event):
            self.X.set(event.x)
            self.Y.set(event.y)
            # 开始截图
            self.sel = True
        self.canvas.bind('<Button-1>', onLeftButtonDown)
        # 鼠标左键移动，显示选取的区域

        def onLeftButtonMove(event):
            if not self.sel:
                return
            global lastDraw
            try:
                # 删除刚画完的图形，要不然鼠标移动的时候是黑乎乎的一片矩形
                self.canvas.delete(lastDraw)
            except Exception as e:
                pass
            lastDraw = self.canvas.create_rectangle(self.X.get(), self.Y.get(), event.x, event.y, outline='#7CDCFE')
        self.canvas.bind('<B1-Motion>', onLeftButtonMove)
        # 获取鼠标左键抬起的位置，保存区域截图

        def onLeftButtonUp(event):
            self.sel = False
            try:
                self.canvas.delete(lastDraw)
            except Exception as e:
                pass
            sleep(0.1)
            self.top.destroy()
            root.destroy()
            # 考虑鼠标左键从右下方按下而从左上方抬起的截图
            myleft, myright = sorted([self.X.get(), event.x])
            mytop, mybottom = sorted([self.Y.get(), event.y])

            self.selectPosition = (myleft, mytop, myright, mybottom)
            
            buffered = grabPic(self.selectPosition)
            res = json.loads(ocrs(buffered.getvalue()))
            buffered.close()
            # 弹出保存截图对话框
            # fileName = tkinter.filedialog.asksaveasfilename(title='保存截图', filetypes=[('PNG files', '*.png')])
            # if fileName:
            #     print('保存:'+fileName+".png")
            #     pic.save(fileName+".png")
            # 关闭当前窗口
            # print(myleft, '  ', mytop,'  ',myright,'  ',mybottom)

            # print(res)
            r = '\n'.join(obj['text'] for obj in res['results'][0])
            print('============================')
            print(r)
            print('============================')
            pyperclip.copy(r)
        self.canvas.bind('<ButtonRelease-1>', onLeftButtonUp)
        self.canvas.pack(fill=tkinter.BOTH, expand=tkinter.YES)
        root.state('normal')
        # 启动消息主循环
        # root.update()
        root.mainloop()


if isWin():
    WinCapture()

elif isMac():
    MacCapture()
