# 用于读取log文件夹下的日志文件，加以分析后，提供给前端页面
# 通过flask框架提供web服务

import csv
from datetime import datetime, timedelta
from io import BytesIO
import logging
import uuid
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory, url_for
import os
import json
import re
import time
import hashlib
import pyautogui
from functools import wraps

from Functions_IO import log_and_print
# from main_tesseract_ghub import LOGITECH

# 当前文件所在目录
File_Dir = os.path.dirname(os.path.abspath(__file__))
# 日志文件所在目录
Log_Dir = os.path.join(File_Dir, 'log')

# 读取日志文件
def Read_Log_File(File_Path):
    # 读取日志文件
    with open(File_Path, 'r', encoding='utf-8') as f:
        Log_Content = f.read()
    return Log_Content

# 分析日志文件
def Analyse_Buy_Conclusion(Log_Content):
    # 通过正则表达式匹配"***已购买{0}，价格：[ {1} ]***"的字符串，其中{0}为商品名称，{1}为价格。例如***已购买Surgical kit，价格：[ 120 ...
    Original_Buy_Conclusion = re.findall(r'\*\*\*已购买(.*?)，价格：\[(.*?)\]', Log_Content)
    # 将商品名称存入字典，相同商品名称的价格依次存入列表
    Buy_Conclusion = {}
    for i in Original_Buy_Conclusion:
        if i[0] not in Buy_Conclusion:
            Buy_Conclusion[i[0]] = [i[1]]
        else:
            Buy_Conclusion[i[0]].append(i[1])
    return Buy_Conclusion
# 剩余购买次数
def Analyse_Left_Buy_Times(Log_Content):
    # buy_times已减少（括号内是注释，或者是“已增加 ”，直接以任意三个汉字代替就行），当前值: 
    Original_Left_Buy_Times = re.findall(r'buy_times.*?，当前值: (.*?)\n', Log_Content)

    # 最新剩余购买次数
    if len(Original_Left_Buy_Times) == 0:
        return [-1]
    Left_Buy_Times = Original_Left_Buy_Times[-1]
    return Original_Left_Buy_Times

# 显示当前物价
def Show_Current_Price(Log_Content):
    # 识别当前物价，格式如下：识别71个'-'，然后匹配数字，直到遇到换行符和另外71个'-'。例如：
    # -----------------------------------------------------------------------
    # 230 240 248 248 249 249 249 250 250 250 
    # -----------------------------------------------------------------------
    Original_Current_Price = re.findall(r'-'*71+'\n(.*?)\n'+'-'*71, Log_Content, re.DOTALL)
    if len(Original_Current_Price) == 0:
        return [-1]
    # 检测是否有Rand_Attrs: 在当前物价中，如果有，说明返回的结果既包括物价，也包括随机属性
    if 'Rand_Attrs:' in Original_Current_Price[-1]:
        # 返回json，包括物价数组和随机属性数组
        Current_Price = Original_Current_Price[-1].split('Rand_Attrs:')[0].split('|')[1:]
        # 去除Current_Price中的空格和换行符
        Current_Price = [i.strip() for i in Current_Price]

        Rand_Attrs = Original_Current_Price[-1].split('Rand_Attrs:')[1].split('|')[1:]
        # 去除Rand_Attrs中的空格和换行符
        Rand_Attrs = [i.strip() for i in Rand_Attrs]
        # print([Current_Price, Rand_Attrs])
        return [Current_Price, Rand_Attrs]
    else:
        # 返回json，只包括物价数组
        Current_Price = Original_Current_Price[-1].split('|')[1:]
        Rand_Attrs = []
        # print([Current_Price, Rand_Attrs])
        return [Current_Price, Rand_Attrs]


def Callculate_But_Succes_Rate(Log_Content):
    # 失败情况：
    # 价格一致，购买中......物品已售出
    # 成功情况：
    # 价格一致，购买中......购买成功！
    # 通过正则表达式匹配"价格一致，购买中......物品已售出"的字符串
    Original_Buy_Fail = re.findall(r'物品已售出', Log_Content)
    # 通过正则表达式匹配"价格一致，购买中......购买成功！"的字符串
    Original_Buy_Success = re.findall(r'购买成功', Log_Content)
    if len(Original_Buy_Success) + len(Original_Buy_Fail) == 0:
        return [0, 0]
    return [len(Original_Buy_Success), len(Original_Buy_Fail)]



