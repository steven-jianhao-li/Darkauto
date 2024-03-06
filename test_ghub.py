import time
import cv2
import os
import random
import easyocr

import ctypes # 调用dll文件
import tkinter as tk # python 内置库,需要安装时勾选安装IDE才会安装,坑爹
import pyautogui # 获取屏幕鼠标坐标


def print_tkui(strs):
    """ 打包控制台输出 """
    print(strs)

class PID:
    """PID"""
    def __init__(self, P=0.35, I=0, D=0):
        """PID"""
        self.kp = P # 比例 
        self.ki = I # 积分
        self.kd = D # 微分
        self.uPrevious = 0 # 上一次控制量
        self.uCurent = 0 # 这一次控制量
        self.setValue = 0 # 目标值
        self.lastErr = 0 # 上一次差值
        self.errSum = 0 # 所有差值的累加
        self.errSumLimit = 10 # 近两次的差值累加
        
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
    try:
        file_path = os.path.abspath(os.path.dirname(__file__)) # 当前路径
        dll = ctypes.CDLL(f'{file_path}/ghub_device.dll') # 打开路径文件
        state = (dll.device_open() == 1) # 启动, 并返回是否成功
        WAIT_TIME = 0.5 # 等待时间
        RANDOM_NUM = 0.1 # 最大时间随机数
        if not state:
            print('错误, 未找到GHUB或LGS驱动程序')
    except FileNotFoundError:
        print(f'错误, 找不到DLL文件')

    def __init__(self) -> None:
        pass

    @classmethod
    def mouse_down(self, code):
        """ 鼠标按下 code: 左 中 右 """
        if not self.state:
            return
        print_tkui(f'按下{code}键')
        if code == '左':
            code = 1
        elif code == '中':
            code = 2
        elif code == '右':
            code = 3
        else: # 默认
            code = 1 
        self.dll.mouse_down(code)

    @classmethod
    def mouse_up(self, code):
        """ 鼠标松开 code: 左 中 右 """
        if not self.state:
            return
        print_tkui(f'松开{code}键')
        if code == '左':
            code = 1
        elif code == '中':
            code = 2
        elif code == '右':
            code = 3
        else: # 默认
            code = 1 
        self.dll.mouse_up(code)
    
    @classmethod
    def mouse_click(self, code, wait_time=0):
        """ 鼠标点击 code: 左 中 右 """
        if wait_time == 0: # 如果没有规定等待时间
            wait_time = self.WAIT_TIME # 默认等待时间
        if wait_time != 0: # 如果等待时间不是0
            wait_time += random.uniform(0, self.RANDOM_NUM)
            time.sleep(wait_time) # 延时时间,秒,生成随机小数0~1.0
            
        if not self.state:
            return
        print_tkui(f'等待{wait_time:.2f}秒后, 点击{code}键')
        if code == '左':
            code = 1
        elif code == '中':
            code = 2
        elif code == '右':
            code = 3
        else: # 默认
            code = 1 

        self.dll.mouse_down(code)
        time.sleep(random.uniform(0, self.RANDOM_NUM)) # 延时时间,秒,生成随机小数0~1.0
        self.dll.mouse_up(code)
    @classmethod
    def mouse_move(self, end_xy, wait_time=0, min_xy=2, min_time=0.1):
        """
        等待多久后 缓慢移动 \n
        end_x       绝对横坐标 \n
        end_y       绝对纵坐标 \n
        time_s      等待时间 \n
        min_xy      最小移动控制量 \n
        min_time    最小移动时间 \n
        """
        if wait_time == 0: # 如果没有规定等待时间
            wait_time = self.WAIT_TIME # 默认等待时间
        if wait_time != 0: # 如果等待时间不是0
            wait_time += random.uniform(0, self.RANDOM_NUM)
            time.sleep(wait_time) # 延时时间,秒,生成随机小数0~1.0
        if not self.state: # 保护措施
            return
        
        end_x, end_y = end_xy
        print_tkui(f'等待{wait_time:.2f}秒后, 移动到坐标{(end_x, end_y)}')

        pid_x = PID() # 创建pid对象
        pid_y = PID()

        while True: # 循环控制鼠标直到重合坐标
            time.sleep(min_time) # 延时时间,秒,生成随机小数0~1.0
            new_x, new_y = pyautogui.position() # 获取当前鼠标位置

            move_x = pid_x.pidPosition(end_x, new_x) # 经过pid计算鼠标运动量
            move_y = pid_y.pidPosition(end_y, new_y)

            # print(f'x={new_x}, y={new_y}, xd={move_x}, yd={move_y}')
            if end_x == new_x and end_y == new_y: # 如果重合就退出循环
                break
            
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


def Mymain():
    """ 主函数 """
    logitech = LOGITECH() # 实例化罗技
    logitech.mouse_click('右') # 点击右键
    logitech.mouse_click('左') # 点击左键
    logitech.mouse_click('中') # 点击中键
    logitech.mouse_move((100, 100)) # 移动到坐标
    
    pass

