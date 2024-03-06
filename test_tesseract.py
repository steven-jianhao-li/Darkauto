import pyautogui
import time
import cv2
import os
import random
import winsound


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

def ringing():
    winsound.Beep(1000, 1000)

def OCR_image(img):
    # 将图片转换为灰度图
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # 将图片转换为二值图，参数解释：https://blog.csdn.net/weixin_42272768/article/details/110746790
    _, img = cv2.threshold(img, 100, 255, cv2.THRESH_BINARY)
    # 使用tesseract识别图片中的数字
    result = pytesseract.image_to_string(img, config='--psm 6')
    return result

class IO_controller:
    def __init__(self, duration=0.1):
        self.duration = duration

    def move_to_click(self, x, y, duration=0.1):
        pyautogui.moveTo(x, y, duration)
        time.sleep(0.1)
        pyautogui.click()
    def rand_move_to_click(self, x, y, rand_x, rand_y):
        x = x + random.randint(-rand_x, rand_x)
        y = y + random.randint(-rand_y, rand_y)
        self.move_to_click(x, y, 0.1 + random.random() * 0.2)


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
        print('Press_Buy_Button:', index + 1)
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
    


class Dark_and_Darker_Appliaction:
    def __init__(self) -> None:
        self.game = Dark_Game_Operation()
    def Dark_and_Darker_buy_ring(self, min_rand_attrs, max_price_target, max_price_low):
        """
        min_rand_attrs: 最小随机属性roll值
        max_price_target: 满足最小随机属性roll值的最大预算
        max_price_low: 无需满足最小随机属性roll值的最大预算
        """
        global pause_flag
        pause_flag = False
        while True:
            if pause_flag:
                print('已暂停...输入任意键继续...')
                input()
                pause_flag = False
                
            time.sleep(1)
            # 获取当前窗口名称
            window_name = pyautogui.getActiveWindow().title
            # print(window_name)
            if 'Dark and Darker' in window_name:
                print('Dark and Darker is running...')
                while True:
                    if 'Dark and Darker' not in pyautogui.getActiveWindow().title:
                        print('Dark and Darker is not running...')
                        break
                    
                    prices = self.game.Get_Prices()
                    rand_attrs = self.game.Get_Random_Attribute()
                    print("prices:", prices)
                    print("rand_attrs:", rand_attrs)
                    if prices != -1 and rand_attrs != -1:
                        # 如果有价格小于等于max_price_low，点击购买按钮
                        if min(prices) <= max_price_low:
                            # 最小价格的位置
                            min_index = prices.index(min(prices))
                            # 点击购买按钮
                            self.game.Press_Buy_Button(min_index)
                            pause_flag = True
                            ringing()
                            time.sleep(0.3 + random.random() * 0.2)
                            self.game.press_Fill_All_Items_Button()
                            time.sleep(0.1 + random.random() * 0.3)
                            self.game.press_Complete_Trade_Button()
                            break
                        # 如果rand_attrs有大于min_rand_attrs的值
                        if max(rand_attrs) >= min_rand_attrs:
                            # 检测它的价格是否小于max_price_target
                            if prices[rand_attrs.index(max(rand_attrs))] <= max_price_target:
                                # 点击购买按钮
                                self.game.Press_Buy_Button(rand_attrs.index(max(rand_attrs)))
                                pause_flag = True
                                ringing()
                                time.sleep(0.3 + random.random() * 0.2)
                                self.game.press_Fill_All_Items_Button()
                                time.sleep(0.1 + random.random() * 0.3)
                                self.game.press_Complete_Trade_Button()
                                break
                    self.game.Press_Search_Button()
                    time.sleep(0.4 + random.random() * 0.1)
    



if __name__ == '__main__':
    dark_game = Dark_and_Darker_Appliaction()
    dark_game.Dark_and_Darker_buy_ring(2, 200, 120)
    global pause_flag
    pause_flag = False
 