import argparse
from multiprocessing import Process
import multiprocessing
import numpy as np
import pyautogui
import time
import cv2
import os
import random
import winsound
import ctypes
import pynput # 调用dll文件

# pip install pytesseract
# pip install pillow
# https://github.com/UB-Mannheim/tesseract/wiki 安装 tesseract-ocr
# 安装完成以后配置环境变量，在计算机-->属性-->高级系统设置-->环境变量-->系统变量path
import pytesseract

from web_service import Open_Web_Service
from Functions_IO import log_and_print, ringing
from Functions_OCR import OCR_image, OCR_Raw_ScreenShot
# from Item_Func_Class import *

# 所有按钮的位置坐标均以2k分辨率为基准
Search_button = (2315, 357, 153, 28)
# 按钮位置
first_Buy_buttons = (2389 - 50 / 2, 477 - 12 / 2, 50, 12)        # 第一个Buy按钮的位置，其余按钮坐标从上向下y坐标依次递减87
Buy_buttons_decrease_y = 86.7
Fill_All_Items_button = (1147, 986, 250, 65)
Complete_Trade_button = (1151, 1101, 250, 52)
# 静态文本位置
Prices_Text = (1986, 441, 93, 850)
Detailed_Prices_Text = (2136, 464, 130, 812)
Random_Attribute_Text = (1450, 441, 112, 850)
# Final_Price = (1383, 877, 168, 37) # 这个是小字，不好识别
Final_Price_Text = (255, 695, 275, 69)
Item_Name_Chosen_Text = (65, 263, 200, 24)
Rarity_Chosen_Text = (383, 263, 200, 24)
Class_Chosen_Text = (701, 263, 200, 24)
Slot_Chosen_Text = (1015, 263, 200, 24)
Type_Chosen_Text = (1334, 263, 200, 24)
Static_Attribute_Chosen_Text = (1649, 263, 200, 24)
Random_Attribute_Chosen_Text = (1965, 263, 200, 24)
Item_Sold_Text = (986, 177, 590, 58)
Buy_Success_Text = (908, 596, 744, 152)
Sure_to_Leave_Text = (1067, 617, 423, 110)

# 初始化数据
# 当前python文件的路径
File_Path = os.path.abspath(os.path.dirname(__file__))
init = {
    'pause_flag': False,
    'end_flag': False,
    'buy_times': 10,
    'LogFilePath': '{0}/log/{1}.txt'.format(File_Path, time.strftime('%Y_%m_%d %H_%M_%S', time.localtime()))
}

def microsecond_sleep(sleep_time):
    """微秒等待

    :param sleep_time: int, 微秒
    :return:
    """

    end_time = time.perf_counter() + (sleep_time - 0.8) / 1e6  # 0.8是时间补偿，需要根据自己PC的性能去实测
    while time.perf_counter() < end_time:
        pass


# 检测剩余购买次数
def check_buy_times():
    """ 检测剩余购买次数 """
    if data['buy_times'] > 1:
        data['buy_times'] -= 1
        log_and_print(data['LogFilePath'], 'buy_times已减少，当前值:', data['buy_times'])
    else:
        data['pause_flag'] = True
        log_and_print(data['LogFilePath'], '已购买足够次数，暂停...')

class PID:
    """PID"""
    def __init__(self, P=0.2, I=0, D=0):
        self.kp = P # 比例 
        self.ki = I # 积分
        self.kd = D # 微分
        self.uPrevious = 0 # 上一次控制量
        self.uCurent = 0 # 这一次控制量
        self.setValue = 0 # 目标值
        self.lastErr = 0 # 上一次差值
        self.errSum = 0 # 所有差值的累加
        
    def pidPosition(self, setValue, curValue):
        """位置式 PID 输出控制量"""
        self.setValue = setValue # 更新目标值
        err = self.setValue - curValue # 计算差值, 作为比例项
        dErr = err - self.lastErr # 计算近两次的差值, 作为微分项
        self.errSum += err # 累加这一次差值,作为积分项
        outPID = (self.kp * err) + (self.ki * self.errSum) + (self.kd * dErr) # PID
        self.lastErr = err # 保存这一次差值,作为下一次的上一次差值
        return outPID # 输出
    
    def pidIncrease(self, setValue, curValue):
        """增量式 PID 输出控制量的差值"""
        self.uCurent = self.pidPosition(setValue, curValue) # 计算位置式
        outPID = self.uCurent - self.uPrevious # 计算差值 
        self.uPrevious = self.uCurent # 保存这一次输出量
        return outPID # 输出

