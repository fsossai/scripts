# region imports
from AlgorithmImports import *
# endregion

class HyperActiveBluePig(QCAlgorithm):

    def initialize(self):
        self.set_start_date(2023, 1, 1)
        self.set_cash(10000)
        
        # Add asset
        self._symbol = self.add_equity("IVE", Resolution.MINUTE).symbol
        
        # Strategy parameters
        self._target_open = -0.02  # Buy on 2% dip (from exit price)
        self._target_close = 0.03  # Sell on 3% gain (from entry price)
        self._wait_time_limit = timedelta(days=5)
        self._hold_time_limit = timedelta(days=10)
        
        # State tracking
        self._phase = "START"  # Start with immediate buy
        self._phase_start_time = self.time
        self._entry_price = None
        self._last_exit_price = None
        self._num_orders = 0
        
        # Check conditions every minute during market hours
        self.schedule.on(self.date_rules.every_day(self._symbol),
                        self.time_rules.every(timedelta(minutes=1)),
                        self._check_cycle)
        
        self.settings.seed_initial_prices = True

    def _check_cycle(self):
        """Check conditions and execute Cycle"""
        if not self.securities[self._symbol].has_data:
            return
            
        current_price = self.securities[self._symbol].price
        
        if self._phase == "START":
            self._execute_buy(current_price, "Initial Entry")
            
        elif self._phase == "HOLD":
            time_in_phase = self.time - self._phase_start_time
            self._handle_hold_phase(current_price, time_in_phase)
            
        elif self._phase == "WAIT":
            time_in_phase = self.time - self._phase_start_time
            self._handle_wait_phase(current_price, time_in_phase)
    
    def _handle_wait_phase(self, current_price: float, time_in_phase: timedelta):
        """Handle the WAIT phase - looking to BUY a dip from LAST EXIT PRICE"""
        if self._last_exit_price is None:
            # Should not happen if logic is correct, but safety net
            return

        # Target Price = Exit Price * (1 + TargetOpen)
        target_price = self._last_exit_price * (1.0 + self._target_open)
        
        # Check if dip target is met (Price <= Target)
        if current_price <= target_price:
            self._execute_buy(current_price, "Target dip reached")
        # Check if time limit is exceeded
        elif time_in_phase >= self._wait_time_limit:
            self._execute_buy(current_price, "Wait time limit reached")
    
    def _handle_hold_phase(self, current_price: float, time_in_phase: timedelta):
        """Handle the HOLD phase - looking to SELL at peak from ENTRY PRICE"""
        if self._entry_price is None:
            return
        
        # Target Price = Entry Price * (1 + TargetClose)
        target_price = self._entry_price * (1.0 + self._target_close)
        
        # Check if peak target is met (Price >= Target)
        if current_price >= target_price:
            self._execute_sell(current_price, "Target peak reached")
        # Check if time limit is exceeded
        elif time_in_phase >= self._hold_time_limit:
            self._execute_sell(current_price, "Hold time limit reached")
    
    def _execute_buy(self, price: float, reason: str):
        """Execute BUY and transition to HOLD phase"""
        self.set_holdings(self._symbol, 1.0)
        self._entry_price = price
        self._phase = "HOLD"
        self._phase_start_time = self.time
        self._num_orders += 1
        self.debug(f"BUY #{self._num_orders} at ${price:.2f} - {reason}")
    
    def _execute_sell(self, price: float, reason: str):
        """Execute SELL and transition to WAIT phase"""
        pnl_pct = ((price - self._entry_price) / self._entry_price) * 100 if self._entry_price else 0
        self.liquidate(self._symbol)
        self._last_exit_price = price
        self._phase = "WAIT"
        self._phase_start_time = self.time
        self._entry_price = None
        self._num_orders += 1
        self.debug(f"SELL #{self._num_orders} at ${price:.2f} (P&L: {pnl_pct:.2f}%) - {reason}")
