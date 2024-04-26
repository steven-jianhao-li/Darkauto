# 提供PID类，用于鼠标移动控制
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