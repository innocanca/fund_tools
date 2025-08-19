#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
专门测试基金110022数据获取的脚本
用于诊断和解决数据获取问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fund_crawler import FundCrawler
import logging
import pandas as pd

def test_fund_110022():
    """
    专门测试基金110022的数据获取功能
    """
    print("=" * 60)
    print("基金110022数据获取测试")
    print("=" * 60)
    
    # 初始化爬虫
    crawler = FundCrawler()
    fund_code = "110022"
    
    print(f"\n1. 测试基金 {fund_code} 基本信息获取...")
    try:
        info = crawler.get_fund_basic_info(fund_code)
        if info:
            print("✓ 基本信息获取成功:")
            print(f"  基金名称: {info['name']}")
            print(f"  最新净值: {info['net_value']}")
            print(f"  估算净值: {info['estimate_value']}")
            print(f"  估算涨跌幅: {info['estimate_growth_rate']:.2f}%")
            print(f"  更新时间: {info['update_time']}")
        else:
            print("✗ 基本信息获取失败")
            return False
    except Exception as e:
        print(f"✗ 基本信息获取异常: {e}")
        return False
    
    print(f"\n2. 测试基金 {fund_code} 历史数据获取...")
    try:
        # 获取最近30天的数据进行测试
        df = crawler.get_fund_history_data(fund_code, start_date="2024-01-01", end_date="2024-12-31")
        
        if df is not None and not df.empty:
            print("✓ 历史数据获取成功:")
            print(f"  数据条数: {len(df)}")
            print(f"  数据日期范围: {df['date'].min()} 至 {df['date'].max()}")
            print(f"  数据样例:")
            print(df.head().to_string(index=False))
            
            # 保存数据
            csv_file = f"test_{fund_code}_data.csv"
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            print(f"  数据已保存至: {csv_file}")
            
            return True
        else:
            print("✗ 历史数据获取失败或返回空数据")
            return False
            
    except Exception as e:
        print(f"✗ 历史数据获取异常: {e}")
        return False

def install_akshare_if_needed():
    """
    检查并安装akshare库
    """
    try:
        import akshare as ak
        print("✓ akshare库已安装")
        return True
    except ImportError:
        print("akshare库未安装，正在尝试安装...")
        import subprocess
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "akshare", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple/"])
            print("✓ akshare库安装成功")
            return True
        except subprocess.CalledProcessError:
            print("✗ akshare库安装失败，将使用其他数据源")
            return False

def test_with_akshare():
    """
    直接测试akshare获取基金110022数据
    """
    try:
        import akshare as ak
        print("\n3. 直接测试akshare数据源...")
        
        # 使用正确的akshare API获取基金净值数据
        df = ak.fund_open_fund_info_em(symbol="110022", indicator="单位净值走势", period="成立来")
        
        if df is not None and not df.empty:
            print("✓ akshare获取数据成功:")
            print(f"  数据条数: {len(df)}")
            print(f"  数据列: {list(df.columns)}")
            print("  数据样例:")
            print(df.head())
            
            # 保存akshare数据
            csv_file = "test_110022_akshare_data.csv"
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            print(f"  akshare数据已保存至: {csv_file}")
            
            # 显示数据范围
            df['净值日期'] = pd.to_datetime(df['净值日期'])
            print(f"  数据日期范围: {df['净值日期'].min()} 至 {df['净值日期'].max()}")
            
        else:
            print("✗ akshare获取数据失败")
            
    except Exception as e:
        print(f"✗ akshare测试异常: {e}")

if __name__ == "__main__":
    # 设置日志级别
    logging.basicConfig(level=logging.INFO)
    
    # 创建必要的目录
    os.makedirs('/home/leonfyang/workspace/project/logs', exist_ok=True)
    
    print("基金110022数据获取问题诊断工具")
    print("正在进行综合测试...\n")
    
    # 1. 检查并安装akshare
    install_akshare_if_needed()
    
    # 2. 测试主要功能
    success = test_fund_110022()
    
    # 3. 测试akshare
    test_with_akshare()
    
    print("\n" + "=" * 60)
    if success:
        print("✓ 测试完成，基金110022数据获取成功！")
        print("您可以正常使用改进后的fund_crawler.py")
    else:
        print("✗ 测试发现问题，请查看上述错误信息")
        print("建议:")
        print("1. 检查网络连接")
        print("2. 尝试安装akshare: pip install akshare")
        print("3. 查看logs/fund_crawler.log获取详细错误信息")
    print("=" * 60)
