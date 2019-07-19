'''
#Track 逐波踏浪0.4

#限制条件
手续费0.0003

#优化参数
0.002,0.001,0,-1,-1,0.0005
0.006/7,0.003,0,10,10
0.005，0.005，20，10，0.001
#交易记录
0.0892 0716 1347

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
from ..base import (
    EngineType)
from vnpy.trader.constant import Interval, Direction, Offset
import numpy as np
########################################################################
class Track04Strategy(CtaTemplate):
    """基于Tick的交易策略"""
    className = 'Track03Strategy'
    author = '南石资本'

    count = 0#记时

    # 策略参数
    pricechange_order = 0.002
    pricechange_stop = 0.001
    volumechange =0.00
    fixed_size = 1
    interval_order=-1
    interval_stop=-1
    losestop=0.0005
    slip=0.001
    decimal=3
    contract_value_crypto=0


    # 策略变量
    posPrice = 0
    orderable=True
    performance=[0.0,0.0]
    traded=0
    history=[0.0]

    # 参数列表，保存了参数的名称
    parameters = ["pricechange_order","pricechange_stop","volumechange","interval_order","interval_stop","losestop","fixed_size","slip","decimal","contract_value_crypto"]

    # 变量列表，保存了变量的名称
    variables = ["posPrice","orderable","performance","traded"]


    # ----------------------------------------------------------------------
    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """Constructor"""

        super(Track04Strategy, self).__init__(cta_engine, strategy_name, vt_symbol, setting)

        #创建Array队列
        self.bg1 = BarGenerator(self.on_bar,24,self.on_performance,Interval.HOUR)
        self.ta = TickArrayManager(size=2,interval=-1)
        self.ta1 = TickArrayManager(size=2,interval=self.interval_order)
        self.ta2 = TickArrayManager(size=2,interval=self.interval_stop)
        #self.am = ArrayManager(size=2)
        if self.decimal==2:
            self.decimal='%.2f'
        elif self.decimal==3:
            self.decimal='%.3f'
        elif self.decimal==4:
            self.decimal='%.4f'
        elif self.decimal==1:
            self.decimal='%.1f'

        self.cta_engine=cta_engine
        self.strategy_name=strategy_name
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
        self.orderable=True

    # ----------------------------------------------------------------------
    def on_stop(self):
        """停止策略（必须由用户继承实现）"""
        self.write_log("策略停止")

    # ----------------------------------------------------------------------
    def on_tick(self, tick: TickData):
        """收到行情TICK推送（必须由用户继承实现）"""

        self.bg1.update_tick(tick)

        self.cancel_all()

        ta=self.ta
        ta1=self.ta1
        ta2=self.ta2

        ordercount=0

        ta1.updateTick(tick)
        ta2.updateTick(tick)
        ta.updateTick(tick)

        if not ta1.inited or not ta2.inited:
            return

        #实盘判断有无活跃委托

        if self.cta_engine.engine_type==EngineType.LIVE:
            vt_orderids = self.cta_engine.strategy_orderid_map[self.strategy_name]
            ordercount=len(vt_orderids)

        if ordercount>0:
            return

        if self.pos == 0 and self.orderable==True:
            if ta1.RatePrice()>self.pricechange_order and ta1.RateVolume()>self.volumechange:
                self.buy(float(self.decimal%(ta.TicklastPriceArray[-1]*(1+self.slip))), self.fixed_size, False)
                self.write_log("buy order"+str(ta.TicklastPriceArray[-1]))
                self.orderable=False
            if ta1.RatePrice()<-1*self.pricechange_order and ta1.RateVolume()>self.volumechange:
                self.short(float(self.decimal%(ta.TicklastPriceArray[-1]*(1-self.slip))), self.fixed_size, False)
                self.write_log("short order"+str(ta.TicklastPriceArray[-1]))
                self.orderable=False
        if self.pos > 0 and self.orderable==True:
            if ta2.RatePrice()<-1*self.pricechange_stop or ta.TicklastPriceArray[-1]<self.posPrice*(1-self.losestop):
                self.sell(float(self.decimal%(ta.TicklastPriceArray[-1]*(1-self.slip))), self.pos, False)
                self.write_log("sell order"+str(ta.TicklastPriceArray[-1]))
                self.orderable=False
        if self.pos < 0 and self.orderable==True:
            if ta2.RatePrice()>self.pricechange_stop or ta.TicklastPriceArray[-1]>self.posPrice*(1+self.losestop):
                self.cover(float(self.decimal%(ta.TicklastPriceArray[-1]*(1+self.slip))), -self.pos, False)
                self.write_log("cover order"+str(ta.TicklastPriceArray[-1]))
                self.orderable=False


    # ----------------------------------------------------------------------
    def on_bar(self, bar: BarData):
        """收到Bar推送（必须由用户继承实现）"""
        self.bg1.update_bar(bar)

    # ----------------------------------------------------------------------
    def on_performance(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        #self.write_log("累计交易"+str(self.traded)+"单位，"+"累计法币毛盈利"+str(self.performance[0]))
        self.history.append(self.performance[0])
        with open(str(self.strategy_name)+".txt","w") as f:
            f.write(str(self.history))

    # ----------------------------------------------------------------------
    def on_order(self, order: OrderData):
        """收到委托变化推送（必须由用户继承实现）"""
        #判断委托是否送达
        self.orderable=True



    # ----------------------------------------------------------------------
    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """

        self.posPrice = trade.price
        a={Direction.LONG:-1,Direction.SHORT:1}
        b={Offset.OPEN:-1,Offset.CLOSE:1}
        if self.contract_value_crypto!=0:
            add=trade.volume/trade.price*a[trade.direction]*b[trade.offset]*self.contract_value_crypto
        else:
            add=trade.volume*trade.price*b[trade.offset]

        if self.pos!=0:
            self.performance[1]=add
        else:
            self.performance[0]+=(self.performance[1]+add)*trade.price#将盈利转为法币
            self.performance[1]=0

        self.traded+=trade.volume

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
    def __init__(self, size, interval):
        """Constructor"""
        self.count = 0  # 缓存计数
        self.countt=0 #tick计数
        self.size = size  # 缓存大小
        self.inited = False  # True if count>=size
        self.interval=interval
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

        if self.countt<self.interval*2:
            self.countt+= 1
            return

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
        self.countt=0

    def RateVolume(self):
        if self.TickaskVolume1Array[-1] - self.TickbidVolume1Array[-2]==0:
            deltavolume=0
        else: deltavolume=np.log(self.TickaskVolume1Array[-1]) - np.log(self.TickbidVolume1Array[-2])
        return (deltavolume)

    def RatePrice(self):
        return (np.log(self.TicklastPriceArray[-1]) - np.log(self.TicklastPriceArray[-2]))
