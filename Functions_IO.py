import os
import winsound

# log_and_print可能有多个参数输入，和print(1, 2)一样
def log_and_print(log_file_path, *log_str, sep=' ', end='\n'):
    """打印和记录日志
    :param log_file_path: str, 日志文件路径
    :param log_str: str, 日志内容
    :return:
    """
    # 处理一下*log_str中可能有的end = ''参数

    log_str = sep.join([str(x) for x in log_str])
    print(log_str, end=end)
    if not os.path.exists(os.path.dirname(log_file_path)):
        os.makedirs(os.path.dirname(log_file_path))
    # 用utf-8编码打开文件，如果文件不存在则创建，如果文件存在则在文件末尾追加
    with open(log_file_path, 'a', encoding='utf-8') as f:
        f.write(log_str + end)

def ringing():
    winsound.Beep(1000, 100)
    pass