class LOGITECH:
    """罗技动态链接库"""
    def __init__(self) -> None:
        try:
            file_path = os.path.abspath(os.path.dirname(__file__)) # 当前路径
            self.dll = ctypes.CDLL(f'{file_path}/ghub_device.dll') # 打开路径文件
            self.state = (self.dll.device_open() == 1) # 启动, 并返回是否成功
            self.WAIT_TIME = 0.5 # 等待时间
            self.MAX_RANDOM_SLEEP_TIME = 0.1 # 最大随机等待时间
            if not self.state:
                log_and_print(data['LogFilePath'], '错误, 未找到GHUB或LGS驱动程序')
        except FileNotFoundError:
            log_and_print(data['LogFilePath'], f'错误, 找不到DLL文件')

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

            # log_and_print(data['LogFilePath'], f'x={new_x}, y={new_y}, xd={move_x}, yd={move_y}')
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
    
class IO_controller:
    def __init__(self, min_time=0.0075):
        self.min_time = min_time
        self.logitech = LOGITECH()

    def left_click(self, wait_time=0):
        """鼠标左键点击"""
        self.logitech.mouse_click('左', wait_time=wait_time)

    def move_to_left_click(self, x, y, min_time):
        """鼠标移动到指定位置并点击"""
        move_flag = self.logitech.mouse_move((x, y), min_time=min_time)
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

