'''
#Track 逐波踏浪0.1

#限制条件


#优化参数
pricechange = 0.002，interval_s=10

#更新内容


#更新目标
下单后急需止损
小数点？
找不到单

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
class Track01Strategy(CtaTemplate):
    """基于Tick的交易策略"""
    className = 'Track01Strategy'
    author = '南石资本'

    count = 0#记时

    # 策略参数
    pricechange = 0.002
    volumechange =0
    fixed_size = 1
    interval_s=10
    losestop=0.001
    winstop=0.01
    slip=0.001
    decimal=3

    # 策略变量
    posPrice = 0
    countinterval=0

    # 参数列表，保存了参数的名称
    parameters = ["pricechange","volumechange","fixed_size","interval_s","losestop","slip","decimal"]

    # 变量列表，保存了变量的名称
    variables = ["posPrice"]


    # ----------------------------------------------------------------------
    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """Constructor"""

        super(Track01Strategy, self).__init__(cta_engine, strategy_name, vt_symbol, setting)

        #创建Array队列
        self.bg = BarGenerator(self.on_bar)
        self.ta = TickArrayManager(size=2)
        self.am = ArrayManager(size=2)

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

        self.cancel_all()
        ta=self.ta
        self.bg.update_tick(tick)

        if self.countinterval<self.interval_s*2:
            self.countinterval+= 1
            return

        ta.updateTick(tick)

        if not ta.inited:
            return

        if self.pos == 0:
            if ta.RatePrice()>self.pricechange and ta.RateVolume()>self.volumechange:
                self.buy(round(ta.TicklastPriceArray[-1]*(1+self.slip),self.decimal), self.fixed_size, False)
                self.write_log("buy order"+str(ta.TicklastPriceArray[-1]))
            if ta.RatePrice()<-1*self.pricechange and ta.RateVolume()>self.volumechange:
                self.short(round(ta.TicklastPriceArray[-1]*(1-self.slip),self.decimal), self.fixed_size, False)
                self.write_log("sell order"+str(ta.TicklastPriceArray[-1]))

                
        self.countinterval=0

    # ----------------------------------------------------------------------
    def on_bar(self, bar: BarData):
        """收到Bar推送（必须由用户继承实现）"""

        self.cancel_all()
        am=self.am
        am.update_bar(bar)

        if not am.inited:
            return

        if self.pos > 0:
            #止损
            self.sell(self.posPrice*(1-self.losestop), self.fixed_size, True)
            #止盈
            if self.ta.TicklastPriceArray[-1]>self.posPrice and (np.log(am.close_array[-1]) - np.log(am.close_array[-2]))<0:
                self.sell(round(self.ta.TicklastPriceArray[-1]*(1-self.slip),self.decimal), self.fixed_size, False)#没成交怎么办
                self.write_log("winstop sell order"+str(self.ta.TicklastPriceArray[-1]))
        elif self.pos < 0:
            #止损
            self.cover(self.posPrice*(1+self.losestop), self.fixed_size, True)
            #止盈
            if self.ta.TicklastPriceArray[-1]<self.posPrice and (np.log(am.close_array[-1]) - np.log(am.close_array[-2]))>0:
                self.cover(round(self.ta.TicklastPriceArray[-1]*(1+self.slip),self.decimal), self.fixed_size, False)
                self.write_log("winstop buy order"+str(self.ta.TicklastPriceArray[-1]))
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
        self.posPrice = trade.price

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
    def __init__(self, size):
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
        self.countinterval=0

    def RateVolume(self):
        if self.TickaskVolume1Array[-1] - self.TickbidVolume1Array[-2]==0:
            deltavolume=0
        else: deltavolume=np.log(self.TickaskVolume1Array[-1]) - np.log(self.TickbidVolume1Array[-2])
        return (deltavolume)

    def RatePrice(self):
        return (np.log(self.TicklastPriceArray[-1]) - np.log(self.TicklastPriceArray[-2]))
