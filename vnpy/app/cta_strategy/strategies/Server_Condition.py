'''
#server_condition 服务器状态推送

#限制条件

#优化参数

#更新内容


#更新目标

'''

from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    Direction,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
)
from vnpy.trader.constant import Interval

class ServerCondition(CtaTemplate):
    """"""
    author = "南石资本"

    count = 0#记时
    interval=0#推送间隔


    parameters = ["interval"]
    variables = ["count"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super(ServerCondition, self).__init__(
            cta_engine, strategy_name, vt_symbol, setting
        )

        self.bg1 = BarGenerator(self.on_bar,self.interval,self.on_server_bar,Interval.HOUR)


    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("策略启动")

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("策略停止")

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg1.update_tick(tick)
        pass

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg1.update_bar(bar)

    def on_server_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.count += 1*self.interval
        self.write_log("该账户目前正常运行"+str(self.count)+"小时，请关注下个小时状态更新")


    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        pass

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass
