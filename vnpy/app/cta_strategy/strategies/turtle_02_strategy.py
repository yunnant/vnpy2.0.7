'''
#turtle 大浪潮头0.21

#限制条件
am_size设置最大为50，载入am数大于50需重新修改
天数load为30天数据

#优化参数
20,10,14,24
12,17,10,12
#更新内容
0.21：初始化完成后可选择立即启动，时间间隔可自选，状态推送

#更新目标
对上轨下轨设置不同参数
onstart可能没用，需检查
动态平仓
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

class Turtle02Strategy(CtaTemplate):
    """"""
    author = "南石资本"

    count = 0#记时

    entry_window = 20
    exit_window = 10
    atr_window = 14
    fixed_size = 1
    candle_interval=24
    start_immediately_once_inited=0

    entry_up = 0
    entry_down = 0
    exit_up = 0
    exit_down = 0
    atr_value = 0

    long_entry = 0
    short_entry = 0
    long_stop = 0
    short_stop = 0

    parameters = ["entry_window", "exit_window", "atr_window", "fixed_size","candle_interval","start_immediately_once_inited"]
    variables = ["entry_up", "entry_down", "exit_up", "exit_down", "atr_value"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super(Turtle02Strategy, self).__init__(
            cta_engine, strategy_name, vt_symbol, setting
        )

        self.bg = BarGenerator(self.on_bar,self.candle_interval,self.on_nhour_bar,Interval.HOUR)
        self.bg1 = BarGenerator(self.on_bar,1,self.on_1hour_bar,Interval.HOUR)

        self.am = ArrayManager(size=50)

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        self.load_bar(30)

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("策略启动")
        self.start_immediately_once_inited=2

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("策略停止")

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg.update_tick(tick)
        #self.write_log(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg.update_bar(bar)
        self.bg1.update_bar(bar)

    def on_1hour_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        if self.start_immediately_once_inited==2:
            self.count += 1
            self.write_log("目前正常运行"+str(self.count)+"小时，请关注下个小时状态更新")

    def on_nhour_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """

        self.cancel_all()

        self.am.update_bar(bar)
        #self.write_log(self.am.close_array)
        if not self.am.inited:
            return

        if self.start_immediately_once_inited==1:
            self.on_start()
            self.trading=True
            self.start_immediately_once_inited=2

        self.entry_up, self.entry_down = self.am.donchian(self.entry_window)
        self.exit_up, self.exit_down = self.am.donchian(self.exit_window)
        self.write_log("参数监控: enup "+str(self.entry_up)+" endo "+str(self.entry_down)+" exup "+str(self.exit_up)+" exdo "+str(self.exit_down))
        if not self.pos:
            self.atr_value = self.am.atr(self.atr_window)
            self.long_entry = 0
            self.short_entry = 0
            self.long_stop = 0
            self.short_stop = 0

            self.send_buy_orders(self.entry_up)

            self.send_short_orders(self.entry_down)

        elif self.pos > 0:
            self.send_buy_orders(self.long_entry)
            sell_price = max(self.long_stop, self.exit_down)
            self.sell(sell_price, abs(self.pos), True)

        elif self.pos < 0:
            self.send_short_orders(self.short_entry)

            cover_price = min(self.short_stop, self.exit_up)
            self.cover(cover_price, abs(self.pos), True)

        self.put_event()

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        if trade.direction == Direction.LONG:
            self.long_entry = trade.price
            self.long_stop = self.long_entry - 2 * self.atr_value
        else:
            self.short_entry = trade.price
            self.short_stop = self.short_entry + 2 * self.atr_value

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

    def send_buy_orders(self, price):
        """"""
        t = self.pos / self.fixed_size

        if t < 1:
            self.buy(price, self.fixed_size, True)

        if t < 2:
            self.buy(price + self.atr_value * 0.5, self.fixed_size, True)

        if t < 3:
            self.buy(price + self.atr_value, self.fixed_size, True)

        if t < 4:
            self.buy(price + self.atr_value * 1.5, self.fixed_size, True)
        self.write_log("buy order "+str(price))
    def send_short_orders(self, price):
        """"""
        t = self.pos / self.fixed_size

        if t > -1:
            self.short(price, self.fixed_size, True)

        if t > -2:
            self.short(price - self.atr_value * 0.5, self.fixed_size, True)

        if t > -3:
            self.short(price - self.atr_value, self.fixed_size, True)

        if t > -4:
            self.short(price - self.atr_value * 1.5, self.fixed_size, True)
        self.write_log("sell order "+str(price))
