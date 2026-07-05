#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动脚本 - 同时运行前端和后端
情感识别系统启动脚本
"""

import os
import sys
import subprocess
import time
import threading
import platform
from pathlib import Path

BACKEND_PORT = int(os.environ.get('FLASK_PORT', 5001))
PROJECT_ROOT = Path(__file__).resolve().parent

def print_header():
    """打印启动信息"""
    print("=" * 60)
    print("  基于脑机接口与人工智能模型的情感识别系统")
    print("=" * 60)
    print(f"  操作系统: {platform.system()} {platform.release()}")
    print(f"  Python版本: {sys.version.split()[0]}")
    print("=" * 60)
    print()

def check_python():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("[错误] 需要Python 3.8或更高版本")
        print(f"当前版本: {sys.version}")
        return False
    return True

def check_dependencies():
    """检查并安装后端依赖"""
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("[错误] backend目录不存在")
        return False
    
    os.chdir(backend_dir)
    
    # 检查是否安装了依赖
    try:
        import flask
        print("[✓] 后端依赖已安装")
    except ImportError:
        print("[提示] 正在安装后端依赖，请稍候...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print("[✓] 后端依赖安装完成")
        except subprocess.CalledProcessError as e:
            print(f"[错误] 后端依赖安装失败: {e}")
            os.chdir("..")
            return False
    
    os.chdir("..")
    return True

def check_nodejs():
    """检查Node.js是否安装"""
    # Windows上需要设置shell=True或使用npm.cmd
    is_windows = platform.system() == 'Windows'
    npm_cmd = "npm.cmd" if is_windows else "npm"
    
    try:
        # 尝试多种方式检测npm
        if is_windows:
            # Windows上尝试使用shell=True
            result = subprocess.run(
                ["npm", "--version"],
                capture_output=True,
                text=True,
                check=True,
                shell=True,
                timeout=5
            )
        else:
            result = subprocess.run(
                ["npm", "--version"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            )
        npm_version = result.stdout.strip()
        print(f"[✓] Node.js已安装 (npm {npm_version})")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        # 如果直接调用失败，尝试使用where命令查找（Windows）
        if is_windows:
            try:
                where_result = subprocess.run(
                    ["where", "npm"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if where_result.returncode == 0 and where_result.stdout.strip():
                    # 找到了npm，再次尝试获取版本
                    version_result = subprocess.run(
                        ["npm", "--version"],
                        capture_output=True,
                        text=True,
                        shell=True,
                        timeout=5
                    )
                    if version_result.returncode == 0:
                        print(f"[✓] Node.js已安装 (npm {version_result.stdout.strip()})")
                        return True
            except:
                pass
        
        print("[警告] 未找到Node.js，将仅启动后端服务")
        print("如需启动前端，请安装Node.js:")
        print("  下载地址: https://nodejs.org/")
        print("  安装后请重启命令行窗口")
        return False

def install_frontend_deps():
    """安装前端依赖"""
    if not Path("node_modules").exists():
        print("[提示] 正在安装前端依赖，请稍候...")
        try:
            is_windows = platform.system() == 'Windows'
            if is_windows:
                subprocess.run(["npm", "install"], check=True, shell=True)
            else:
                subprocess.run(["npm", "install"], check=True)
            print("[✓] 前端依赖安装完成")
        except subprocess.CalledProcessError as e:
            print(f"[错误] 前端依赖安装失败: {e}")
            return False
    else:
        print("[✓] 前端依赖已安装")
    return True

def run_backend():
    """运行后端服务"""
    backend_dir = Path("backend")
    original_dir = os.getcwd()
    
    try:
        os.chdir(backend_dir)
        print("[后端] 启动Flask服务...")
        env = os.environ.copy()
        env.setdefault('FLASK_USE_RELOADER', '0')
        subprocess.run([sys.executable, "run.py"], check=True, env=env)
    except KeyboardInterrupt:
        print("\n[后端] 服务已停止")
    except Exception as e:
        print(f"[后端] 服务启动失败: {e}")
    finally:
        os.chdir(original_dir)

def run_frontend() -> bool:
    """运行前端服务，失败时返回 False 而不抛出异常。"""
    try:
        print("[前端] 启动Vite开发服务器...")
        is_windows = platform.system() == 'Windows'
        if is_windows:
            subprocess.run(["npm", "run", "dev"], check=True, shell=True)
        else:
            subprocess.run(["npm", "run", "dev"], check=True)
        return True
    except KeyboardInterrupt:
        print("\n[前端] 服务已停止")
        raise
    except subprocess.CalledProcessError as e:
        print(f"[前端] 服务启动失败: {e}")
        if e.returncode == 228 or 'ENOSPC' in str(e):
            print("[提示] 磁盘空间不足 (ENOSPC)。可清理 workspace 下旧训练目录/压缩包，或仅使用后端 API。")
        return False
    except Exception as e:
        print(f"[前端] 服务启动失败: {e}")
        return False

def main():
    """主函数"""
    os.chdir(PROJECT_ROOT)
    print_header()
    
    # 检查Python版本
    if not check_python():
        input("按Enter键退出...")
        return
    
    # 检查必要的文件
    if not Path("backend").exists():
        print("[错误] backend目录不存在")
        input("按Enter键退出...")
        return
    
    has_frontend = Path("package.json").exists()
    if not has_frontend:
        print("[警告] package.json 不存在，将仅启动后端")
    
    # 创建必要的目录
    print("[1/4] 创建必要的目录...")
    dirs = ["backend/uploads", "backend/results", "backend/logs"]
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
        print(f"  ✓ {dir_path}")
    
    # 检查并安装后端依赖
    print("\n[2/4] 检查后端依赖...")
    if not check_dependencies():
        input("按Enter键退出...")
        return
    
    # 检查Node.js
    print("\n[3/4] 检查Node.js...")
    has_nodejs = has_frontend and check_nodejs()
    
    # 如果安装了Node.js，检查前端依赖
    if has_nodejs:
        print("\n[4/4] 检查前端依赖...")
        if not install_frontend_deps():
            input("按Enter键退出...")
            return
        
        # 启动服务
        print("\n" + "=" * 60)
        print("  服务启动中...")
        print(f"  后端API: http://localhost:{BACKEND_PORT}")
        print("  前端界面: http://localhost:5173")
        print("  按 Ctrl+C 停止服务")
        print("=" * 60)
        print()
        
        # 启动后端服务（在后台线程中；非 daemon，前端失败时后端仍可继续）
        backend_thread = threading.Thread(target=run_backend, daemon=False)
        backend_thread.start()
        
        # 等待后端启动
        print("等待后端服务启动...")
        time.sleep(3)
        
        # 启动前端服务（主线程）
        if not run_frontend():
            print("\n[提示] 前端未启动，后端仍在运行: http://localhost:{0}".format(BACKEND_PORT))
            print("[提示] 释放磁盘空间后重新运行 start.py 以启动前端。")
            try:
                backend_thread.join()
            except KeyboardInterrupt:
                print("\n[后端] 服务已停止")
            return
    else:
        # 仅启动后端
        print("\n" + "=" * 60)
        print("  仅启动后端服务...")
        print(f"  后端API: http://localhost:{BACKEND_PORT}")
        print("  按 Ctrl+C 停止服务")
        print("=" * 60)
        print()
        
        run_backend()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序已退出")
    except Exception as e:
        print(f"\n[错误] 发生未预期的错误: {e}")
        import traceback
        traceback.print_exc()
        input("按Enter键退出...")