Search_button = (2315, 357, 153, 28)

def Get_Prices():
    # 截取左上坐标(1986,441)开始，宽度93，高度850的画面
    # 截取的画面保存到当前目录下的screen.png，region参数是一个元组，元组的第一个元素是截图的左上角的x坐标，第二个元素是截图的左上角的y坐标，第三个元素是截图的宽度，第四个元素是截图的高度
    pyautogui.screenshot('screen.png', region=(1986, 441, 93, 850))
    # 将screen.png垂直分割为10个图片，保存到pic_split目录下，每个图片包含一个数字
    if not os.path.exists('pic_split'):
        os.mkdir('pic_split')
    img = cv2.imread('screen.png')
    for i in range(10):
        # 保存数字图片
        cv2.imwrite('pic_split/num' + str(i) + '.png', img[85 * i:85 * (i + 1), 0:93])
    # 识别图片中的数字
    img = cv2.imread('screen.png')
    # 将图片转换为灰度图
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # 将图片转换为二值图
    _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # 识别图片中的数字
    reader = easyocr.Reader(['en'], gpu=True)
    # 识别图片中的文字，detail=0表示只返回识别结果
    result = reader.readtext(img, detail=0)
    # 将识别结果中的,去掉
    result = [x.replace(',', '') for x in result]
    # 转换识别结果为数字
    result = [int(x) for x in result]
    if len(result) < 10:
        result = -1
    return result
    # # 依次识别十个数字图片中的数字
    # num = []
    # for i in range(10):
    #     img = cv2.imread('pic_split/num' + str(i) + '.png')
    #     # 将图片转换为灰度图
    #     img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #     # 将图片转换为二值图
    #     _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    #     # 识别图片中的数字
    #     reader = easyocr.Reader(['en'], gpu=True)
    #     # 识别图片中的文字，detail=0表示只返回识别结果
    #     result = reader.readtext(img, detail=0)
    #     # 将识别结果中的,去掉
    #     result = [x.replace(',', '') for x in result]
    #     # 如果识别结果为空，将数字置为-1
    #     if len(result) == 0:
    #         num.append(-1)
    #     else:
    #         num.append(int(result[0]))


    # return num

def move_to_click(x, y, duration=0.1):
    # 鼠标缓慢移动到指定位置
    pyautogui.moveTo(x, y, duration)
    time.sleep(0.1)
    pyautogui.click()

def rand_move_to_click(x, y, rand_x, rand_y):
    x = x + random.randint(-rand_x, rand_x)
    y = y + random.randint(-rand_y, rand_y)
    move_to_click(x, y, 0.2)

def Press_Search_Button():
    center_x = int(Search_button[0] + Search_button[2] / 2)
    center_y = int(Search_button[1] + Search_button[3] / 2)
    rand_x = int(Search_button[2] / 2)
    rand_y = int(Search_button[3] / 2)
    rand_move_to_click(center_x, center_y, rand_x, rand_y)
    # Q:为什么pyautogui.moveTo()函数移动不了游戏中的鼠标？
    # A:因为游戏中的鼠标是由游戏程序控制的，pyautogui.moveTo()函数只能控制操作系统的鼠标
    # Q:呢我怎么才能控制游戏中的鼠标移动？



def Press_Buy_Button():
    print('Press_Buy_Button')
    pass

def Dark_and_Darker_buy_ring():
    while True:
        time.sleep(1)
        # 获取当前窗口名称
        window_name = pyautogui.getActiveWindow().title
        # print(window_name)
        if 'Chrome' in window_name:
            print('Dark and Darker is running...')
            while True:
                Press_Search_Button()
                time.sleep(1)
                prices = Get_Prices()
                print(prices)
                if prices != -1:
                    # 如果有价格小于100，点击购买按钮
                    if min(prices) < 100:
                        # 最小价格的位置
                        min_index = prices.index(min(prices))
                        # 点击购买按钮
                        Press_Buy_Button()
                if 'Dark and Darker' not in pyautogui.getActiveWindow().title:
                    print('Dark and Darker is not running...')
                    break


if __name__ == '__main__':
    Mymain()
    # Dark_and_Darker_buy_ring()
            
    # 我是cuda_12.3版本，我应该安装的是torch-2.1.2
    # 获取当前屏幕分辨率
    # screen_width, screen_height = pyautogui.size()
    # time.sleep(0)
    
    # print(window_name)
    # prices = Get_Prices()
    # print(prices)
    # Press_Search_Button()
    # Get_Prices()

    # # 设置要点击的位置
    # click_x = 449
    # click_y = 247
    
    # # 将鼠标移动到指定位置并点击
    # pyautogui.moveTo(click_x, click_y)
    # pyautogui.click()
