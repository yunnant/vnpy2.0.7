'''
#Track 逐波踏浪0.1

#限制条件


#优化参数


#更新内容


#更新目标


'''


from datetime import datetime, time
from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
)
import numpy as np
########################################################################
class Track01mStrategy(CtaTemplate):
    """基于Tick的交易策略"""
    className = 'Track01mStrategy'
    author = '南石资本'

    # 策略参数
    pricechange = 0.01
    volumechange =0
    # 策略变量



    # 参数列表，保存了参数的名称
    parameters = ["pricechange","volumechange"]

    # 变量列表，保存了变量的名称
    variables = []


    # ----------------------------------------------------------------------
    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """Constructor"""

        super(Track01mStrategy, self).__init__(cta_engine, strategy_name, vt_symbol, setting)

        #创建Array队列
        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()

    # ----------------------------------------------------------------------

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        #tick级别交易，不需要过往历史数据

    # ----------------------------------------------------------------------
    def on_start(self):
        """启动策略（必须由用户继承实现）"""
        self.write_log("策略启动")

    # ----------------------------------------------------------------------
    def on_stop(self):
        """停止策略（必须由用户继承实现）"""
        self.write_log("策略停止")

    # ----------------------------------------------------------------------
    def on_tick(self, tick: TickData):
        """收到行情TICK推送（必须由用户继承实现）"""
        # 平仓，撤单
        self.bg.update_tick(tick)

    # ----------------------------------------------------------------------
    def on_bar(self, bar: BarData):
        """收到Bar推送（必须由用户继承实现）"""

        am=self.am

        am.update_bar(bar)
        if not am.inited:
            return
        if self.pos == 0:
            if (np.log(am.close_array[-1]) - np.log(am.close_array[-2]))>self.pricechange and (np.log(am.volume_array[-1]) - np.log(am.volume_array[-2]))>self.volumechange:
                self.write_log("up")
            if (np.log(am.close_array[-1]) - np.log(am.close_array[-2]))<-1*self.pricechange and (np.log(am.volume_array[-1]) - np.log(am.volume_array[-2]))>self.volumechange:
                self.write_log("down")
        elif self.pos > 0:
            pass
        elif self.pos < 0:
            pass

    # ----------------------------------------------------------------------
    def on_1hour_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.write_log("目前运行正常，请关注下个小时状态更新")


    # ----------------------------------------------------------------------
    def on_order(self, order: OrderData):
        """收到委托变化推送（必须由用户继承实现）"""
        pass

    # ----------------------------------------------------------------------
    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """

    # ----------------------------------------------------------------------
    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass

class TickArrayManager(object):
    """
    Tick序列管理工具，负责：
    1. Tick时间序列的维护
    2. 常用技术指标的计算
    """

    # ----------------------------------------------------------------------
    def __init__(self, size=10):
        """Constructor"""
        self.count = 0  # 缓存计数
        self.size = size  # 缓存大小
        self.inited = False  # True if count>=size

        self.TicklastPriceArray = np.zeros(self.size)
        self.TickaskVolume1Array = np.zeros(self.size)
        self.TickbidVolume1Array = np.zeros(self.size)
        self.TickaskPrice1Array = np.zeros(self.size)
        self.TickbidPrice1Array = np.zeros(self.size)
        self.TickopenInterestArray = np.zeros(self.size)
        self.TickvolumeArray = np.zeros(self.size)

    # ----------------------------------------------------------------------
    def updateTick(self, tick):
        """更新tick Array"""
        if self.count< self.size:
            self.count+= 1
        else:
            self.inited = True

        self.TicklastPriceArray[0:self.size - 1] = self.TicklastPriceArray[1:self.size]
        self.TickaskVolume1Array[0:self.size - 1] = self.TickaskVolume1Array[1:self.size]
        self.TickbidVolume1Array[0:self.size - 1] = self.TickbidVolume1Array[1:self.size]
        self.TickaskPrice1Array[0:self.size - 1] = self.TickaskPrice1Array[1:self.size]
        self.TickbidPrice1Array[0:self.size - 1] = self.TickbidPrice1Array[1:self.size]
        self.TickopenInterestArray[0:self.size - 1] = self.TickopenInterestArray[1:self.size]
        self.TickvolumeArray[0:self.size - 1] = self.TickvolumeArray[1:self.size]

        self.TicklastPriceArray[-1] = tick.last_price
        self.TickaskVolume1Array[-1] = tick.ask_volume_1
        self.TickbidVolume1Array[-1] = tick.bid_volume_1
        self.TickaskPrice1Array[-1] = tick.ask_price_1
        self.TickbidPrice1Array[-1] = tick.bid_price_1
        self.TickvolumeArray[-1] = tick.volume

    def RateVolume(self):
        if self.TickaskVolume1Array[-1] - self.TickbidVolume1Array[-2]==0:
            deltavolume=0
        else: deltavolume=np.log(self.TickaskVolume1Array[-1]) - np.log(self.TickbidVolume1Array[-2])
        return (deltavolume)

    def RatePrice(self):
        return (np.log(self.TicklastPriceArray[-1]) - np.log(self.TicklastPriceArray[-2]))
