# region imports
from AlgorithmImports import *
# endregion

class MovingAverageCrossover(QCAlgorithm):

    def initialize(self):
        self.set_start_date(2025, 1, 1)
        self.set_end_date(2026, 1, 1)
        self.set_cash(10000)
        
        # Add asset
        self._symbol = self.add_equity("SPY", Resolution.MINUTE).symbol
        
        # Strategy parameters
        self._fast_period = 50
        self._slow_period = 200
        
        # Indicators
        self._fast_sma = self.SMA(self._symbol, self._fast_period, Resolution.DAILY)
        self._slow_sma = self.SMA(self._symbol, self._slow_period, Resolution.DAILY)
        
        # Warm up
        self.set_warm_up(self._slow_period)
        
        # State
        self._invested = False

    def on_data(self, data: Slice):
        if self.is_warming_up:
            return
            
        if not self._fast_sma.is_ready or not self._slow_sma.is_ready:
            return
            
        # Get current values
        fast = self._fast_sma.current.value
        slow = self._slow_sma.current.value
        
        # Plotting
        self.plot("Trade Plot", "Price", self.securities[self._symbol].price)
        self.plot("Trade Plot", "Fast SMA", fast)
        self.plot("Trade Plot", "Slow SMA", slow)
        
        # Logic
        if not self.portfolio.invested:
            # Entry: Fast > Slow (Golden Cross)
            if fast > slow:
                self.set_holdings(self._symbol, 1.0)
                # self.debug(f"BUY at {self.time} (Fast: {fast:.2f} > Slow: {slow:.2f})")
        else:
            # Exit: Fast < Slow (Death Cross)
            if fast < slow:
                self.liquidate(self._symbol)
                # self.debug(f"SELL at {self.time} (Fast: {fast:.2f} < Slow: {slow:.2f})")
