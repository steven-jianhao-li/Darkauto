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
from Functions import log_and_print

# 所有按钮的位置坐标均以2k分辨率为基准
Search_button = (2315, 357, 153, 28)
# 按钮位置
first_Buy_buttons = (2325, 468, 130, 17)        # 第一个Buy按钮的位置，其余按钮坐标从上向下y坐标依次递减87
Buy_buttons_decrease_y = 87
Fill_All_Items_button = (1147, 986, 250, 65)
Complete_Trade_button = (1151, 1101, 250, 52)
# 静态文本位置
Prices = (1986, 441, 93, 850)
Detailed_Prices = (2136, 464, 130, 812)
Random_Attribute = (1495, 441, 112, 850)
# Final_Price = (1383, 877, 168, 37) # 这个是小字，不好识别
Final_Price = (255, 695, 275, 69)
Slot_Chosen = (818, 263, 234, 30)
Item_Name_Chosen = (106, 263, 234, 24)
Random_Attribute_Chosen = (1895, 263, 234, 23)
Item_Sold = (986, 177, 590, 58)
Buy_Success = (908, 596, 744, 152)

# 初始化数据
# 当前python文件的路径
File_Path = os.path.abspath(os.path.dirname(__file__))
init = {
    'pause_flag': False,
    'end_flag': False,
    'buy_times': 2,
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

def ringing():
    # winsound.Beep(1000, 100)
    pass

def OCR_image(img, only_number=False):
    # 将图片转换为灰度图
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # 将图片转换为二值图，参数解释：https://blog.csdn.net/weixin_42272768/article/details/110746790
    _, img = cv2.threshold(img, 109, 255, cv2.THRESH_BINARY)
    # 使用tesseract识别图片中的数字
    if only_number:
        result = pytesseract.image_to_string(img, config=r'-c tessedit_char_whitelist=0123456789, --psm 6 --oem 3')
    else:
        result = pytesseract.image_to_string(img, config='--psm 6')
    return result

def print_tkui(strs):
    """ 打包控制台输出 """
    log_and_print(data['LogFilePath'], strs)

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
    # Q: 我想让鼠标移动的速度更加平滑，所以我使用了PID控制器，我想加快移动速度，所以参数我应该如何调整？
    # A: 你可以调整P、I、D的值，P是比例，I是积分，D是微分，P是控制鼠标移动速度的，I是控制鼠标移动的平滑度的，D是控制鼠标移动的稳定性的。
    def __init__(self, P=0.2, I=0, D=0):
        """PID"""
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
    
    def mouse_move_not_pid(self, end_xy, max_xy=30, min_time=0.001):
        if not self.state:
            return
        end_x, end_y = end_xy
        # 创建pid对象
        pid_x = PID() 
        pid_y = PID()

        while True: # 循环控制鼠标直到重合坐标
            microsecond_sleep(10000)
            new_x, new_y = pyautogui.position() # 获取当前鼠标位置

            move_x = pid_x.pidPosition(end_x, new_x) # 经过pid计算鼠标运动量
            move_y = pid_y.pidPosition(end_y, new_y)
            # 如果近似重合就退出循环
            if end_x - new_x < 2 and end_y - new_y < 2:
                break
            
            if move_x > (max_xy): # 如果鼠标移动量大于0并且小于最大移动量
                move_x = (max_xy + random.randrange(-10, 10))
            elif move_x < -(max_xy): # 如果鼠标移动量小于0并且大于最大移动量的负数
                move_x = -(max_xy + random.randrange(-10, 10))
            else:
                move_x = int(move_x)
            if move_y > (max_xy):
                move_y = (max_xy + random.randrange(-10, 10))
            elif move_y < -(max_xy):
                move_y = -(max_xy + random.randrange(-10, 10))
            else:
                move_y = int(move_y)

            print_tkui(f'当前坐标: {new_x, new_y}, 移动量: {move_x, move_y}')
            self.dll.moveR(move_x, move_y, True) # 貌似有第三个参数,但是没试出来什么用
    
    def mouse_move(self, end_xy, min_xy=1, min_time=0.01):
        if not self.state:
            return
        end_x, end_y = end_xy

        pid_x = PID() # 创建pid对象
        pid_y = PID()
        # 循环控制鼠标直到重合坐标，最多50次
        for i in range(120):
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
    def __init__(self, min_time=0.01):
        self.min_time = min_time
        self.logitech = LOGITECH()

    def move_to_left_click(self, x, y, min_time):
        move_flag = self.logitech.mouse_move((x, y), min_time=min_time)
        if move_flag:
            self.logitech.mouse_left_click()
        
    def rand_move_to_left_click(self, x, y, rand_x, rand_y):
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
        # 截取左上坐标(1986,441)开始，宽度93，高度850的画面
        # 截取的画面保存到当前目录下的screen.png，region参数是一个元组，元组的第一个元素是截图的左上角的x坐标，第二个元素是截图的左上角的y坐标，第三个元素是截图的宽度，第四个元素是截图的高度
        img = screen_shot_img[Prices[1]:Prices[1] + Prices[3], Prices[0]:Prices[0] + Prices[2]]
        # img = pyautogui.screenshot(region=(Prices[0], Prices[1], Prices[2], Prices[3]))
        # 类型转换，将screenshot返回的PIL.Image.Image转换为cv2的图像格式
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        # 使用tesseract识别图片中的数字
        result = OCR_image(img, only_number=True)
        # 转换识别结果为数组
        result = result.split('\n')
        try:
            # 清空空元素
            result = [x for x in result if x]
            # 将识别结果中的,去掉
            result = [x.replace(',', '') for x in result]
            result = [int(x) for x in result]
            if len(result) < 10:
                result = -1
            return result
        except:
            return -1
    
    def Get_Detailed_Prices(self, screen_shot_img):
        img = screen_shot_img[Detailed_Prices[1]:Detailed_Prices[1] + Detailed_Prices[3], Detailed_Prices[0]:Detailed_Prices[0] + Detailed_Prices[2]]
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        result = OCR_image(img)
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
        img = screen_shot_img[Random_Attribute[1]:Random_Attribute[1] + Random_Attribute[3], Random_Attribute[0]:Random_Attribute[0] + Random_Attribute[2]]
        # img = pyautogui.screenshot(region=(Random_Attribute[0], Random_Attribute[1], Random_Attribute[2], Random_Attribute[3]))
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        result = OCR_image(img)
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
        img = pyautogui.screenshot(region=(Buy_Success[0], Buy_Success[1], Buy_Success[2], Buy_Success[3]))
        img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        result = OCR_image(img)
        # Your purchase has been completed.The item has been delivered to your inventory or storage.
        if 'completed' in result:
            return True
        else:
            return False

    def Check_If_Sold(self):
        img = pyautogui.screenshot(region=(Item_Sold[0], Item_Sold[1], Item_Sold[2], Item_Sold[3]))
        img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        result = OCR_image(img)
        if 'sold' in result:
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
        img = pyautogui.screenshot(region=(Final_Price[0], Final_Price[1], Final_Price[2], Final_Price[3]))
        img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        final_price = OCR_image(img)
        # ——————————————————————————————————————————————这里要优化↓
        if ']' in final_price:
            log_and_print(data['LogFilePath'], 'final_price:', final_price, '价格不一致')
            time.sleep(2 + random.random() * 0.1)
            # 键盘按下esc键
            pyautogui.keyDown('esc')
            time.sleep(0.05 + random.random() * 0.1)
            pyautogui.keyUp('esc')
            return
        # ————————————————————————————————————————————————
        if str(target_price) not in final_price:
            log_and_print(data['LogFilePath'], 'final_price:', final_price, '价格不一致')
            time.sleep(2 + random.random() * 0.1)
            # 键盘按下esc键
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
        
    def Check_Slot(self):
        img = pyautogui.screenshot(region=(Slot_Chosen[0], Slot_Chosen[1], Slot_Chosen[2], Slot_Chosen[3]))
        # 类型转换，将screenshot返回的PIL.Image.Image转换为cv2的图像格式
        img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        result = OCR_image(img)
        result = result.replace('\n', '')
        return result
    def Check_Item_Name(self):
        img = pyautogui.screenshot(region=(Item_Name_Chosen[0], Item_Name_Chosen[1], Item_Name_Chosen[2], Item_Name_Chosen[3]))
        img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        result = OCR_image(img)
        result = result.replace('\n', '')
        return result
    def Check_Random_Attribute(self):
        img = pyautogui.screenshot(region=(Random_Attribute_Chosen[0], Random_Attribute_Chosen[1], Random_Attribute_Chosen[2], Random_Attribute_Chosen[3]))
        img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        result = OCR_image(img)
        result = result.replace('\n', '')
        return result

            
    
class Output:
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
    

class Dark_and_Darker_Appliaction:
    def __init__(self, data) -> None:
        self.game = Dark_Game_Operation()
        self.output = Output()
        self.data = data
        log_and_print(data['LogFilePath'], 'buy_times已初始化，当前值:', data['buy_times'])
    def Dark_and_Darker_buy_ring_TrueMagicDamage(self, min_rand_attrs, max_price_target, max_price_low):
        """
        min_rand_attrs: 最小随机属性roll值
        max_price_target: 满足最小随机属性roll值的最大预算
        max_price_low: 无需满足最小随机属性roll值的最大预算
        """
        log_and_print(data['LogFilePath'], '正在运行Buy Ring程序...等待Dark and Darker启动...')
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
                # 检测部位是否为Ring
                if 'Ring' not in self.game.Check_Slot():
                    # log_and_print(data['LogFilePath'], 'Slot is not Ring. Waiting for 1s...')
                    time.sleep(1)
                    continue
                else:
                    self.game.Press_Search_Button()
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
                        time.sleep(0.05 + random.random() * 0.05)
                        prices = self.game.Get_Prices()
                        rand_attrs = self.game.Get_Random_Attribute()
                        # 如果prices和rand_attrs都不为-1
                        if prices != -1 and rand_attrs != -1:
                            # 如果价格或者随机属性有变化，打印出来
                            if prices != old_prices or rand_attrs != old_rand_attrs:
                                self.output.Print_Random_Attribute_and_Prices(rand_attrs, prices)
                            old_prices = prices
                            old_rand_attrs = rand_attrs
                            # 如果rand_attrs有大于min_rand_attrs的值，且价格小于max_price_target，点击购买按钮
                            target_item_index = rand_attrs.index(max(rand_attrs))
                            if rand_attrs[target_item_index] >= min_rand_attrs and prices[target_item_index] <= max_price_target:
                                    ringing()
                                    try:
                                        state = self.game.Buy_Item(target_item_index, prices[target_item_index])
                                        if state == 1:
                                            log_and_print(data['LogFilePath'], '***已购买Ring，价格：[{0}]，随机属性：[{1}]***'.format(prices[target_item_index], rand_attrs[target_item_index]))
                                            check_buy_times()
                                    except Exception as e:
                                        log_and_print(data['LogFilePath'], e)
                                    self.game.Press_Search_Button()
                                    break
                            # 如果有价格小于等于max_price_low，点击购买按钮
                            target_item_index = prices.index(min(prices))
                            if min(prices) <= max_price_low:
                                ringing()
                                try:
                                    state = self.game.Buy_Item(target_item_index, prices[target_item_index])
                                    if state == 1:
                                        log_and_print(data['LogFilePath'], '***已购买Ring，价格：[{0}]，随机属性：[{1}]***'.format(prices[target_item_index], rand_attrs[target_item_index]))
                                        check_buy_times()
                                except Exception as e:
                                    log_and_print(data['LogFilePath'], e)
                                
                                self.game.Press_Search_Button()
                                break
                        time.sleep(0.05 + random.random() * 0.1)
                        self.game.Press_Search_Button()

    def Dark_and_Darker_buy_ring_AdditionMagicDamage(self, min_rand_attrs, max_price_target, max_price_low):
        """
        min_rand_attrs: 最小随机属性roll值
        max_price_target: 满足最小随机属性roll值的最大预算
        max_price_low: 无需满足最小随机属性roll值的最大预算
        """
        log_and_print(data['LogFilePath'], '正在运行Buy Ring程序...等待Dark and Darker启动...')
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
                # 检测部位是否为Ring
                if 'Ring' not in self.game.Check_Slot():
                    # log_and_print(data['LogFilePath'], 'Slot is not Ring. Waiting for 1s...')
                    time.sleep(1)
                    continue
                else:
                    self.game.Press_Search_Button()
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
                        prices = self.game.Get_Prices(screen_shot_img)
                        rand_attrs = self.game.Get_Random_Attribute(screen_shot_img)
                        # 如果prices和rand_attrs都不为-1
                        if prices != -1 and rand_attrs != -1:
                            # 如果价格或者随机属性有变化，打印出来
                            if prices != old_prices or rand_attrs != old_rand_attrs:
                                self.output.Print_Random_Attribute_and_Prices(rand_attrs, prices)
                            old_prices = prices
                            old_rand_attrs = rand_attrs
                            # 如果rand_attrs有大于min_rand_attrs的值，且价格小于max_price_target，点击购买按钮
                            target_item_index = rand_attrs.index(max(rand_attrs))
                            if rand_attrs[target_item_index] >= min_rand_attrs and prices[target_item_index] <= max_price_target:
                                ringing()
                                try:
                                    state = self.game.Buy_Item(target_item_index, prices[target_item_index])
                                    if state == 1:
                                        log_and_print(data['LogFilePath'], '***已购买Ring，价格：[{0}]，随机属性：[{1}]***'.format(prices[target_item_index], rand_attrs[target_item_index]))
                                        check_buy_times()
                                except Exception as e:
                                    log_and_print(data['LogFilePath'], e)
                                self.game.Press_Search_Button()
                                break
                            # 如果有价格小于等于max_price_low，点击购买按钮
                            target_item_index = prices.index(min(prices))
                            if min(prices) <= max_price_low:
                                ringing()
                                try:
                                    state = self.game.Buy_Item(target_item_index, prices[target_item_index])
                                    if state == 1:
                                        log_and_print(data['LogFilePath'], '***已购买Ring，价格：[{0}]，随机属性：[{1}]***'.format(prices[target_item_index], rand_attrs[target_item_index]))
                                        check_buy_times()
                                except Exception as e:
                                    log_and_print(data['LogFilePath'], e)
                                self.game.Press_Search_Button()
                                break
                        time.sleep(0.03 + random.random() * 0.05)
                        self.game.Press_Search_Button()
    
    def Dark_and_Darker_buy_Surgicalkit(self, max_price_low):
        log_and_print(data['LogFilePath'], '正在运行Buy Surgical kit程序...等待Dark and Darker启动...')
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
                # 检测物品名称是否为Surgical kit
                if 'Surgical Kit' not in self.game.Check_Item_Name():
                    time.sleep(1)
                    continue
                else:
                    self.game.Press_Search_Button()
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
                        prices = self.game.Get_Prices()
                        # 如果prices不为-1，即识别成功
                        if prices != -1:
                            # 如果价格有变化，打印出来
                            if prices != old_prices:
                                self.output.Print_Prices(prices)
                            old_prices = prices
                            # 如果有价格小于等于max_price_low，点击购买按钮
                            target_item_index = prices.index(min(prices))
                            if min(prices) <= max_price_low:
                                ringing()
                                try:
                                    state = self.game.Buy_Item(target_item_index, prices[target_item_index])
                                    if state == 1:
                                        log_and_print(data['LogFilePath'], '***已购买Surgical kit，价格：[{0}]***'.format(prices[target_item_index]))
                                        check_buy_times()
                                except Exception as e:
                                    log_and_print(data['LogFilePath'], e)
                                self.game.Press_Search_Button()
                                break
                        time.sleep(0.05 + random.random() * 0.1)
                        self.game.Press_Search_Button()
    
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
                if 'Protection' not in self.game.Check_Item_Name():
                    time.sleep(1)
                    continue
                else:
                    self.game.Press_Search_Button()
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
                        prices = self.game.Get_Prices()
                        details_prices = self.game.Get_Detailed_Prices()
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
                                    state = self.game.Buy_Item(target_item_index, prices[target_item_index])
                                    if state == 1:
                                        log_and_print(data['LogFilePath'], '***已购买Protection，价格：[{0}]，数量：[{1}]***'.format(prices[target_item_index], details_prices[target_item_index][1]))
                                        check_buy_times()
                                except Exception as e:
                                    log_and_print(data['LogFilePath'], e)
                                self.game.Press_Search_Button()
                                break
                        time.sleep(0.05 + random.random() * 0.1)
                        self.game.Press_Search_Button()
    
    def Dark_and_Darker_buy_Gold_Coin_Bag(self, max_price_low):
        log_and_print(data['LogFilePath'], '正在运行Buy Gold Coin Bag程序...等待Dark and Darker启动...')
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
                # 检测物品名称是否为Gold Coin Bag
                if 'Gold Coin Bag' not in self.game.Check_Item_Name():
                    time.sleep(1)
                    continue
                else:
                    self.game.Press_Search_Button()
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
                        screen_shot_img = pyautogui.screenshot()
                        screen_shot_img = np.array(screen_shot_img)
                        prices = self.game.Get_Prices(screen_shot_img)
                        # 如果prices不为-1，即识别成功
                        if prices != -1:
                            # 如果价格有变化，打印出来
                            if prices != old_prices:
                                self.output.Print_Prices(prices)
                            old_prices = prices
                            # 如果有价格小于等于max_price_low，点击购买按钮
                            target_item_index = prices.index(min(prices))
                            if min(prices) <= max_price_low:
                                ringing()
                                try:
                                    state = self.game.Buy_Item(target_item_index, prices[target_item_index])
                                    if state == 1:
                                        log_and_print(data['LogFilePath'], '***已购买Gold Coin Bag，价格：[{0}]***'.format(prices[target_item_index]))
                                        check_buy_times()
                                except Exception as e:
                                    log_and_print(data['LogFilePath'], e)
                                self.game.Press_Search_Button()
                                break
                        time.sleep(0.05 + random.random() * 0.1)
                        self.game.Press_Search_Button()



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
            log_and_print(data['LogFilePath'], 'buy_times已增加，当前值:', data_input['buy_times'])
            return True
    global data
    data = data_input.copy()
    while not data_input['end_flag']:
        log_and_print(data['LogFilePath'], '正在检测键盘按键，按下Home键暂停，按下End键结束，按下PgUp键开始， 按下PgDown键增加购买次数...')
        with pynput.keyboard.Listener(on_release=KeyBoard_CallBack) as k:
            k.join()
            log_and_print(data['LogFilePath'], 'pause_flag:', data_input['pause_flag'], 'end_flag:', data_input['end_flag'])



if __name__ == '__main__':
    # # 用于测试
    # dark_game = Dark_Game_Operation()
    # # dark_game.Press_Search_Button()
    # # dark_game.Press_Buy_Button(0)
    # # dark_game.press_Fill_All_Items_Button()
    # # dark_game.press_Complete_Trade_Button()
    # img = pyautogui.screenshot()
    # img = np.array(img)
    # # r = dark_game.Get_Detailed_Prices(img)
    # r = dark_game.Get_Prices(img)
    # print(r)
    # print(dark_game.Get_Random_Attribute(img))
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
    # dark_game.Dark_and_Darker_buy_ring_TrueMagicDamage(2, 200, 100)
    # dark_game.Dark_and_Darker_buy_ring_AdditionMagicDamage(3, 150, 65)
    
    # dark_game.Dark_and_Darker_buy_Surgicalkit(10)
    # dark_game.Dark_and_Darker_buy_Protection(75)
    dark_game.Dark_and_Darker_buy_Gold_Coin_Bag(2500)
    pk.join()
    pweb.join()




 