class Dark_Game_Operation:
    def __init__(self) -> None:
        self.io = IO_controller()

    def Press_Search_Button(self):
        center_x = int(Search_button[0] + Search_button[2] / 2)
        center_y = int(Search_button[1] + Search_button[3] / 2)
        rand_x = int(Search_button[2] / 2)
        rand_y = int(Search_button[3] / 2)
        self.io.rand_move_to_left_click(center_x, center_y, rand_x, rand_y)

    def Press_Buy_Button(self, index):
        center_x = int(first_Buy_buttons[0] + first_Buy_buttons[2] / 2)
        center_y = int(first_Buy_buttons[1] + first_Buy_buttons[3] / 2 + Buy_buttons_decrease_y * index)
        rand_x = int(first_Buy_buttons[2] / 2)
        rand_y = int(first_Buy_buttons[3] / 2)
        self.io.rand_move_to_left_click(center_x, center_y, rand_x, rand_y)
        self.io.left_click(0.001 + random.random() * 0.006)

    def press_Fill_All_Items_Button(self):
        center_x = int(Fill_All_Items_button[0] + Fill_All_Items_button[2] / 2)
        center_y = int(Fill_All_Items_button[1] + Fill_All_Items_button[3] / 2)
        rand_x = int(Fill_All_Items_button[2] / 2)
        rand_y = int(Fill_All_Items_button[3] / 2)
        self.io.rand_move_to_left_click(center_x, center_y, rand_x, rand_y)

    def press_Complete_Trade_Button(self):
        center_x = int(Complete_Trade_button[0] + Complete_Trade_button[2] / 2)
        center_y = int(Complete_Trade_button[1] + Complete_Trade_button[3] / 2)
        rand_x = int(Complete_Trade_button[2] / 2)
        rand_y = int(Complete_Trade_button[3] / 2)
        self.io.rand_move_to_left_click(center_x, center_y, rand_x, rand_y)

        
    def Get_Prices(self, screen_shot_img):
        """
        获取价格
        :param screen_shot_img: 全屏幕截图
        :return: 价格列表
        """
        # 对全屏幕截图进行裁剪，只保留价格区域
        img = screen_shot_img[Prices_Text[1]:Prices_Text[1] + Prices_Text[3], Prices_Text[0]:Prices_Text[0] + Prices_Text[2]]
        result = OCR_Raw_ScreenShot(img, only_number=True)
        # 转换识别结果为数组
        result = result.split('\n')
        try:
            # 清空空元素
            result = [x for x in result if x]
            # 将识别结果中的,去掉
            result = [x.replace(',', '') for x in result]
            result = [int(x) for x in result]
            # ——————————————————————————————————————————————这里要优化↓
            # 把'11'这个结果转换为111
            result = [x if x != 11 else 111 for x in result]
            # ————————————————————————————————————————————————
            if len(result) < 10:
                result = -1
            return result
        except:
            return -1
    
    def Get_Detailed_Prices(self, screen_shot_img):
        img = screen_shot_img[Detailed_Prices_Text[1]:Detailed_Prices_Text[1] + Detailed_Prices_Text[3], Detailed_Prices_Text[0]:Detailed_Prices_Text[0] + Detailed_Prices_Text[2]]
        result = OCR_Raw_ScreenShot(img)
        result = result.split('\n')
        # Detailed_Prices正常情况下是个10维数组。每一个元素为单价*数量，需要将其分解为单价和数量
        try:
            result = [x for x in result if x]
            result = [x.replace(',', '') for x in result]
            # 将×作为分隔符，分割出单价和数量
            result = [x.split('x') for x in result]
            # 价格转换为浮点数，数量转换为整数
            result = [[float(x[0]), int(x[1])] for x in result]
            if len(result) < 10:
                result = -1
            return result
        except:
            return -1
        
    def Get_Random_Attribute(self, screen_shot_img):
        img = screen_shot_img[Random_Attribute_Text[1]:Random_Attribute_Text[1] + Random_Attribute_Text[3], Random_Attribute_Text[0]:Random_Attribute_Text[0] + Random_Attribute_Text[2]]
        # img = pyautogui.screenshot(region=(Random_Attribute[0], Random_Attribute[1], Random_Attribute[2], Random_Attribute[3]))
        result = OCR_Raw_ScreenShot(img)
        result = result.split('\n')
        try:
            result = [x for x in result if x]
            result = [x.replace(',', '') for x in result]
            result = [int(x) for x in result]
            if len(result) < 10:
                result = -1
            return result
        except:
            return -1
        
    # 定义函数检测是否购买商品成功
    def Check_Buy_Success(self):
        img = pyautogui.screenshot(region=(Buy_Success_Text[0], Buy_Success_Text[1], Buy_Success_Text[2], Buy_Success_Text[3]))
        result = OCR_Raw_ScreenShot(img)
        # Your purchase has been completed.The item has been delivered to your inventory or storage.
        if 'completed' in result:
            return True
        else:
            return False

    def Check_If_Sold(self):
        img = pyautogui.screenshot(region=(Item_Sold_Text[0], Item_Sold_Text[1], Item_Sold_Text[2], Item_Sold_Text[3]))
        result = OCR_Raw_ScreenShot(img)
        if 'sold' in result:
            return True
        else:
            return False
        
    def Check_Sure_to_Leave(self):
        img = pyautogui.screenshot(region=(Sure_to_Leave_Text[0], Sure_to_Leave_Text[1], Sure_to_Leave_Text[2], Sure_to_Leave_Text[3]))
        result = OCR_Raw_ScreenShot(img)
        if 'Are you sure to leave' in result:
            return True
        else:
            return False

    def Buy_Item(self, index, target_price):
        log_and_print(data['LogFilePath'], 'Buy Item:', index + 1)
        # 点击Buy按钮
        self.Press_Buy_Button(index)
        # 点击Fill All Items按钮
        self.press_Fill_All_Items_Button()
        time.sleep(0.01 + random.random() * 0.01)
        # 检测价格是否一致
        img = pyautogui.screenshot(region=(Final_Price_Text[0], Final_Price_Text[1], Final_Price_Text[2], Final_Price_Text[3]))
        final_price = OCR_Raw_ScreenShot(img)
        # ——————————————————————————————————————————————这里要优化↓
        # if ']' in final_price:
        #     log_and_print(data['LogFilePath'], 'final_price:', final_price, '价格不一致')
        #     time.sleep(2 + random.random() * 0.1)
        #     # 键盘按下esc键
        #     pyautogui.keyDown('esc')
        #     time.sleep(0.05 + random.random() * 0.1)
        #     pyautogui.keyUp('esc')
        #     time.sleep(1)
        #     if self.Check_Sure_to_Leave():
        #         log_and_print(data['LogFilePath'], '{}发生未知错误，试图离开交易界面'.format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())))
        #         pyautogui.keyDown('esc')
        #         time.sleep(0.05 + random.random() * 0.1)
        #         pyautogui.keyUp('esc')
        #     return
        if ']' in final_price:
            # 把]替换为1
            final_price = final_price.replace(']', '1')
        # ————————————————————————————————————————————————
        if str(target_price) not in final_price:
            log_and_print(data['LogFilePath'], 'final_price:', final_price, '价格不一致')
            time.sleep(2 + random.random() * 0.1)
            # 键盘按下esc键
            pyautogui.keyDown('esc')
            time.sleep(0.05 + random.random() * 0.1)
            pyautogui.keyUp('esc')
            time.sleep(1)
            if self.Check_Sure_to_Leave():
                log_and_print(data['LogFilePath'], '{}发生未知错误，试图离开交易界面'.format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())))
                pyautogui.keyDown('esc')
                time.sleep(0.05 + random.random() * 0.1)
                pyautogui.keyUp('esc')
            return
        else:
            log_and_print(data['LogFilePath'], 'final_price:', final_price, '价格一致，购买中......', end='')
            # time.sleep(random.random() * 0.01)
            # 点击Complete Trade按钮
            self.press_Complete_Trade_Button()
            time.sleep(2 + random.random() * 0.1)
            if self.Check_Buy_Success():
                log_and_print(data['LogFilePath'], '购买成功')
                state = 1
            elif self.Check_If_Sold():
                log_and_print(data['LogFilePath'], '物品已售出')
                state = 0
            else:
                log_and_print(data['LogFilePath'], '未知错误（即未购买成功，也未售出）')
                state = -1
            # 键盘按下esc键
            pyautogui.keyDown('esc')
            time.sleep(0.05 + random.random() * 0.1)
            pyautogui.keyUp('esc')
            time.sleep(0.2 + random.random() * 0.1)
            return state
        
    def Check_Filter_Text(self, screen_shot_img, attribute_text):
        if type(attribute_text) != np.ndarray:
            screen_shot_img = np.array(screen_shot_img)
        img = screen_shot_img[attribute_text[1]:attribute_text[1] + attribute_text[3], attribute_text[0]:attribute_text[0] + attribute_text[2]]
        result = OCR_Raw_ScreenShot(img)
        result = result.replace('\n', '')
        return result

    def Check_Item_Name(self, screen_shot_img):
        return self.Check_Filter_Text(screen_shot_img, Item_Name_Chosen_Text)

    def Check_Rarity(self, screen_shot_img):
        return self.Check_Filter_Text(screen_shot_img, Rarity_Chosen_Text)

    def Check_Slot(self, screen_shot_img):
        return self.Check_Filter_Text(screen_shot_img, Slot_Chosen_Text)

    def Check_Type(self, screen_shot_img):
        return self.Check_Filter_Text(screen_shot_img, Type_Chosen_Text)

    def Check_Static_Attribute(self, screen_shot_img):
        return self.Check_Filter_Text(screen_shot_img, Static_Attribute_Chosen_Text)

    def Check_Random_Attribute(self, screen_shot_img):
        return self.Check_Filter_Text(screen_shot_img, Random_Attribute_Chosen_Text)


