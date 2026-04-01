#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
backtest_fair_v3.py - 龙头战法公平回测（最终版）
核心逻辑：
  1. 双模式买入：尾盘确认 + 打板模式
  2. 动态 MA5 止损（不是固定百分比）
  3. 龙头需要板块效应（排除独立炒作）
  4. 排除 ST 股
运行：python backtest/backtest_fair_v3.py
"""

import akshare as ak
import pandas as pd
import numpy as np
import yaml
from datetime import datetime, timedelta
from tqdm import tqdm
import json
import os
import time

# ==================== 配置加载 ====================
with open('config/strategy.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

PERIOD = config['backtest']['current_period']
DATES = config['backtest']['periods'][PERIOD]
START_DATE = DATES['start']
END_DATE = DATES['end']
INITIAL_CAPITAL = 1000000
MAX_HOLDINGS = config['strategy']['position']['max_holdings']
MA_PERIOD = config['strategy']['entry']['ma_period']
MIN_YANG_BODY = config['strategy']['entry']['min_yang_body']
MIN_CONSECUTIVE_LIMIT = config['strategy']['dragon']['min_consecutive_limit']
MIN_FOLLOW_LIMIT = config['strategy']['dragon'].get('min_follow_limit', 3)
OBSERVATION_WINDOW = config['strategy']['entry'].get('observation_window', 90)
LIMIT_UP_THRESHOLD = 9.5

print("=" * 70)
print("🐉 龙头战法公平回测 v3 - 双模式买入 + 动态 MA5 止损")
print("=" * 70)
print(f"📅 回测周期：{START_DATE} → {END_DATE}")
print(f"💰 初始资金：{INITIAL_CAPITAL/10000:.2f}万")
print(f"📦 最大持仓：{MAX_HOLDINGS}只")
print(f"📈 连板要求：≥{MIN_CONSECUTIVE_LIMIT}连板")
print(f"👥 跟风要求：≥{MIN_FOLLOW_LIMIT}只跟风涨停")
print(f"📉 止损条件：收盘价<当日 MA5（动态）")
print("-" * 70)
print("📥 买入模式：")
print("   模式一：尾盘确认（收盘>MA5 + 大阳线 + 主力流入）")
print("   模式二：打板模式（突破 5 日线后直接涨停，任何时间）")
print("=" * 70)

SECTOR_STOCKS = {
    '商业航天': ['000738', '000768', '600118', '600879', '002151'],
    '人工智能': ['002230', '000977', '603019', '002371', '600570'],
    '机器人': ['002747', '300024', '000528', '603666', '300607'],
    '半导体': ['002371', '603986', '002156', '600584', '300782'],
    '算力': ['000977', '002335', '603019', '002230', '300271'],
    '无人驾驶': ['002920', '002594', '002230', '603596', '002405'],
}

def get_sector_from_stock(symbol):
    for sector, stocks in SECTOR_STOCKS.items():
        if symbol in stocks:
            return sector
    return None

def get_sector_limit_up_count(date, sector):
    try:
        zt_df = ak.stock_zt_pool_em(date=date)
        if len(zt_df) == 0:
            return 0
        return len(zt_df[zt_df['代码'].isin(SECTOR_STOCKS.get(sector, []))])
    except:
        return 0

def get_all_stocks():
    print("\n📦 获取 A 股股票列表...")
    try:
        df = ak.stock_info_a_code_name()
        df = df[~df['名称'].str.contains('ST', na=False)]
        print(f"✅ 股票总数：{len(df)}（已排除 ST 股）")
        return df
    except Exception as e:
        print(f"❌ 获取股票列表失败：{e}")
        return pd.DataFrame()

def get_kline_data(symbol, start_date, end_date):
    try:
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
        if len(df) > 0:
            df['MA5'] = df['收盘'].rolling(window=5).mean()
            df['YangBody'] = (df['收盘'] - df['开盘']) / df['开盘'] * 100
            df['PctChange'] = df['涨跌幅']
            df['IsLimitUp'] = df['PctChange'] >= LIMIT_UP_THRESHOLD
        return df
    except:
        return pd.DataFrame()

def get_fund_flow(symbol):
    try:
        df = ak.stock_individual_fund_flow(symbol=symbol)
        return df.iloc[0] if len(df) > 0 else None
    except:
        return None

def get_fund_flow_history(symbol, days=10):
    try:
        df = ak.stock_individual_fund_flow(symbol=symbol)
        return df.head(days).to_dict('records') if len(df) >= days else []
    except:
        return []

def detect_consecutive_limit(kline, min_limit=5):
    positions = []
    if len(kline) < min_limit:
        return positions
    i = min_limit - 1
    while i < len(kline):
        count = sum(1 for j in range(min_limit) if i-j >= 0 and kline.iloc[i-j]['PctChange'] > 9.5)
        if count >= min_limit:
            positions.append(i)
            i += min_limit
        else:
            i += 1
    return positions

def check_sector_effect(symbol, limit_end_date, min_follow=3):
    sector = get_sector_from_stock(symbol)
    if sector is None:
        return False
    return get_sector_limit_up_count(limit_end_date.replace('-', ''), sector) >= min_follow

def detect_pullback_entry(kline, limit_end_pos, observation_window=90):
    signals = []
    for pos in limit_end_pos:
        post = kline.iloc[pos+1:].reset_index(drop=True)
        if len(post) < 5 or len(post) > observation_window:
            continue
        break_point = next((i for i in range(len(post)) if post.iloc[i]['收盘'] < post.iloc[i]['MA5']), -1)
        if break_point == -1:
            continue
        for i in range(break_point + 1, min(break_point + 30, len(post))):
            cur = post.iloc[i]
            tail = cur['收盘'] > cur['MA5'] and cur['YangBody'] > MIN_YANG_BODY and cur['收盘'] > cur['开盘']
            limit = cur['IsLimitUp'] and cur['收盘'] > cur['MA5']
            if tail or limit:
                signals.append({
                    'limit_end_date': kline.iloc[pos]['日期'],
                    'entry_date': cur['日期'],
                    'entry_price': cur['收盘'],
                    'entry_index': pos + 1 + i,
                    'yang_body': cur['YangBody'],
                    'ma5_at_entry': cur['MA5'],
                    'entry_mode': 'limit_up' if limit else 'tail',
                    'is_limit_up': cur['IsLimitUp'],
                    'pct_change': cur['PctChange']
                })
                break
    return signals

def check_exit_signal(kline, entry_pos, current_pos, flow_history):
    if current_pos >= len(kline):
        return True, 'timeout'
    cur = kline.iloc[current_pos]
    if cur['收盘'] < cur['MA5']:
        return True, 'break_ma5'
    if len(flow_history) >= 2 and flow_history[0].get('净流入额', 0) < 0 and flow_history[1].get('净流入额', 0) < 0:
        return True, 'consecutive_outflow'
    if current_pos - entry_pos > 10:
        return True, 'time_stop'
    return False, None

class FairBacktestEngine:
    def __init__(self, capital, max_hold):
        self.capital = capital
        self.max_holdings = max_hold
        self.positions = {}
        self.trades = []
    
    def buy(self, symbol, price, shares, date, info):
        if len(self.positions) >= self.max_holdings:
            return False
        cost = price * shares
        if cost <= self.capital:
            self.capital -= cost
            self.positions[symbol] = {'shares': shares, 'cost': price, 'entry_date': date, 'entry_ma5': info.get('ma5_at_entry', price), 'entry_mode': info.get('entry_mode', 'unknown')}
            self.trades.append({'type': 'BUY', 'symbol': symbol, 'price': price, 'shares': shares, 'date': date, 'entry_mode': info.get('entry_mode', 'unknown')})
            return True
        return False
    
    def sell(self, symbol, price, date, reason, ma5):
        if symbol in self.positions:
            pos = self.positions[symbol]
            self.capital += price * pos['shares']
            self.trades.append({'type': 'SELL', 'symbol': symbol, 'price': price, 'profit': (price - pos['cost']) / pos['cost'], 'date': date, 'exit_reason': reason, 'entry_mode': pos['entry_mode']})
            del self.positions[symbol]
            return True
        return False

def run_backtest():
    stocks = get_all_stocks()
    if len(stocks) == 0:
        return None
    engine = FairBacktestEngine(INITIAL_CAPITAL, MAX_HOLDINGS)
    total_signals = valid_signals = tail_count = limit_count = 0
    
    print(f"\n🚀 开始回测...")
    test_count = min(200, len(stocks))
    
    for idx, row in tqdm(stocks.head(test_count).iterrows(), total=test_count, desc="回测中"):
        symbol, name = row['代码'], row['名称']
        if 'ST' in name:
            continue
        kline = get_kline_data(symbol, START_DATE, END_DATE)
        if len(kline) < 30:
            continue
        limits = detect_consecutive_limit(kline, MIN_CONSECUTIVE_LIMIT)
        if not limits:
            continue
        signals = detect_pullback_entry(kline, limits, OBSERVATION_WINDOW)
        if not signals:
            continue
        for sig in signals:
            total_signals += 1
            if not check_sector_effect(symbol, sig['limit_end_date'], MIN_FOLLOW_LIMIT):
                continue
            valid_signals += 1
            limit_count += 1 if sig['entry_mode'] == 'limit_up' else 0
            tail_count += 1 if sig['entry_mode'] == 'tail' else 0
            if sig['entry_mode'] == 'tail':
                flow = get_fund_flow(symbol)
                if not flow or flow.get('净流入额', 0) <= 0:
                    continue
            shares = int((engine.capital / MAX_HOLDINGS) / sig['entry_price'] / 100) * 100
            if shares < 100:
                continue
            if engine.buy(symbol, sig['entry_price'], shares, sig['entry_date'], sig):
                flow_hist = get_fund_flow_history(symbol)
                for sell_idx in range(sig['entry_index'] + 1, min(sig['entry_index'] + 30, len(kline))):
                    exit_sig, reason = check_exit_signal(kline, sig['entry_index'], sell_idx, flow_hist)
                    if exit_sig:
                        engine.sell(symbol, kline.iloc[sell_idx]['收盘'], kline.iloc[sell_idx]['日期'], reason, kline.iloc[sell_idx]['MA5'])
                        break
                if symbol in engine.positions:
                    last = min(sig['entry_index'] + 30, len(kline) - 1)
                    engine.sell(symbol, kline.iloc[last]['收盘'], kline.iloc[last]['日期'], 'timeout', kline.iloc[last]['MA5'])
        if idx % 10 == 0:
            time.sleep(0.5)
    
    sells = [t for t in engine.trades if t['type'] == 'SELL']
    wins = len([t for t in sells if t.get('profit', 0) > 0])
    losses = len(sells) - wins
    total_profit = sum(t.get('profit', 0) for t in sells)
    
    print("\n" + "=" * 70)
    print("📊 回测报告")
    print("=" * 70)
    print(f"💵 最终市值：{engine.capital/10000:.2f}万")
    print(f"📈 总收益率：{(engine.capital - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100:.2f}%")
    print(f"📝 交易次数：{len(sells)}")
    print(f"🎯 胜率：{wins/len(sells)*100:.2f}%" if sells else "🎯 胜率：N/A")
    print(f"📥 尾盘确认：{tail_count} 次")
    print(f"📥 打板模式：{limit_count} 次")
    print("=" * 70)
    
    os.makedirs('report', exist_ok=True)
    with open('report/fair_backtest_report_v3.json', 'w', encoding='utf-8') as f:
        json.dump({'total_return': (engine.capital - INITIAL_CAPITAL) / INITIAL_CAPITAL, 'trades': engine.trades}, f, indent=2)
    print("\n✅ 报告已保存至：report/fair_backtest_report_v3.json")
    return engine.capital

if __name__ == '__main__':
    try:
        run_backtest()
        print("\n🎉 回测完成！")
    except KeyboardInterrupt:
        print("\n⚠️  用户中断")
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()