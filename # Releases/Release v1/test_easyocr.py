import pyautogui
import time
import cv2
import os
import random
import easyocr

Search_button = (2315, 357, 153, 28)

def Get_Prices():
    # 截取左上坐标(1986,441)开始，宽度93，高度850的画面
    # 截取的画面保存到当前目录下的screen.png，region参数是一个元组，元组的第一个元素是截图的左上角的x坐标，第二个元素是截图的左上角的y坐标，第三个元素是截图的宽度，第四个元素是截图的高度
    # pyautogui.screenshot('screen.png', region=(1986, 441, 93, 850))
    pyautogui.screenshot('screen.png', region=(1490, 441, 581, 850))
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
        if 'Dark and Darker' in window_name:
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
    Dark_and_Darker_buy_ring()
            
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