class Dark_Log_Output:
    def __init__(self) -> None:
        pass

    def Print_Random_Attribute(self, rand_attrs):
        for i in range(71):
            log_and_print(data['LogFilePath'], '-', end='')
        log_and_print(data['LogFilePath'], )
        for rand_attr in rand_attrs:
            log_and_print(data['LogFilePath'], rand_attr, end=' ')
        log_and_print(data['LogFilePath'], )
        for i in range(71):
            log_and_print(data['LogFilePath'], '-', end='')
        log_and_print(data['LogFilePath'], )
    
    def Print_Prices(self, prices):
        for i in range(71):
            log_and_print(data['LogFilePath'], '-', end='')
        log_and_print(data['LogFilePath'], '\nPrices:    ', end='')
        # 用表格打印，方便观察，每个数字之间用|分隔，占位符为5个字符
        for price in prices:
            log_and_print(data['LogFilePath'], f'|{price:5}', end='')
        log_and_print(data['LogFilePath'], )
        for i in range(71):
            log_and_print(data['LogFilePath'], '-', end='')
        log_and_print(data['LogFilePath'], )
    
    def Print_Random_Attribute_and_Prices(self, rand_attrs, prices):
        for i in range(71):
            log_and_print(data['LogFilePath'], '-', end='')
        # 用表格打印，方便观察，每个数字之间用|分隔，占位符为5个字符
        log_and_print(data['LogFilePath'], '\nPrices:    ', end='')
        for price in prices:
            log_and_print(data['LogFilePath'], f'|{price:5}', end='')
        log_and_print(data['LogFilePath'], '\nRand_Attrs:', end='')
        for rand_attr in rand_attrs:
            log_and_print(data['LogFilePath'], f'|{rand_attr:5}', end='')
        log_and_print(data['LogFilePath'], )
        for i in range(71):
            log_and_print(data['LogFilePath'], '-', end='')
        log_and_print(data['LogFilePath'], )
    

