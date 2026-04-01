#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试 AkShare 数据连接"""

import akshare as ak

print("=" * 60)
print("🔌 测试 AkShare 数据连接")
print("=" * 60)

print(f"\n📦 AkShare 版本：{ak.__version__}")

print("\n📈 测试获取 K 线数据...")
try:
    df = ak.stock_zh_a_hist(symbol="000592", period="daily", start_date="20250801", end_date="20250901", adjust="qfq")
    print(f"✅ K 线数据获取成功！{len(df)} 条记录")
    print(df[['日期', '收盘', '成交量']].head())
except Exception as e:
    print(f"❌ K 线数据获取失败：{e}")

print("\n💰 测试获取资金流向...")
try:
    flow_df = ak.stock_individual_fund_flow(symbol="000592")
    print(f"✅ 资金流向获取成功！")
    print(flow_df.iloc[0])
except Exception as e:
    print(f"❌ 资金流向获取失败：{e}")

print("\n🔥 测试获取涨停池...")
try:
    zt_df = ak.stock_zt_pool_em(date="20250120")
    print(f"✅ 涨停池获取成功！{len(zt_df)} 只股票")
    if len(zt_df) > 0:
        print(zt_df[['代码', '名称', '连板数']].head())
except Exception as e:
    print(f"❌ 涨停池获取失败：{e}")

print("\n📊 测试获取板块资金流向...")
try:
    sector_df = ak.stock_board_industry_name_em()
    print(f"✅ 板块资金流向获取成功！{len(sector_df)} 个板块")
    print(sector_df[['板块名称', '净流入额', '涨跌幅']].head(10))
except Exception as e:
    print(f"❌ 板块资金流向获取失败：{e}")

print("\n" + "=" * 60)
print("✅ 连接测试完成！")
print("=" * 60)
