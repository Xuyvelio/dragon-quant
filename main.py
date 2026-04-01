#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dragon Quant - 龙头战法量化交易系统 主入口"""

import yaml
import os
import json

from data.akshare_fetcher import AkShareFetcher
from core.dragon_selector import DragonSelector
from core.signal_detector import SignalDetector
from core.position_manager import PositionManager
from backtest.engine import BacktestEngine
from utils.helpers import print_banner, print_config, print_report


def load_config():
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'strategy.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def main():
    """主函数"""
    print_banner()
    
    print("📁 加载配置...")
    config = load_config()
    print_config(config)
    
    print("\n🔧 初始化组件...")
    fetcher = AkShareFetcher()
    selector = DragonSelector(config)
    detector = SignalDetector(config)
    position_mgr = PositionManager(config)
    
    print("\n🚀 运行回测...")
    engine = BacktestEngine(config, fetcher, selector, detector, position_mgr)
    report = engine.run()
    
    print_report(report)
    
    os.makedirs('report', exist_ok=True)
    with open('report/backtest_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("\n💾 报告已保存至：report/backtest_report.json")
    
    return report


if __name__ == '__main__':
    main()