class BaseItemFunc:
    def __init__(self, item_func_name, item_name = '-1', rarity = '-1', slot = '-1', type = '-1', static_attribute = '-1', random_attribute = '-1', target_prices_chart = {}) -> None:
        """
        :param item_func_name: 物品功能函数名，如Ring_AdditionalMagicalDamage
        """
        self.item_func_name = item_func_name
        self.Item_Name = item_name
        self.Rarity = rarity
        self.Slot = slot
        self.Type = type
        self.Static_Attribute = static_attribute
        self.Random_Attribute = random_attribute
        if item_func_name in target_prices_chart:
            self.target_prices = target_prices_chart[self.item_func_name]
        else:
            self.target_prices = -1
            print('Error: 未找到对应的价格表')

    # 条件检测函数
    def check_filter_condition(self, game_op: Dark_Game_Operation, screen_shot_img):
        """
        检测是否满足购买条件
        :param game_op: Dark_Game_Operation类的实例
        :param screen_shot_img: 当前屏幕的完整截图
        """
        attributes = ['Item_Name', 'Rarity', 'Slot', 'Type', 'Static_Attribute', 'Random_Attribute']
        check_methods = [game_op.Check_Item_Name, game_op.Check_Rarity, game_op.Check_Slot, game_op.Check_Type, game_op.Check_Static_Attribute, game_op.Check_Random_Attribute]
        for attr, method in zip(attributes, check_methods):
            if getattr(self, attr) != '-1' and getattr(self, attr) not in method(screen_shot_img):
                return False
        return True

    def get_price_threshold(self, rand_attr):
        """
        根据随机属性获取价格阈值"""
        # 先解析一下价格表，获取随机属性范围对应的最大价格
        additional_attr2max_price = self.target_prices["additional_attr2max_price"]
        # 随机属性范围
        additional_attrs = [-1]
        additional_attrs.extend(list(additional_attr2max_price.keys()))
        # 查找一下，把additional_attrs中的'*'替换为65535
        additional_attrs = [x if x != '*' else int(65535) for x in additional_attrs]
        # 检查additional_attrs是否增序
        for i in range(len(additional_attrs) - 1):
            if additional_attrs[i] >= additional_attrs[i + 1]:
                print('ERROR - 随机属性范围不是增序，请检查价格表')
                return -1
        # 价格上限
        max_prices = list(additional_attr2max_price.values())
        for i in range(len(additional_attrs) - 1):
            if additional_attrs[i] < rand_attr <= additional_attrs[i + 1]:
                return max_prices[i]
        print('ERROR - 价格表未包含该随机属性{}, 请检查价格表'.format(rand_attr))
        return -1

    def MixedLogic_Buy(self, game_op: Dark_Game_Operation, prices, rand_attrs):
        """
        根据价格表购买，考虑随机属性
        :param game_op: Dark_Game_Operation类的实例
        :param prices: 当前市场价格序列
        :param rand_attrs: 当前市场随机属性序列
        return: 是否购买成功
        """
        # 依次遍历prices，如果有满足价格表条件的，购买
        for i in range(len(prices)):
            if self.get_price_threshold(rand_attrs[i]) >= prices[i]:
                ringing()
                try:
                    state = game_op.Buy_Item(i, prices[i])
                    if state == 1:
                        log_and_print(data['LogFilePath'], '***已购买{0}，价格：[{1}]，随机属性：[{2}]***'.format(self.item_func_name, prices[i], rand_attrs[i]))
                        check_buy_times()
                except Exception as e:
                    log_and_print(data['LogFilePath'], e)
                game_op.Press_Search_Button()
                return True
        return False

    def OnlyMax_Buy(self, game_op: Dark_Game_Operation, prices):
        """
        仅购买价格阈值下的最低价格物品，不考虑随机属性
        :param game_op: Dark_Game_Operation类的实例
        :param prices: 当前市场价格序列
        return: 是否购买成功
        """
        min_price = min(prices)
        min_price_index = prices.index(min_price)
        if min_price <= self.target_prices['max_price']:
            ringing()
            try:
                state = game_op.Buy_Item(min_price_index, min_price)
                if state == 1:
                    log_and_print(data['LogFilePath'], '***已购买{0}，价格：[{1}]***'.format(self.Item_Name, min_price))
                    check_buy_times()
            except Exception as e:
                log_and_print(data['LogFilePath'], e)
            game_op.Press_Search_Button()
            return True
        return False
        

class Ring_AdditionalMagicalDamage_Func(BaseItemFunc):
    def __init__(self, target_prices_chart) -> None:
        super().__init__(   item_func_name='Ring_AdditionalMagicalDamage', 
                            slot='Ring', 
                            random_attribute='Additional Magical Damage', 
                            target_prices_chart=target_prices_chart)

