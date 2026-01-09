#!/usr/bin/env python3
"""
启动Qwen微调服务前端

此脚本用于启动Flask前端应用。
"""

import os
from dotenv import load_dotenv
from client.app import app

def main():
    """启动客户端"""
    # 加载环境变量
    load_dotenv()

    # 从环境变量获取配置
    host = os.getenv("CLIENT_HOST", "0.0.0.0")
    port = int(os.getenv("CLIENT_PORT", "5000"))
    debug = os.getenv("DEBUG", "false").lower() == "true"

    print(f"🎨 启动Qwen微调服务前端")
    print(f"🌐 前端地址: http://{host}:{port}")
    print(f"🔧 调试模式: {'开启' if debug else '关闭'}")

    # 启动Flask应用
    app.run(
        host=host,
        port=port,
        debug=debug
    )

if __name__ == "__main__":
    main()
