# 基金数据爬取使用指南

## 概述
本项目提供了两种方式来获取基金走势数据：
1. **自建爬虫** (`fund_crawler.py`) - 直接从天天基金网等网站爬取数据
2. **akshare库** (`fund_akshare.py`) - 使用专业的金融数据库

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 方法1: 使用自建爬虫

```bash
python fund_crawler.py
```

**特点:**
- 直接从天天基金网获取数据
- 实时估值信息
- 自定义程度高
- 可能需要处理反爬虫机制

### 方法2: 使用 akshare 库 (推荐)

```bash
python fund_akshare.py
```

**特点:**
- 数据来源稳定
- API接口规范
- 支持多种金融产品
- 维护活跃

## 数据来源对比

| 数据源 | 优点 | 缺点 | 推荐度 |
|--------|------|------|--------|
| 天天基金网 | 数据全面、更新及时 | 可能有反爬虫 | ⭐⭐⭐⭐ |
| akshare | 接口稳定、使用简单 | 依赖第三方库 | ⭐⭐⭐⭐⭐ |
| 蚂蚁基金 | 数据准确 | 需要登录认证 | ⭐⭐⭐ |
| Wind/彭博 | 数据专业 | 收费，门槛高 | ⭐⭐⭐⭐⭐ (商业用途) |

## 常用基金代码

```python
# 热门基金代码示例
popular_funds = {
    '000001': '华夏成长混合',
    '110022': '易方达消费行业股票', 
    '161725': '招商中证白酒指数',
    '320003': '诺安股票基金',
    '001594': '天弘中证500指数A',
    '110011': '易方达中小盘混合',
    '260108': '景顺长城新兴成长混合',
    '163402': '兴全趋势投资混合'
}
```

## 法律合规建议

⚠️ **重要提醒:**

1. **遵守robots.txt**: 检查目标网站的爬虫协议
2. **控制请求频率**: 避免对服务器造成压力
3. **仅限个人学习**: 商业用途请购买正式数据服务
4. **数据免责**: 爬取的数据仅供参考，投资需谨慎

## 技术要点

### 反爬虫应对
```python
# 设置请求头
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'http://fund.eastmoney.com/',
    'Accept': 'application/json, text/javascript, */*; q=0.01'
}

# 添加请求间隔
import time
time.sleep(1)  # 1秒间隔

# 使用代理 (如果需要)
proxies = {'http': 'http://proxy:port'}
```

### 数据清洗
```python
# 处理异常数据
df = df.dropna()  # 删除空值
df = df[df['net_value'] > 0]  # 删除异常净值

# 数据类型转换
df['date'] = pd.to_datetime(df['date'])
df['net_value'] = pd.to_numeric(df['net_value'], errors='coerce')
```

## 扩展功能

### 1. 批量处理
```python
fund_codes = ['000001', '110022', '161725']
for code in fund_codes:
    crawler.plot_fund_trend(code)
```

### 2. 数据存储
```python
# 存储到数据库
import sqlite3
conn = sqlite3.connect('fund_data.db')
df.to_sql('fund_history', conn, if_exists='append', index=False)
```

### 3. 实时监控
```python
# 定时任务
import schedule
schedule.every(30).minutes.do(update_fund_data)
```

## 故障排除

### 常见问题:
1. **网络超时**: 增加timeout参数，使用重试机制
2. **编码问题**: 指定正确的字符编码 (utf-8)
3. **数据格式变化**: 检查API接口是否有更新
4. **IP被封**: 使用代理池或降低请求频率

### 调试技巧:
```python
# 打印响应内容
print(response.text[:500])

# 保存原始数据
with open('debug.html', 'w', encoding='utf-8') as f:
    f.write(response.text)
```

## 联系方式

如有问题或建议，请通过以下方式联系：
- GitHub Issues
- Email: your-email@example.com

---

**免责声明**: 本工具仅供学习和研究使用，使用者应自行承担风险。投资有风险，决策需谨慎。