class Ring_TrueMagicalDamage_Func(BaseItemFunc):
    def __init__(self, target_prices_chart) -> None:
        super().__init__(   item_func_name='Ring_TrueMagicalDamage', 
                            slot='Ring', 
                            random_attribute='True Magical Damage', 
                            target_prices_chart=target_prices_chart)
        
class Ring_AdditionalPhysicalDamage_Func(BaseItemFunc):
    def __init__(self, target_prices_chart) -> None:
        super().__init__(   item_func_name='Ring_AdditionalPhysicalDamage', 
                            slot='Ring', 
                            random_attribute='Additional Physical Damage', 
                            target_prices_chart=target_prices_chart)

class Surgicalkit_Func(BaseItemFunc):
    def __init__(self, target_prices_chart) -> None:
        super().__init__(   item_func_name='Surgicalkit', 
                            item_name='Surgical kit', 
                            target_prices_chart=target_prices_chart)
        
class Gold_Coin_Bag_Func(BaseItemFunc):
    def __init__(self, target_prices_chart) -> None:
        super().__init__(   item_func_name='Gold_Coin_Bag', 
                            item_name='Gold Coin Bag', 
                            target_prices_chart=target_prices_chart)
        


class Dark_and_Darker_Appliaction:
    def __init__(self, data) -> None:
        self.game_op = Dark_Game_Operation()
        self.output = Dark_Log_Output()
        self.data = data
        log_and_print(data['LogFilePath'], 'buy_times已初始化，当前值:', data['buy_times'])

    
    def Dark_and_Darker_buy_Protection(self, max_price_low):
        log_and_print(data['LogFilePath'], '正在运行Buy Protection程序...等待Dark and Darker启动...')
        print_flag = True
        while True:
            time.sleep(1)
            if data['end_flag']:
                return
            if data['pause_flag']:
                if print_flag:
                    log_and_print(data['LogFilePath'], '已暂停...按下page up键继续...')
                    print_flag = False
                continue
            print_flag = True
            if 'Dark and Darker' in pyautogui.getActiveWindow().title:
                log_and_print(data['LogFilePath'], 'Dark and Darker is running...')
                # 检测物品名称是否为Protection
                if 'Protection' not in self.game_op.Check_Item_Name():
                    time.sleep(1)
                    continue
                else:
                    self.game_op.Press_Search_Button()
                    time.sleep(1 + random.random() * 0.5)
                    old_prices = []
                    while True:
                        if data['end_flag']:
                            return
                        if data['pause_flag']:
                            break
                        if 'Dark and Darker' not in pyautogui.getActiveWindow().title:
                            log_and_print(data['LogFilePath'], 'Dark and Darker is not running...')
                            break
                        time.sleep(0.05 + random.random() * 0.05)
                        prices = self.game_op.Get_Prices()
                        details_prices = self.game_op.Get_Detailed_Prices()
                        # 如果prices不为-1，即识别成功
                        if prices != -1:
                            # 如果价格有变化，打印出来
                            if prices != old_prices:
                                self.output.Print_Prices(prices)
                            old_prices = prices
                            # 如果有价格小于等于max_price_low，点击购买按钮
                            target_item_index = prices.index(min(prices))
                            # 并且购买数量等于3，并且单价乘以3约等于max_price_low（差值小于max_price_low的1/10）
                            if min(prices) <= max_price_low and details_prices[target_item_index][1] == 3 and abs(prices[target_item_index] * 3 - max_price_low) < max_price_low / 10:
                                ringing()
                                try:
                                    state = self.game_op.Buy_Item(target_item_index, prices[target_item_index])
                                    if state == 1:
                                        log_and_print(data['LogFilePath'], '***已购买Protection，价格：[{0}]，数量：[{1}]***'.format(prices[target_item_index], details_prices[target_item_index][1]))
                                        check_buy_times()
                                except Exception as e:
                                    log_and_print(data['LogFilePath'], e)
                                self.game_op.Press_Search_Button()
                                break
                        time.sleep(0.05 + random.random() * 0.1)
                        self.game_op.Press_Search_Button()
    
    def Dark_and_Darker_BuyItem(self, item_func: BaseItemFunc):
        """
        本函数用于对以上功能函数如Dark_and_Darker_buy_ring_TrueMagicDamage进行重构，增强通用性
        :param item_function: 功能函数，如Ring_AdditionalMagicDamage
        :param target_prices: 目标价格表，规定了不同类型物品的价格上限，如随机属性AdditionalMagicDamage为1的Ring的价格上限
        """
        log_and_print(data['LogFilePath'], '正在运行Buy {0}程序...等待Dark and Darker启动...'.format(item_func.item_func_name))
        print_flag = True
        while True:
            time.sleep(0.5 + random.random() * 0.5)
            if data['end_flag']:
                return
            if data['pause_flag']:
                if print_flag:
                    log_and_print(data['LogFilePath'], '已暂停...按下page up键继续...')
                    print_flag = False
                continue
            print_flag = True

            if 'Dark and Darker' in pyautogui.getActiveWindow().title:
                log_and_print(data['LogFilePath'], 'Dark and Darker is running...')
                screen_shot_img = pyautogui.screenshot()
                # 检测筛选条件是否符合，若不符合，等待1s
                if not item_func.check_filter_condition(self.game_op, screen_shot_img):
                    time.sleep(1)
                    continue
                else:
                    self.game_op.Press_Search_Button()
                    time.sleep(1 + random.random() * 0.5)
                    old_prices = []
                    old_rand_attrs = []
                    while True:
                        if data['end_flag']:
                            return
                        if data['pause_flag']:
                            log_and_print(data['LogFilePath'], '已暂停...按下page up键继续...')
                            break
                        if 'Dark and Darker' not in pyautogui.getActiveWindow().title:
                            log_and_print(data['LogFilePath'], 'Dark and Darker is not running...')
                            break
                        time.sleep(0.01 + random.random() * 0.02)
                        screen_shot_img = pyautogui.screenshot()
                        screen_shot_img = np.array(screen_shot_img)
                        prices = self.game_op.Get_Prices(screen_shot_img)
                        if not item_func.target_prices['only_max_price']:
                            rand_attrs = self.game_op.Get_Random_Attribute(screen_shot_img)
                        else:
                            rand_attrs = [-1] * 10
                        # 如果prices和rand_attrs都不为-1
                        if prices != -1 and rand_attrs != -1:
                            # 如果价格或者随机属性有变化，打印出来
                            if prices != old_prices or rand_attrs != old_rand_attrs:
                                self.output.Print_Random_Attribute_and_Prices(rand_attrs, prices)
                            old_prices = prices
                            old_rand_attrs = rand_attrs
                            # 如果不仅仅是最大价格，调用MixedLogic_Buy
                            if not item_func.target_prices['only_max_price']:
                                if item_func.MixedLogic_Buy(self.game_op, prices, rand_attrs):
                                    break
                            else:
                                if item_func.OnlyMax_Buy(self.game_op, prices):
                                    break
                        time.sleep(0.03 + random.random() * 0.05)
                        self.game_op.Press_Search_Button()



