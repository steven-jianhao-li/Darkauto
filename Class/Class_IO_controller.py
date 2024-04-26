# 基于LOGITECH类，实现更易使用的鼠标键盘操作类
import random
import time
from Class.Class_LOGITECH import LOGITECH


class IO_controller:
    def __init__(self, min_time=0.0075):
        self.min_time = min_time
        self.logitech = LOGITECH()

    def left_click(self, wait_time=0):
        """鼠标左键点击"""
        self.logitech.mouse_click('左', wait_time=wait_time)

    def right_click(self, wait_time=0):
        """鼠标右键点击"""
        self.logitech.mouse_click('右', wait_time=wait_time)

    def mid_click(self, wait_time=0):
        """鼠标中键点击"""
        self.logitech.mouse_click('中', wait_time=wait_time)
        

    def move_to(self, x, y, input_min_interval_time=-1):
        """鼠标移动到指定位置"""
        if input_min_interval_time == -1:
            input_min_interval_time = self.min_time
        self.logitech.mouse_move((x, y), min_time=input_min_interval_time)

    def move_to_left_click(self, x, y, input_min_interval_time=-1):
        """鼠标移动到指定位置并点击"""
        if input_min_interval_time == -1:
            input_min_interval_time = self.min_time
        move_flag = self.logitech.mouse_move((x, y), min_time=input_min_interval_time)
        if move_flag:   # 如果鼠标移动到指定位置，才会触发点击操作
            self.logitech.mouse_left_click()
        else:
            print("时间", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), "鼠标移动失败，未点击")
        
    def rand_move_to_left_click(self, x, y, rand_x, rand_y):
        """
        鼠标随机移动到指定位置附近并点击，范围是矩形
        x, y: 目标位置
        rand_x, rand_y: 随机范围
        """
        x += random.randint(-rand_x, rand_x)
        y += random.randint(-rand_y, rand_y)
        self.move_to_left_click(x, y, self.min_time)

    def keyboard_press(self, code):
        self.logitech.keyboard_click(code)