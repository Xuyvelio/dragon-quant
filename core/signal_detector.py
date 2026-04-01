#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""信号检测器 - 三要素确认"""

import pandas as pd


class SignalDetector:
    """入场信号检测器"""
    
    def __init__(self, config):
        self.config = config
        self.entry_cfg = config.get('strategy', {}).get('entry', {})
        self.ma_period = self.entry_cfg.get('ma_period', 5)
        self.min_yang_body = self.entry_cfg.get('min_yang_body', 5.0)
        self.fund_flow_positive = self.entry_cfg.get('fund_flow_positive', True)
    
    def check_entry(self, kline_df, fund_flow):
        """检查入场信号 (三要素缺一不可)"""
        if kline_df is None or len(kline_df) == 0:
            return {'signal': False, 'conditions': {}}
        
        latest = kline_df.iloc[-1]
        prev = kline_df.iloc[-2] if len(kline_df) > 1 else latest
        
        above_ma5 = self._check_above_ma5(latest, prev)
        big_yang = self._check_big_yang(latest, prev)
        flow_positive = self._check_fund_flow(fund_flow)
        
        signal = above_ma5 and big_yang and flow_positive
        
        return {
            'signal': signal,
            'conditions': {
                'above_ma5': above_ma5,
                'big_yang': big_yang,
                'flow_positive': flow_positive,
                'close': latest.get('收盘', 0),
                'ma5': latest.get(f'MA{self.ma_period}', 0),
                'change_pct': latest.get('涨跌幅', 0)
            }
        }
    
    def _check_above_ma5(self, latest, prev):
        """检查是否站上 5 日线"""
        ma5_col = f'MA{self.ma_period}'
        
        today_close = latest.get('收盘', 0)
        today_ma5 = latest.get(ma5_col, 0)
        yesterday_close = prev.get('收盘', 0)
        yesterday_ma5 = prev.get(ma5_col, 0)
        
        if pd.isna(today_ma5) or pd.isna(yesterday_ma5):
            return False
        
        breakthrough = today_close > today_ma5 and yesterday_close <= yesterday_ma5
        already_above = today_close > today_ma5 and yesterday_close > yesterday_ma5
        
        return breakthrough or already_above
    
    def _check_big_yang(self, latest, prev):
        """检查是否大阳线"""
        change_pct = latest.get('涨跌幅', 0)
        if pd.isna(change_pct):
            return False
        return change_pct >= self.min_yang_body
    
    def _check_fund_flow(self, fund_flow):
        """检查资金流向"""
        if fund_flow is None:
            return False
        
        net_inflow = fund_flow.get('net_inflow', 0)
        inflow_ratio = fund_flow.get('inflow_ratio', 0)
        
        if self.fund_flow_positive:
            return net_inflow > 0 or inflow_ratio > 0
        
        return True
    
    def check_exit(self, kline_df, fund_flow_list, holding_days):
        """检查出场信号"""
        exit_cfg = self.config.get('strategy', {}).get('exit', {})
        
        if exit_cfg.get('break_ma5', True):
            latest = kline_df.iloc[-1]
            ma5_col = f'MA{self.ma_period}'
            if latest.get('收盘', 0) < latest.get(ma5_col, 0):
                return {'should_exit': True, 'reason': '跌破 5 日线'}
        
        if exit_cfg.get('consecutive_outflow', 2) > 0:
            outflow_days = sum(1 for f in fund_flow_list if f and f.get('net_inflow', 0) < 0)
            if outflow_days >= exit_cfg.get('consecutive_outflow', 2):
                return {'should_exit': True, 'reason': '连续主力流出'}
        
        time_stop = exit_cfg.get('time_stop', 5)
        if holding_days >= time_stop:
            return {'should_exit': True, 'reason': '时间止损'}
        
        return {'should_exit': False, 'reason': ''}