def Listen_KeyBoard(data_input):
    def KeyBoard_CallBack(key):
        if key == pynput.keyboard.Key.end:  # 结束程序 End 键
            winsound.Beep(400, 200)
            data_input['end_flag'] = True
            return False
        elif key == pynput.keyboard.Key.page_up:  # 开始程序 PgUp 键
            winsound.Beep(600, 200)
            data_input['pause_flag'] = False
            return False
        elif key == pynput.keyboard.Key.home:  # 暂停程序 Home 键
            winsound.Beep(700, 200)
            data_input['pause_flag'] = True
            return True
        elif key == pynput.keyboard.Key.page_down:  # 增加购买次数 PgDown 键
            winsound.Beep(800, 200)
            data_input['buy_times'] += 1
            log_and_print(data_input['LogFilePath'], 'buy_times已增加，当前值:', data_input['buy_times'])
            return True
    while not data_input['end_flag']:
        log_and_print(data_input['LogFilePath'], '正在检测键盘按键，按下Home键暂停，按下End键结束，按下PgUp键开始， 按下PgDown键增加购买次数...')
        with pynput.keyboard.Listener(on_release=KeyBoard_CallBack) as k:
            k.join()
            log_and_print(data_input['LogFilePath'], 'pause_flag:', data_input['pause_flag'], 'end_flag:', data_input['end_flag'])


