#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""工具函数"""


def print_banner():
    """打印 Banner"""
    banner = """
🐉🐉🐉🐉🐉🐉🐉🐉🐉🐉🐉🐉🐉🐉🐉
        Dragon Quant - 龙头战法量化交易系统        
🐉🐉🐉🐉🐉🐉🐉🐉🐉🐉🐉🐉🐉🐉🐉
"""
    print(banner)


def print_config(config):
    """打印配置"""
    period = config['backtest']['current_period']
    dates = config['backtest']['periods'][period]
    
    print("⚙️  当前配置:")
    print(f"   回测周期：{period} ({dates.get('desc', '自定义')})")
    print(f"   时间范围：{dates['start']} → {dates['end']}")
    print(f"   连板要求：{config['strategy']['dragon']['min_consecutive_limit']}板")
    print(f"   阳线要求：>{config['strategy']['entry']['min_yang_body']}%")
    print(f"   最大持仓：{config['strategy']['position']['max_holdings']}只")


def print_report(report):
    """打印回测报告"""
    print("\n" + "=" * 60)
    print("                      📊 回测报告                      ")
    print("=" * 60)
    
    print(f"\n📅 回测周期：{report.get('period', 'N/A')}")
    print(f"💰 初始资金：{report.get('initial_capital', 0):,.0f}")
    print(f"💵 最终市值：{report.get('final_capital', 0):,.0f}")
    
    print(f"\n📈 总收益率：{report.get('total_return', 0):.2%}")
    print(f"📉 最大回撤：{report.get('max_drawdown', 0):.2%}")
    print(f"🎯 胜率：{report.get('win_rate', 0):.2%}")
    print(f"💹 平均盈利：{report.get('avg_profit', 0):.2%}")
    
    print(f"\n📝 交易次数：{report.get('trade_count', 0)}")
    print(f"📥 盈利次数：{report.get('win_count', 0)}")
    print(f"📤 亏损次数：{report.get('loss_count', 0)}")
    
    print("\n" + "=" * 60)
