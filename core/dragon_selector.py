#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""龙头筛选器"""

import pandas as pd


class DragonSelector:
    """龙头股筛选器"""
    
    def __init__(self, config):
        self.config = config
        self.dragon_cfg = config.get('strategy', {}).get('dragon', {})
        self.min_consecutive = self.dragon_cfg.get('min_consecutive_limit', 5)
        self.min_follow = self.dragon_cfg.get('min_follow_limit', 3)
    
    def filter_dragons(self, zt_df, top_sectors=None):
        """从涨停池中筛选龙头"""
        if zt_df is None or len(zt_df) == 0:
            return []
        
        dragons = []
        
        for _, row in zt_df.iterrows():
            consecutive = int(row.get('连板数', 0))
            if consecutive < self.min_consecutive:
                continue
            
            dragon = {
                '代码': row.get('代码', ''),
                '名称': row.get('名称', ''),
                '连板数': consecutive,
                '涨停原因': row.get('涨停原因类别', ''),
                '封板时间': row.get('首次封板时间', ''),
                '评分': self._calculate_score(row, top_sectors)
            }
            
            dragons.append(dragon)
        
        dragons.sort(key=lambda x: x['评分'], reverse=True)
        return dragons
    
    def _calculate_score(self, row, top_sectors=None):
        """计算龙头评分"""
        score = 0
        
        consecutive = int(row.get('连板数', 0))
        score += consecutive * 10
        
        first_limit_time = row.get('首次封板时间', '')
        if first_limit_time and first_limit_time < '10:00':
            score += 20
        elif first_limit_time and first_limit_time < '10:30':
            score += 15
        
        if top_sectors:
            reason = str(row.get('涨停原因类别', ''))
            for sector in top_sectors:
                if sector in reason:
                    score += 30
                    break
        
        return score