if __name__ == '__main__':
    target_prices_chart = {
        'Ring_AdditionalMagicalDamage': {
            'only_max_price': False,
            # 代表随机属性[0, 1]的价格上限为65，(1, 2]的价格上限为100，(2, 3]的价格上限为150，(3, ∞)的价格上限为150
            'additional_attr2max_price': {
                1   : 85,
                2   : 145,
                3   : 211,
                '*' : 211
            }
        },
        'Ring_TrueMagicalDamage': {
            'only_max_price': False,
            'additional_attr2max_price': {
                1   : 60,
                2   : 180,
                '*' : 180
            }
        },
        'Ring_AdditionalPhysicalDamage': {
            'only_max_price': False,
            'additional_attr2max_price': {
                1   : 75,
                2   : 100,
                3   : 150,
                '*' : 150
            }
        },
        'Surgicalkit': {
            'only_max_price': True,
            'max_price': 100
        },
        'Protection': {
            'only_max_price': True,
            'max_price': 75
        },
        'Gold_Coin_Bag': {
            'only_max_price': True,
            'max_price': 4400
        }
    }


    # 用于测试
    # dark_game = Dark_Game_Operation()
    # dark_game.Press_Search_Button()
    # dark_game.Press_Buy_Button(0)
    # dark_game.press_Fill_All_Items_Button()
    # dark_game.press_Complete_Trade_Button()
    # img = pyautogui.screenshot()
    # img = np.array(img)
    # # r = dark_game.Get_Detailed_Prices(img)
    # r = dark_game.Get_Prices(img)
    # print(r)
    # print(dark_game.Get_Random_Attribute(img))
    # multiprocessing.freeze_support()
    # manager = multiprocessing.Manager()
    # data = manager.dict()
    # data.update(init)
    # queue = manager.Queue(10)
    # time.sleep(3)
    # # try:
    # for i in range(10):
    #     dark_game.Press_Search_Button()
    #     dark_game.Buy_Item(i, i *8888)
    #     time.sleep(1)

    # # except Exception as e:
    # #     print(e)
    # #     a = input('按任意键结束')
    # exit()

    multiprocessing.freeze_support()
    manager = multiprocessing.Manager()
    data = manager.dict()
    data.update(init)
    queue = manager.Queue(10)

    pk = Process(target=Listen_KeyBoard, args=(data,), name='Listen_KeyBoard')
    pweb = Process(target=Open_Web_Service, args=(data,), name='Open_Web_Service')
    pk.start()
    pweb.start()

    dark_game = Dark_and_Darker_Appliaction(data)
    parser = argparse.ArgumentParser()
    parser.add_argument('--Ring_AdditionalPhysicalDamage', action='store_true')
    parser.add_argument('--Ring_TrueMagicalDamage', action='store_true')
    parser.add_argument('--Ring_AdditionalMagicalDamage', action='store_true')
    parser.add_argument('--Surgicalkit', action='store_true')
    parser.add_argument('--Gold_Coin_Bag', action='store_true')
    # 如果没有传入参数，使用默认参数
    args = parser.parse_args()
    if not args:
        dark_game.Dark_and_Darker_BuyItem(Ring_AdditionalMagicalDamage_Func(target_prices_chart))
    if args.Ring_AdditionalMagicalDamage:
        dark_game.Dark_and_Darker_BuyItem(Ring_AdditionalMagicalDamage_Func(target_prices_chart))
    if args.Ring_TrueMagicalDamage:
        dark_game.Dark_and_Darker_BuyItem(Ring_TrueMagicalDamage_Func(target_prices_chart))
    if args.Ring_AdditionalPhysicalDamage:
        dark_game.Dark_and_Darker_BuyItem(Ring_AdditionalPhysicalDamage_Func(target_prices_chart))
    if args.Surgicalkit:
        dark_game.Dark_and_Darker_BuyItem(Surgicalkit_Func(target_prices_chart))
    if args.Gold_Coin_Bag:
        dark_game.Dark_and_Darker_BuyItem(Gold_Coin_Bag_Func(target_prices_chart))
    # dark_game.Dark_and_Darker_BuyItem(Ring_TrueMagicalDamage_Func(target_prices_chart))
    # dark_game.Dark_and_Darker_BuyItem(Ring_AdditionalPhysicalDamage_Func(target_prices_chart))
    # dark_game.Dark_and_Darker_BuyItem(Surgicalkit_Func(target_prices_chart))
    # dark_game.Dark_and_Darker_BuyItem(Gold_Coin_Bag_Func(target_prices_chart))

    # dark_game.Dark_and_Darker_buy_ring_TrueMagicDamage(2, 200, 100)
    # dark_game.Dark_and_Darker_buy_ring_AdditionalMagicDamage(3, 150, 65)
    
    # dark_game.Dark_and_Darker_buy_Surgicalkit(10)
    # dark_game.Dark_and_Darker_buy_Protection(75)
    # dark_game.Dark_and_Darker_buy_Gold_Coin_Bag(2500)
    pk.join()
    pweb.join()

