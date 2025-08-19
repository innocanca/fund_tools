#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
基金数据爬取工具安装脚本
"""

import subprocess
import sys
import os

def install_requirements():
    """
    安装依赖包
    """
    print("正在安装依赖包...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✓ 依赖包安装成功!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 依赖包安装失败: {e}")
        return False

def check_python_version():
    """
    检查Python版本
    """
    if sys.version_info < (3, 7):
        print("✗ 需要Python 3.7或更高版本")
        return False
    else:
        print(f"✓ Python版本: {sys.version}")
        return True

def create_directories():
    """
    创建必要的目录
    """
    dirs = ['data', 'output', 'logs']
    for dir_name in dirs:
        os.makedirs(dir_name, exist_ok=True)
    print("✓ 目录结构创建完成")

def main():
    """
    主安装流程
    """
    print("=== 基金数据爬取工具 安装程序 ===\n")
    
    # 检查Python版本
    if not check_python_version():
        sys.exit(1)
    
    # 创建目录
    create_directories()
    
    # 安装依赖
    if not install_requirements():
        sys.exit(1)
    
    print("\n" + "="*50)
    print("🎉 安装完成!")
    print("\n使用方法:")
    print("1. 基础爬虫: python fund_crawler.py")
    print("2. akshare版本: python fund_akshare.py")
    print("3. 查看文档: usage_guide.md")
    print("="*50)

if __name__ == "__main__":
    main()

