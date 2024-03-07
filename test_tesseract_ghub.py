from multiprocessing import Process
import multiprocessing
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

# 所有按钮的位置坐标均以2k分辨率为基准
Search_button = (2315, 357, 153, 28)
# 第一个Buy按钮的位置，其余按钮坐标从上向下y坐标依次递减87
first_Buy_buttons = (2312, 460, 153, 34)
Buy_buttons_decrease_y = 87

Fill_All_Items_button = (1147, 986, 250, 65)
Complete_Trade_button = (1151, 1101, 250, 52)

Final_Price = (1383, 877, 168, 37)
Slot_chosen = (818, 260, 225, 30)

init = {
    'pause_flag': False,
    'end_flag': False
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

def OCR_image(img):
    # 将图片转换为灰度图
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # 将图片转换为二值图，参数解释：https://blog.csdn.net/weixin_42272768/article/details/110746790
    _, img = cv2.threshold(img, 100, 255, cv2.THRESH_BINARY)
    # 使用tesseract识别图片中的数字
    result = pytesseract.image_to_string(img, config='--psm 6')
    return result

def print_tkui(strs):
    """ 打包控制台输出 """
    print(strs)

class PID:
    """PID"""
    # Q: 我想让鼠标移动的速度更加平滑，所以我使用了PID控制器，我想加快移动速度，所以参数我应该如何调整？
    # A: 你可以调整P、I、D的值，P是比例，I是积分，D是微分，P是控制鼠标移动速度的，I是控制鼠标移动的平滑度的，D是控制鼠标移动的稳定性的。
    def __init__(self, P=0.1, I=0, D=0):
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
            self.RANDOM_NUM = 0.1 # 最大时间随机数
            if not self.state:
                print('错误, 未找到GHUB或LGS驱动程序')
        except FileNotFoundError:
            print(f'错误, 找不到DLL文件')



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
        time.sleep(random.uniform(0, self.RANDOM_NUM)) # 延时时间,秒,生成随机小数0~1.0
        self.dll.mouse_up(code)

    def mouse_left_click(self):
        """ 鼠标左键点击 """
        if not self.state:
            return
        self.dll.mouse_down(1)
        time.sleep(random.uniform(0, self.RANDOM_NUM))
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
        for i in range(100):
            time.sleep(min_time) # 等待时间
            new_x, new_y = pyautogui.position() # 获取当前鼠标位置

            move_x = pid_x.pidPosition(end_x, new_x) # 经过pid计算鼠标运动量
            move_y = pid_y.pidPosition(end_y, new_y)

            # print(f'x={new_x}, y={new_y}, xd={move_x}, yd={move_y}')
            # 如果近似重合就退出循环
            if end_x - new_x < 2 and end_y - new_y < 2:
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

class IO_controller:
    def __init__(self, min_time=0.01):
        self.min_time = min_time
        self.logitech = LOGITECH()

    def move_to_click(self, x, y, min_time):
        move_flag = self.logitech.mouse_move((x, y), min_time=min_time)
        if move_flag:
            self.logitech.mouse_left_click()
        
    def rand_move_to_click(self, x, y, rand_x, rand_y):
        x += random.randint(-rand_x, rand_x)
        y += random.randint(-rand_y, rand_y)
        self.move_to_click(x, y, self.min_time)


class Dark_Game_Operation:
    def __init__(self) -> None:
        self.io = IO_controller()

    def Press_Search_Button(self):
        center_x = int(Search_button[0] + Search_button[2] / 2)
        center_y = int(Search_button[1] + Search_button[3] / 2)
        rand_x = int(Search_button[2] / 2)
        rand_y = int(Search_button[3] / 2)
        self.io.rand_move_to_click(center_x, center_y, rand_x, rand_y)

    def Press_Buy_Button(self, index):
        center_x = int(first_Buy_buttons[0] + first_Buy_buttons[2] / 2)
        center_y = int(first_Buy_buttons[1] + first_Buy_buttons[3] / 2 + Buy_buttons_decrease_y * index)
        rand_x = int(first_Buy_buttons[2] / 2)
        rand_y = int(first_Buy_buttons[3] / 2)
        self.io.rand_move_to_click(center_x, center_y, rand_x, rand_y)

    def press_Fill_All_Items_Button(self):
        center_x = int(Fill_All_Items_button[0] + Fill_All_Items_button[2] / 2)
        center_y = int(Fill_All_Items_button[1] + Fill_All_Items_button[3] / 2)
        rand_x = int(Fill_All_Items_button[2] / 2)
        rand_y = int(Fill_All_Items_button[3] / 2)
        self.io.rand_move_to_click(center_x, center_y, rand_x, rand_y)

    def press_Complete_Trade_Button(self):
        center_x = int(Complete_Trade_button[0] + Complete_Trade_button[2] / 2)
        center_y = int(Complete_Trade_button[1] + Complete_Trade_button[3] / 2)
        rand_x = int(Complete_Trade_button[2] / 2)
        rand_y = int(Complete_Trade_button[3] / 2)
        self.io.rand_move_to_click(center_x, center_y, rand_x, rand_y)

    def Get_Prices(self):
        # 截取左上坐标(1986,441)开始，宽度93，高度850的画面
        # 截取的画面保存到当前目录下的screen.png，region参数是一个元组，元组的第一个元素是截图的左上角的x坐标，第二个元素是截图的左上角的y坐标，第三个元素是截图的宽度，第四个元素是截图的高度
        pyautogui.screenshot('prices_screen.png', region=(1986, 441, 93, 850))
        # 识别图片中的数字
        img = cv2.imread('prices_screen.png')
        result = OCR_image(img)
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
        
    def Get_Random_Attribute(self):
        pyautogui.screenshot('Random_Attribute_screen.png', region=(1495, 441, 112, 850))
        img = cv2.imread('Random_Attribute_screen.png')
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
        
    def Buy_Item(self, index, target_price):
        print('Buy Item:', index + 1)
        # 点击Buy按钮
        self.Press_Buy_Button(index)
        time.sleep(0.1 + random.random() * 0.1)
        # 检测价格是否一致
        pyautogui.screenshot('final_price.png', region=(Final_Price[0], Final_Price[1], Final_Price[2], Final_Price[3]))
        img = cv2.imread('final_price.png')
        final_price = OCR_image(img)
        if str(target_price) not in final_price:
            print('final_price:', final_price, '价格不一致')
            time.sleep(2 + random.random() * 0.1)
            # 键盘按下esc键
            pyautogui.keyDown('esc')
            time.sleep(0.05 + random.random() * 0.1)
            pyautogui.keyUp('esc')
            return
        else:
            print('final_price:', final_price, '价格一致，购买中......', end='')
            # 点击Fill All Items按钮
            self.press_Fill_All_Items_Button()
            time.sleep(0.03 + random.random() * 0.07)
            # 点击Complete Trade按钮
            self.press_Complete_Trade_Button()
            time.sleep(2 + random.random() * 0.1)
            # 键盘按下esc键
            pyautogui.keyDown('esc')
            time.sleep(0.05 + random.random() * 0.1)
            pyautogui.keyUp('esc')
            print('购买完成')

            
    
class Output:
    def __init__(self) -> None:
        pass

    def Print_Random_Attribute_and_Prices(self, rand_attrs, prices):
        for i in range(71):
            print('-', end='')
        # 用表格打印，方便观察，每个数字之间用|分隔，占位符为5个字符
        print('\nPrices:    ', end='')
        for price in prices:
            print(f'|{price:5}', end='')
        print('\nRand_Attrs:', end='')
        for rand_attr in rand_attrs:
            print(f'|{rand_attr:5}', end='')
        print()
        for i in range(71):
            print('-', end='')
        print()

class Dark_and_Darker_Appliaction:
    def __init__(self, data) -> None:
        self.game = Dark_Game_Operation()
        self.output = Output()
        self.data = data
    def Dark_and_Darker_buy_ring(self, min_rand_attrs, max_price_target, max_price_low):
        """
        min_rand_attrs: 最小随机属性roll值
        max_price_target: 满足最小随机属性roll值的最大预算
        max_price_low: 无需满足最小随机属性roll值的最大预算
        """
        print('正在运行Buy Ring程序...等待Dark and Darker启动...')
        while True:
            # print('pause_flag:', pause_flag, 'end_flag:', end_flag)
            time.sleep(1)
            if data['end_flag']:
                return
            if data['pause_flag']:
                print('已暂停...按下home键继续...')
                continue


            # 获取当前窗口名称
            window_name = pyautogui.getActiveWindow().title
            # print(window_name)
            if 'Dark and Darker' in window_name:
                print('Dark and Darker is running...')
                # 检测部位是否为Ring
                pyautogui.screenshot('slot_chosen.png', region=(Slot_chosen[0], Slot_chosen[1], Slot_chosen[2], Slot_chosen[3]))
                img = cv2.imread('slot_chosen.png')
                result = OCR_image(img)
                if 'Ring' not in result:
                    # print('Slot is not Ring. Waiting for 1s...')
                    time.sleep(1)
                    continue
                else:
                    old_prices = []
                    old_rand_attrs = []
                    while True:
                        if data['end_flag']:
                            return
                        if data['pause_flag']:
                            print('已暂停...按下home键继续...')
                            break
                        if 'Dark and Darker' not in pyautogui.getActiveWindow().title:
                            print('Dark and Darker is not running...')
                            break
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
                                        self.game.Buy_Item(target_item_index, prices[target_item_index])
                                    except Exception as e:
                                        print(e)
                                    data['pause_flag'] = True
                                    break
                            # 如果有价格小于等于max_price_low，点击购买按钮
                            target_item_index = prices.index(min(prices))
                            if min(prices) <= max_price_low:
                                ringing()
                                try:
                                    self.game.Buy_Item(target_item_index, prices[target_item_index])
                                except Exception as e:
                                    print(e)
                                data['pause_flag'] = True
                                break
                        time.sleep(1 + random.random() * 0.2)
                        self.game.Press_Search_Button()
    



def Listen_KeyBoard(data):
    def KeyBoard_CallBack(key):
        if key == pynput.keyboard.Key.end:  # 结束程序 End 键
            winsound.Beep(400, 200)
            data['end_flag'] = True
            return False
        elif key == pynput.keyboard.Key.home:  # 开始程序 Home 键
            winsound.Beep(600, 200)
            data['pause_flag'] = False
            return False
        elif key == pynput.keyboard.Key.page_up:  # 暂停程序 PgUp 键
            winsound.Beep(700, 200)
            data['pause_flag'] = True
            return True
    while not data['end_flag']:
        print('正在检测键盘按键，按下Home键开始，按下End键结束，按下PgUp键暂停')
        with pynput.keyboard.Listener(on_release=KeyBoard_CallBack) as k:
            k.join()
            print('pause_flag:', data['pause_flag'], 'end_flag:', data['end_flag'])

if __name__ == '__main__':
    multiprocessing.freeze_support()
    manager = multiprocessing.Manager()
    data = manager.dict()
    data.update(init)
    queue = manager.Queue(10)

    pk = Process(target=Listen_KeyBoard, args=(data,), name='Listen_KeyBoard')
    pk.start()

    dark_game = Dark_and_Darker_Appliaction(data)
    dark_game.Dark_and_Darker_buy_ring(2, 200, 100)
    # while not end_flag:
    #     print('按下Home键开始，按下End键结束，按下PgUp键暂停...')
    #     with pynput.keyboard.Listener(on_release=KeyBoard_CallBack) as k:
    #         dark_game.Dark_and_Darker_buy_ring(2, 200, 100)
    #         k.join()
    pk.join()




 