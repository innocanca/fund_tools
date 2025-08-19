#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
基金数据爬取工具（增强版）
支持从多个数据源获取基金走势数据
增加了更好的错误处理和备用数据源
"""

import requests
import pandas as pd
import json
import time
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import logging
from urllib.parse import quote

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/leonfyang/workspace/project/logs/fund_crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False   # 用来正常显示负号

# 尝试导入akshare作为备用数据源
try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
    logger.info("akshare库可用，将作为备用数据源")
except ImportError:
    AKSHARE_AVAILABLE = False
    logger.warning("akshare库不可用，请安装: pip install akshare")

class FundCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.session.headers.update(self.headers)
        # 创建logs目录
        import os
        os.makedirs('/home/leonfyang/workspace/project/logs', exist_ok=True)
    
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
        获取基金历史净值数据（支持多数据源）
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"开始获取基金 {fund_code} 从 {start_date} 到 {end_date} 的历史数据")
        
        # 数据源列表，按优先级排序
        data_sources = [
            self._get_history_from_eastmoney_new,
            self._get_history_from_eastmoney_old,
            self._get_history_from_sina,
        ]
        
        # 如果akshare可用，添加到数据源列表
        if AKSHARE_AVAILABLE:
            data_sources.insert(0, self._get_history_from_akshare)
        
        # 逐个尝试数据源
        for i, data_source in enumerate(data_sources, 1):
            try:
                logger.info(f"尝试数据源 {i}/{len(data_sources)}: {data_source.__name__}")
                df = data_source(fund_code, start_date, end_date)
                if df is not None and not df.empty:
                    logger.info(f"成功从 {data_source.__name__} 获取到 {len(df)} 条记录")
                    return df
                else:
                    logger.warning(f"数据源 {data_source.__name__} 返回空数据")
            except Exception as e:
                logger.error(f"数据源 {data_source.__name__} 获取失败: {str(e)}")
                continue
        
        logger.error(f"所有数据源都无法获取基金 {fund_code} 的历史数据")
        return None
    
    def _get_history_from_akshare(self, fund_code, start_date, end_date):
        """
        使用akshare获取基金历史数据
        """
        if not AKSHARE_AVAILABLE:
            return None
        
        try:
            # 使用正确的akshare API获取基金净值数据
            df = ak.fund_open_fund_info_em(symbol=fund_code, indicator='单位净值走势', period='成立来')
            
            if df is not None and not df.empty:
                logger.info(f"akshare获取到 {len(df)} 条原始数据，列名: {list(df.columns)}")
                
                # 转换列名为统一格式
                df = df.rename(columns={
                    '净值日期': 'date',
                    '单位净值': 'net_value', 
                    '日增长率': 'growth_rate'
                })
                
                # 数据类型转换
                df['date'] = pd.to_datetime(df['date'])
                df['net_value'] = pd.to_numeric(df['net_value'], errors='coerce')
                df['growth_rate'] = pd.to_numeric(df['growth_rate'], errors='coerce')
                
                # akshare数据没有累计净值，我们暂时设为与单位净值相同
                df['cumulative_value'] = df['net_value']
                
                # 日期筛选
                start_dt = pd.to_datetime(start_date)
                end_dt = pd.to_datetime(end_date)
                df = df[(df['date'] >= start_dt) & (df['date'] <= end_dt)]
                
                df = df.sort_values('date').reset_index(drop=True)
                logger.info(f"筛选后剩余 {len(df)} 条数据（{start_date} 至 {end_date}）")
                return df
        except Exception as e:
            logger.error(f"akshare数据源获取失败: {str(e)}")
            return None
    
    def _get_history_from_eastmoney_new(self, fund_code, start_date, end_date):
        """
        使用东方财富新接口获取历史数据
        """
        url = "http://api.fund.eastmoney.com/f10/lsjz"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': f'http://fund.eastmoney.com/{fund_code}.html',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
        }
        
        params = {
            'callback': 'jQuery18309441675404303797_' + str(int(time.time() * 1000)),
            'fundCode': fund_code,
            'pageIndex': 1,
            'pageSize': 10000,
            'startDate': start_date,
            'endDate': end_date,
            '_': int(time.time() * 1000)
        }
        
        # 添加重试机制
        for attempt in range(3):
            try:
                logger.info(f"东方财富新接口尝试第 {attempt + 1} 次")
                response = self.session.get(url, params=params, headers=headers, timeout=20)
                response.encoding = 'utf-8'
                
                logger.info(f"响应状态码: {response.status_code}")
                logger.info(f"响应内容前100字符: {response.text[:100]}")
                
                if response.status_code != 200:
                    continue
                
                # 提取JSON数据
                json_str = response.text
                start_idx = json_str.find('{')
                end_idx = json_str.rfind('}') + 1
                
                if start_idx == -1 or end_idx == 0:
                    logger.warning("响应中未找到JSON数据")
                    continue
                
                json_data = json.loads(json_str[start_idx:end_idx])
                logger.info(f"JSON解析结果: ErrCode={json_data.get('ErrCode')}, TotalCount={json_data.get('TotalCount')}")
                
                if json_data.get('ErrCode') != 0:
                    logger.warning(f"API返回错误: {json_data.get('ErrCode')} - {json_data.get('ErrMsg')}")
                    continue
                
                if json_data.get('Data') and json_data['Data'].get('LSJZList'):
                    data_list = []
                    for item in json_data['Data']['LSJZList']:
                        data_list.append({
                            'date': item['FSRQ'],
                            'net_value': float(item['DWJZ']) if item['DWJZ'] else 0,
                            'cumulative_value': float(item['LJJZ']) if item['LJJZ'] else 0,
                            'growth_rate': float(item['JZZZL']) if item['JZZZL'] else 0
                        })
                    
                    if data_list:
                        df = pd.DataFrame(data_list)
                        df['date'] = pd.to_datetime(df['date'])
                        df = df.sort_values('date').reset_index(drop=True)
                        return df
                else:
                    logger.warning("API响应中没有数据")
                    
            except Exception as e:
                logger.error(f"东方财富新接口第 {attempt + 1} 次尝试失败: {str(e)}")
                if attempt < 2:  # 如果不是最后一次尝试
                    time.sleep(2)  # 等待2秒再重试
                    
        return None
    
    def _get_history_from_eastmoney_old(self, fund_code, start_date, end_date):
        """
        使用东方财富旧接口获取历史数据
        """
        url = f"http://fund.eastmoney.com/f10/F10DataApi.aspx"
        
        params = {
            'type': 'lsjz',
            'code': fund_code,
            'page': 1,
            'per': 10000,
            'sdate': start_date,
            'edate': end_date
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': f'http://fund.eastmoney.com/{fund_code}.html'
        }
        
        try:
            response = self.session.get(url, params=params, headers=headers, timeout=15)
            response.encoding = 'utf-8'
            
            # 这里需要根据实际响应格式解析数据
            # 由于接口格式可能变化，这里先返回None
            logger.info(f"东方财富旧接口响应状态: {response.status_code}")
            logger.info(f"响应内容前100字符: {response.text[:100]}")
            
        except Exception as e:
            logger.error(f"东方财富旧接口获取失败: {str(e)}")
            
        return None
    
    def _get_history_from_sina(self, fund_code, start_date, end_date):
        """
        使用新浪财经接口获取历史数据
        """
        # 这是一个备用方案，实际实现需要根据新浪的接口格式
        logger.info("新浪财经接口暂未实现")
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
        df = crawler.plot_fund_trend(fund_code, days=30)
        
        if df is not None:
            print(f"\n数据获取成功！共 {len(df)} 条记录")
            print(f"走势图已保存为: {fund_code}_trend.png")
            
            # 保存数据到CSV
            csv_filename = f"{fund_code}_data.csv"
            df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
            print(f"历史数据已保存为: {csv_filename}")

if __name__ == "__main__":
    main()

