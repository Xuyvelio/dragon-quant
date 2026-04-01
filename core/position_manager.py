#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""持仓管理器"""


class PositionManager:
    """持仓管理类"""
    
    def __init__(self, config):
        self.config = config
        self.pos_cfg = config.get('strategy', {}).get('position', {})
        self.max_holdings = self.pos_cfg.get('max_holdings', 3)
        self.single_limit = self.pos_cfg.get('single_position_limit', 0.33)
        self.positions = {}
    
    def can_buy(self, symbol):
        """检查是否可以买入"""
        if symbol in self.positions:
            return False
        if len(self.positions) >= self.max_holdings:
            return False
        return True
    
    def buy(self, symbol, name, price, shares, signal_info):
        """买入"""
        self.positions[symbol] = {
            'name': name,
            'buy_price': price,
            'buy_shares': shares,
            'buy_date': signal_info.get('date', ''),
            'signal_conditions': signal_info.get('conditions', {}),
            'holding_days': 0,
            'fund_flow_outflow_days': 0
        }
    
    def sell(self, symbol, price, reason):
        """卖出"""
        if symbol not in self.positions:
            return None
        
        pos = self.positions[symbol]
        profit = (price - pos['buy_price']) * pos['buy_shares']
        profit_pct = (price - pos['buy_price']) / pos['buy_price']
        
        result = {
            'symbol': symbol,
            'name': pos['name'],
            'buy_price': pos['buy_price'],
            'sell_price': price,
            'shares': pos['buy_shares'],
            'profit': profit,
            'profit_pct': profit_pct,
            'holding_days': pos['holding_days'],
            'reason': reason
        }
        
        del self.positions[symbol]
        return result
    
    def update_positions(self, current_prices):
        """更新持仓信息"""
        for symbol, pos in self.positions.items():
            pos['holding_days'] += 1
            if symbol in current_prices:
                pos['current_price'] = current_prices[symbol]
                pos['current_value'] = current_prices[symbol] * pos['buy_shares']
    
    def get_position_count(self):
        return len(self.positions)
    
    def get_positions(self):
        return self.positions.copy()
    
    def clear(self):
        self.positions = {}
