#!/usr/bin/env python3
"""
Flask应用启动脚本
"""

import os
import sys
from app import app
from config import config

def main():
    """主函数"""
    # 获取环境变量
    env = os.environ.get('FLASK_ENV', 'development')
    
    # 加载配置
    app.config.from_object(config[env])
    
    # 确保必要的目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)
    os.makedirs(app.config['LOGS_FOLDER'], exist_ok=True)
    
    # 启动应用
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5001))
    debug = app.config['DEBUG']
    
    print(f"启动Flask应用...")
    print(f"环境: {env}")
    print(f"主机: {host}")
    print(f"端口: {port}")
    print(f"调试模式: {debug}")
    print(f"上传目录: {app.config['UPLOAD_FOLDER']}")
    print(f"结果目录: {app.config['RESULTS_FOLDER']}")
    
    app.run(host=host, port=port, debug=debug, threaded=True)

if __name__ == '__main__':
    main()













