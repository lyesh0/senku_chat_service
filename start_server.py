#!/usr/bin/env python3
"""
启动Qwen微调服务

此脚本用于启动FastAPI后端服务器。
"""

import uvicorn
import os
from pathlib import Path
from dotenv import load_dotenv

def main():
    """启动服务器"""
    # 加载环境变量
    load_dotenv()

    # 确保models目录存在
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)

    # 从环境变量或配置文件获取端口
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")

    print(f"🚀 启动Qwen微调服务API服务器")
    print(f"📡 服务器地址: http://{host}:{port}")
    print(f"📚 API文档: http://{host}:{port}/docs")
    print(f"🔄 健康检查: http://{host}:{port}/health")

    # 启动服务器
    uvicorn.run(
        "server.api:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
