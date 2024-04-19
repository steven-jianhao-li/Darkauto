# Readme
用管理员方式运行test_tesseract_ghub.py（目前效率最高最完善）
已编写run.bat，运行该脚本即可使程序具有管理员权限运行。但仍需手动修改脚本中的路径。
IO操作已用罗技驱动实现，极大降低被检测概率。
已设计快捷键操作：Home键可以暂停程序，PgUp键可以继续程序，End键可以退出程序。

## 功能
1. 自动买戒指（仍需手动操作）

## 环境依赖
1. Python 3
2. Tesseract-OCR —— https://github.com/UB-Mannheim/tesseract/wiki
3. 罗技驱动（以下两个均需安装，安装包已上传至本项目）：
    - LGS  —— LGS_9.02.65_x64_Logitech_2.exe（超过Github要求的100M大小，可从https://pan.baidu.com/s/1VkE2FQrNEOOkW6tCOLZ-kw?pwd=yh3s下载）
    - LGhub —— lghub_WIN7_2021.3.5164.exe

## 待实现
1. 目前的键盘操作仍由pyautogui实现。后续将改用罗技驱动实现。