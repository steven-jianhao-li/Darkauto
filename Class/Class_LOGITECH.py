# 提供LOGITECH类，用于调用罗技驱动控制鼠标和键盘
import ctypes
import random
import time

# 将上一级目录加入python搜索路径
import os
import sys

import pyautogui
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

from Class.Class_PID import PID

class LOGITECH:
    """罗技动态链接库"""
    def __init__(self) -> None:
        try:
            file_path = os.path.abspath(os.path.dirname(__file__)) # 当前文件路径
            file_path = os.path.abspath(os.path.join(file_path, os.pardir)) # 向上一级目录查找ghub_device.dll
            self.dll = ctypes.CDLL(f'{file_path}/ghub_device.dll') # 打开路径文件
            self.state = (self.dll.device_open() == 1) # 启动, 并返回是否成功
            self.WAIT_TIME = 0.5 # 等待时间
            self.MAX_RANDOM_SLEEP_TIME = 0.1 # 最大随机等待时间
            if not self.state:
                print('错误, 未找到GHUB或LGS驱动程序')
        except FileNotFoundError:
            print('错误, 找不到DLL文件')

    def mouse_down(self, code):
        """ 鼠标按下 code: 左 中 右 """
        if not self.state:
            return
        if code == '左':
            code = 1
        elif code == '中':
            code = 2
        elif code == '右':
            code = 3
        else: # 默认
            code = 1 
        self.dll.mouse_down(code)

    def mouse_up(self, code):
        """ 鼠标松开 code: 左 中 右 """
        if not self.state:
            return
        if code == '左':
            code = 1
        elif code == '中':
            code = 2
        elif code == '右':
            code = 3
        else: # 默认
            code = 1 
        self.dll.mouse_up(code)
    
    def mouse_click(self, code, wait_time=0):
        """ 鼠标点击 code: 左 中 右 """
        if wait_time != 0: # 如果等待时间不是0
            time.sleep(wait_time) # 延时时间
        if not self.state:
            return
        if code == '左':
            code = 1
        elif code == '中':
            code = 2
        elif code == '右':
            code = 3
        else: # 默认
            code = 1 
        self.dll.mouse_down(code)
        time.sleep(random.uniform(0, self.MAX_RANDOM_SLEEP_TIME)) # 延时时间
        self.dll.mouse_up(code)

    def mouse_left_click(self):
        """ 鼠标左键点击 """
        if not self.state:
            return
        self.dll.mouse_down(1)
        time.sleep(random.uniform(0, self.MAX_RANDOM_SLEEP_TIME))
        self.dll.mouse_up(1)
        
    def mouse_move(self, end_xy, min_xy=1, min_time=0.01):
        """
        利用pid循环控制鼠标直到重合坐标，最多循环100次
        相当于最多保持移动1秒，若在1秒内未达到指定坐标则退出，不执行点击操作
        :param end_xy: 目标坐标
        :param min_xy: 最小移动量
        :param min_time: 移动时的时间间隔
        :return: 是否到达目标坐标
        """
        if not self.state:
            return
        end_x, end_y = end_xy # 解码目标坐标
        pid_x = PID() # 创建pid对象
        pid_y = PID()

        for i in range(150):
            time.sleep(min_time) # 等待时间
            new_x, new_y = pyautogui.position() # 获取当前鼠标位置

            move_x = pid_x.pidPosition(end_x, new_x) # 经过pid计算鼠标运动量
            move_y = pid_y.pidPosition(end_y, new_y)

            # 如果近似重合就退出循环
            if abs(end_x - new_x) < 2 and abs(end_y - new_y) < 2:
                return True
            
            if move_x > 0 and move_x < (min_xy): # 限制正最小值
                move_x = (min_xy)
            elif move_x < 0 and move_x > -(min_xy): # 限制负最小值
                move_x = -(min_xy)
            else:
                move_x = int(move_x) # 需要输入整数,小数会报错

            if move_y > 0 and move_y < (min_xy):
                move_y = (min_xy)
            elif move_y < 0 and move_y > -(min_xy):
                move_y = -(min_xy)
            else:
                move_y = int(move_y)

            self.dll.moveR(move_x, move_y, True) # 貌似有第三个参数,但是没试出来什么用
        return False
    
    def keyboard_down(self, code):
        """ 键盘按下 code: 键盘按键 """
        if not self.state:
            return
        self.dll.key_down(code)

    def keyboard_up(self, code):
        """ 键盘松开 code: 键盘按键 """
        if not self.state:
            return
        self.dll.key_up(code)
    
    def keyboard_click(self, code):
        """ 键盘点击 code: 键盘按键 """
        if not self.state:
            return
        self.keyboard_down(code)
        time.sleep(random.uniform(0, self.MAX_RANDOM_SLEEP_TIME))
        self.keyboard_up(code)