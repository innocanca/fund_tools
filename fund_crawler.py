#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
基金数据爬取工具
支持从多个数据源获取基金走势数据
"""

import requests
import pandas as pd
import json
import time
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False   # 用来正常显示负号

class FundCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session.headers.update(self.headers)
    
    def get_fund_basic_info(self, fund_code):
        """
        获取基金基本信息
        """
        url = f"http://fundgz.1234567.com.cn/js/{fund_code}.js"
        
        try:
            response = self.session.get(url, timeout=10)
            response.encoding = 'utf-8'
            
            # 提取JSON数据
            json_str = response.text.replace('jsonpgz(', '').replace(');', '')
            data = json.loads(json_str)
            
            return {
                'code': data.get('fundcode'),
                'name': data.get('name'),
                'net_value': float(data.get('dwjz', 0)),
                'estimate_value': float(data.get('gsz', 0)),
                'estimate_growth_rate': float(data.get('gszzl', 0)),
                'update_time': data.get('gztime')
            }
        except Exception as e:
            print(f"获取基金 {fund_code} 基本信息失败: {e}")
            return None
    
    def get_fund_history_data(self, fund_code, start_date=None, end_date=None):
        """
        获取基金历史净值数据（从天天基金网）
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        # 天天基金网历史净值接口
        url = f"http://api.fund.eastmoney.com/f10/lsjz"
        params = {
            'callback': 'jQuery',
            'fundCode': fund_code,
            'pageIndex': 1,
            'pageSize': 10000,
            'startDate': start_date,
            'endDate': end_date,
            '_': int(time.time() * 1000)
        }
        
        try:
            response = self.session.get(url, params=params, timeout=15)
            response.encoding = 'utf-8'
            
            # 提取JSON数据
            json_str = response.text
            start_idx = json_str.find('{')
            end_idx = json_str.rfind('}') + 1
            json_data = json.loads(json_str[start_idx:end_idx])
            
            if json_data.get('Data') and json_data['Data'].get('LSJZList'):
                data_list = []
                for item in json_data['Data']['LSJZList']:
                    data_list.append({
                        'date': item['FSRQ'],
                        'net_value': float(item['DWJZ']) if item['DWJZ'] else 0,
                        'cumulative_value': float(item['LJJZ']) if item['LJJZ'] else 0,
                        'growth_rate': float(item['JZZZL']) if item['JZZZL'] else 0
                    })
                
                df = pd.DataFrame(data_list)
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date').reset_index(drop=True)
                
                return df
        except Exception as e:
            print(f"获取基金 {fund_code} 历史数据失败: {e}")
            return None
    
    def plot_fund_trend(self, fund_code, days=365):
        """
        绘制基金走势图
        """
        # 获取基金信息
        fund_info = self.get_fund_basic_info(fund_code)
        if not fund_info:
            print(f"无法获取基金 {fund_code} 的基本信息")
            return
        
        # 获取历史数据
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        df = self.get_fund_history_data(fund_code, start_date)
        
        if df is None or df.empty:
            print(f"无法获取基金 {fund_code} 的历史数据")
            return
        
        # 绘制走势图
        plt.figure(figsize=(12, 8))
        
        # 净值走势
        plt.subplot(2, 1, 1)
        plt.plot(df['date'], df['net_value'], linewidth=2, color='blue', label='单位净值')
        plt.plot(df['date'], df['cumulative_value'], linewidth=2, color='red', label='累计净值')
        plt.title(f"{fund_info['name']} ({fund_code}) - 净值走势图", fontsize=14, fontweight='bold')
        plt.ylabel('净值')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # 涨跌幅走势
        plt.subplot(2, 1, 2)
        colors = ['red' if x >= 0 else 'green' for x in df['growth_rate']]
        plt.bar(df['date'], df['growth_rate'], color=colors, alpha=0.7, width=1)
        plt.title('日涨跌幅', fontsize=12)
        plt.ylabel('涨跌幅 (%)')
        plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'{fund_code}_trend.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        return df

def main():
    """
    示例用法
    """
    crawler = FundCrawler()
    
    # 常见基金代码示例
    popular_funds = [
        '000001',  # 华夏成长混合
        '110022',  # 易方达消费行业股票
        '161725',  # 招商中证白酒指数
        '320003',  # 诺安股票基金
        '001594'   # 天弘中证500指数A
    ]
    
    print("基金数据爬取工具")
    print("=" * 50)
    
    # 让用户选择基金或输入基金代码
    print("热门基金代码:")
    for i, code in enumerate(popular_funds, 1):
        info = crawler.get_fund_basic_info(code)
        if info:
            print(f"{i}. {code} - {info['name']}")
    
    print("\n请选择:")
    print("1. 输入数字选择热门基金")
    print("2. 输入基金代码")
    
    choice = input("请输入选择: ").strip()
    
    fund_code = None
    if choice.isdigit() and 1 <= int(choice) <= len(popular_funds):
        fund_code = popular_funds[int(choice) - 1]
    else:
        fund_code = choice
    
    if fund_code:
        print(f"\n正在获取基金 {fund_code} 的数据...")
        
        # 获取基本信息
        info = crawler.get_fund_basic_info(fund_code)
        if info:
            print("\n基金基本信息:")
            print(f"基金名称: {info['name']}")
            print(f"最新净值: {info['net_value']}")
            print(f"估算净值: {info['estimate_value']}")
            print(f"估算涨跌幅: {info['estimate_growth_rate']:.2f}%")
            print(f"更新时间: {info['update_time']}")
        
        # 绘制走势图
        print("\n正在生成走势图...")
        df = crawler.plot_fund_trend(fund_code, days=365)
        
        if df is not None:
            print(f"\n数据获取成功！共 {len(df)} 条记录")
            print(f"走势图已保存为: {fund_code}_trend.png")
            
            # 保存数据到CSV
            csv_filename = f"{fund_code}_data.csv"
            df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
            print(f"历史数据已保存为: {csv_filename}")

if __name__ == "__main__":
    main()