class user_certification:
    def __init__(self):
        self.TOKENS_FILE = 'tokens.csv'
        self.TOKEN_NoActionTTL = timedelta(minutes=5)
        self.TOKEN_MaxTTL = timedelta(hours=12)
        # 如果文件不存在，则创建文件
        if not os.path.exists(self.TOKENS_FILE):
            with open(self.TOKENS_FILE, mode='w', newline='') as file:
                pass
        # 删除过期的token
        self.delete_expired_tokens()



    def generate_token(self):
        token = str(uuid.uuid4())
        creation_time = datetime.now().isoformat()
        return token, creation_time
    

    def delete_expired_tokens(self):
        temp_rows = []
        with open(self.TOKENS_FILE, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                creation_time = datetime.fromisoformat(row['creation_time'])
                if datetime.now() < datetime.fromisoformat(row['expiry']) and \
                        datetime.now() < creation_time + self.TOKEN_MaxTTL:
                    temp_rows.append(row)
        with open(self.TOKENS_FILE, mode='w', newline='') as file:
            fieldnames = ['token', 'expiry', 'creation_time']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(temp_rows)
    
    def validate_token(self, token):
        with open(self.TOKENS_FILE, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['token'] == token:
                    if datetime.now() < datetime.fromisoformat(row['expiry']) and \
                        datetime.now() < datetime.fromisoformat(row['creation_time']) + self.TOKEN_MaxTTL:
                        return True
                    else:
                        # 删除过期的token
                        self.delete_expired_tokens()
                        return False
        return False
    
    def update_token_expiry(self, token):
        temp_rows = []
        with open(self.TOKENS_FILE, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['token'] == token:
                    row['expiry'] = (datetime.now() + self.TOKEN_NoActionTTL).isoformat()
                temp_rows.append(row)
        with open(self.TOKENS_FILE, mode='w', newline='') as file:
            fieldnames = ['token', 'expiry', 'creation_time']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(temp_rows)

class Mouse_Control:
    def __init__(self):
        pass



    def move_mouse(self, x, y):
        pyautogui.moveTo(x, y)
    
    def click_mouse(self, opcode):
        if opcode == 1:
            pyautogui.click(button='left')
        elif opcode == 2:
            pyautogui.click(button='right')
        elif opcode == 3:
            pyautogui.click(button='middle')

def Open_Web_Service(Data_input):
    app = Flask(__name__, static_folder='HTML')
    # url_for('static', filename='script.js')
    # 获取 Werkzeug 的日志记录器并设置其级别为错误
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.ERROR)
    print('Web Service is running...')
    target_log = Data_input['LogFilePath']
    uc = user_certification()
    mouse_control = Mouse_Control()

    def token_required(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = request.headers.get('Authorization')
            if not token:
                return jsonify({'error': 'Missing token'}), 401
            if not uc.validate_token(token):
                return jsonify({'error': 'Invalid token'}), 401
            uc.delete_expired_tokens()
            uc.update_token_expiry(token)
            return f(*args, **kwargs)
        return wrapper

    @app.route('/buy_history', methods=['GET'])
    def log():
        # 读取日志文件
        Log_Content = Read_Log_File(target_log)
        # 分析日志文件
        Buy_Conclusion = Analyse_Buy_Conclusion(Log_Content)
        return jsonify(Buy_Conclusion)
    
    @app.route('/left_buy_times', methods=['GET'])
    def left_buy_times():
        # 读取日志文件
        Log_Content = Read_Log_File(target_log)
        # 分析日志文件
        Left_Buy_Times = Analyse_Left_Buy_Times(Log_Content)
        return jsonify(Left_Buy_Times)
    
    @app.route('/current_price', methods=['GET'])
    def current_price():
        # 读取日志文件
        Log_Content = Read_Log_File(target_log)
        # 分析日志文件
        Current_Price = Show_Current_Price(Log_Content)
        return jsonify(Current_Price)

    @app.route('/buy_success_rate', methods=['GET'])
    def buy_success_rate():
        # 读取日志文件
        Log_Content = Read_Log_File(target_log)
        # 分析日志文件
        Buy_Success_Rate = Callculate_But_Succes_Rate(Log_Content)
        return jsonify(Buy_Success_Rate)

    @app.route('/log', methods=['GET'])
    def log_file():
        # 读取日志文件
        Log_Content = Read_Log_File(target_log)
        # 把\n替换为<br>，以便在html页面中显示
        Log_Content = Log_Content.replace('\n', '<br>')
        return Log_Content
    
    @app.route('/add_buy_times', methods=['GET'])
    def add_buy_times():
        # 直接对Data_input['buy_times']进行加1操作
        Data_input['buy_times'] += 1
        log_and_print(Data_input['LogFilePath'], 'buy_times已增加，当前值:', Data_input['buy_times'])
        return jsonify(Data_input['buy_times'])
    
    @app.route('/get_screen_shot', methods=['GET'])
    def get_screen_shot():
        # 获取当前屏幕截图
        img = pyautogui.screenshot()
        # 转换为可发送的格式
        img_io = BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        return send_file(img_io, mimetype='image/png')
    
    @app.route('/move_mouse', methods=['POST'])
    @token_required
    def move_mouse():
        # 获取前端传来的json数据
        data = request.get_data()
        data = json.loads(data)
        # 移动鼠标
        mouse_control.move_mouse(data['x'], data['y'])
        return jsonify({'message': 'Mouse moved successfully'}), 200

    @app.route('/click_mouse', methods=['POST'])
    @token_required
    def click_mouse():
        # 获取前端传来的json数据
        data = request.get_data()
        data = json.loads(data)
        # opcode为1表示左键单击，为2表示右键单击，为3表示中键单击
        if data['opcode'] == 1:
            mouse_control.click_mouse(1)
        elif data['opcode'] == 2:
            mouse_control.click_mouse(2)
        elif data['opcode'] == 3:
            mouse_control.click_mouse(3)
        return jsonify({'message': 'Mouse clicked successfully'}), 200


    @app.route('/')
    def index():
        return send_from_directory(File_Dir + '/HTML', 'Index.html')
    
    @app.route('/usercontrol')
    def usercontrol():
        UserControl_Css_url = url_for('static', filename='CSS/UserControl.css')
        return send_from_directory(File_Dir + '/HTML', 'UserControl.html')
    
    @app.route('/login')
    def login():
        login_Css_url = url_for('static', filename='CSS/Login.css')
        return send_from_directory(File_Dir + '/HTML', 'Login.html')

    @app.route('/loginrequest', methods=['POST'])
    def loginrequest():
        # 获取前端传来的json数据
        data = request.get_json()
        data_hashed_password = data['hashed_password']

        # 读取明文密码文件Secret
        with open('Secret', 'r') as f:
            Secret = f.read()
        

        hashed_password = []
        # 对明文密码和当前时间（精确到分钟）进行hash
        m = hashlib.sha256()
        # m.update(Secret.encode('utf-8'))
        # m.update(str(int(time.time() / 60)).encode('utf-8'))
        # print(Secret + str(int(time.time() / 60)))
        m.update(str(Secret + str(int(time.time() / 60))).encode('utf-8'))
        hashed_password.append(m.hexdigest())

        # 对明文密码和当前时间的上一分钟进行hash
        m = hashlib.sha256()
        # m.update(Secret.encode('utf-8'))
        # m.update(str(int(time.time() / 60) - 1).encode('utf-8'))
        m.update(str(Secret + str(int(time.time() / 60) - 1)).encode('utf-8'))
        hashed_password.append(m.hexdigest())

        # 验证密码
        if data_hashed_password in hashed_password:
            # 生成token
            token, creation_time = uc.generate_token()
            expiry = (datetime.now() + uc.TOKEN_NoActionTTL).isoformat()
            print('New generated token:', token, '\nExpiry time:', expiry)
            with open(uc.TOKENS_FILE, mode='a', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=['token', 'expiry', 'creation_time'])
                if os.stat(uc.TOKENS_FILE).st_size == 0:
                        writer.writeheader()
                writer.writerow({'token': token, 'expiry': expiry, 'creation_time': creation_time})
            return jsonify({'token': token}), 200
        return jsonify({'message': 'Invalid credentials'}), 401
    
    @app.route('/verifytoken', methods=['POST'])
    def verifytoken():
        # 获取前端传来的json数据
        data = request.get_json()
        token = data['token']
        # 删除过期的token
        uc.delete_expired_tokens()
        if uc.validate_token(token):
            return jsonify({'valid': 'Token is valid'}), 200
        return jsonify({'error': 'Invalid token'}), 401


    # logitech = LOGITECH()
    # 启动web服务，默认端口为5000，可通过host参数指定ip地址
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == '__main__':
    Data_input = {
        "LogFilePath": r'log\2024_03_12 19_05_16.txt'
    }
    Open_Web_Service(Data_input)