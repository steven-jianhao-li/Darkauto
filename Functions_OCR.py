import cv2
import numpy as np
import pytesseract


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

def OCR_Raw_ScreenShot(img, only_number=False):
    """
    对pyautogui.screenshot产生的截图进行OCR识别
    :param img: pyautogui.screenshot返回的图像，也可以是numpy格式的图像
    :param only_number: 是否只识别数字，默认为False
    :return: 识别结果
    """
    # 将非numpy格式的图像转换为numpy格式
    if type(img) != np.ndarray:
        img = np.array(img)
    # 类型转换，将screenshot返回的PIL.Image.Image转换为cv2的图像格式
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    # 使用tesseract识别图片中的数字
    if only_number:
        result = OCR_image(img, only_number=True)
    else:
        result = OCR_image(img, only_number=False)
    return result