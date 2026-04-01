#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AkShare 数据获取封装"""

import akshare as ak
import pandas as pd
import time


class AkShareFetcher:
    """AkShare 数据获取封装类"""
    
    def __init__(self, retry_times=3, retry_delay=1):
        self.retry_times = retry_times
        self.retry_delay = retry_delay
    
    def _retry_request(self, func, *args, **kwargs):
        for i in range(self.retry_times):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if i == self.retry_times - 1:
                    raise
                time.sleep(self.retry_delay)
    
    def get_kline(self, symbol, start_date, end_date, ma_period=5):
        """获取 K 线数据并计算均线"""
        def _fetch():
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )
            return df
        
        df = self._retry_request(_fetch)
        df[f'MA{ma_period}'] = df['收盘'].rolling(window=ma_period).mean()
        df['MA10'] = df['收盘'].rolling(window=10).mean()
        df['MA20'] = df['收盘'].rolling(window=20).mean()
        return df
    
    def get_fund_flow(self, symbol):
        """获取个股资金流向"""
        def _fetch():
            df = ak.stock_individual_fund_flow(symbol=symbol)
            return df
        
        df = self._retry_request(_fetch)
        if len(df) == 0:
            return None
        
        latest = df.iloc[0]
        return {
            'date': latest.get('日期', ''),
            'net_inflow': latest.get('净流入额', 0),
            'inflow_ratio': latest.get('净流入占比', 0),
            'main_force_inflow': latest.get('主力资金净流入', 0)
        }
    
    def get_limit_up_pool(self, date=None):
        """获取涨停板池"""
        if date is None:
            from datetime import datetime
            date = datetime.now().strftime("%Y%m%d")
        
        def _fetch():
            return ak.stock_zt_pool_em(date=date)
        
        return self._retry_request(_fetch)
    
    def get_sector_flow(self):
        """获取行业板块资金流向"""
        def _fetch():
            return ak.stock_board_industry_name_em()
        
        return self._retry_request(_fetch)
