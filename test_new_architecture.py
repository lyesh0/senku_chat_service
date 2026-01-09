#!/usr/bin/env python3
"""
测试新的client/server架构

此脚本用于验证重构后的代码是否正常工作。
"""

import os
import sys
from pathlib import Path

def test_imports():
    """测试关键模块是否可以正常导入"""
    print("🔍 测试模块导入...")

    try:
        # 测试后端模块
        from server.api import app as server_app
        print("✅ server.api 导入成功")

        from server.fine_tune import QwenFineTuner
        print("✅ server.fine_tune 导入成功")

        from server.storage import get_storage_backend
        print("✅ server.storage 导入成功")

        # 测试前端模块
        from client.app import app as client_app
        print("✅ client.app 导入成功")

        # 测试配置
        from config import config
        print("✅ config 导入成功")

        return True

    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_config():
    """测试配置是否正确加载"""
    print("\n🔍 测试配置加载...")

    try:
        from config import config

        # 检查关键配置
        print(f"📊 默认模型: {config.model.DEFAULT_MODEL}")
        print(f"🚀 服务器配置: {config.server.HOST}:{config.server.PORT}")
        print(f"💾 存储类型: {config.STORAGE_TYPE}")

        available_apis = config.api.get_available_apis()
        print(f"🤖 可用API: {', '.join([k for k, v in available_apis.items() if v])}")

        return True

    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        return False

def test_roles():
    """测试角色文件是否可以访问"""
    print("\n🔍 测试角色配置...")

    try:
        roles_dir = Path("roles")
        if not roles_dir.exists():
            print("❌ roles目录不存在")
            return False

        role_files = list(roles_dir.glob("*.json"))
        if not role_files:
            print("❌ 没有找到角色配置文件")
            return False

        print(f"📁 找到 {len(role_files)} 个角色文件:")
        for role_file in role_files[:3]:  # 只显示前3个
            print(f"   - {role_file.name}")

        if len(role_files) > 3:
            print(f"   ... 还有 {len(role_files) - 3} 个文件")

        return True

    except Exception as e:
        print(f"❌ 角色测试失败: {e}")
        return False

def test_directory_structure():
    """测试目录结构是否正确"""
    print("\n🔍 测试目录结构...")

    required_dirs = ["client", "server", "roles", "static"]
    required_files = [
        "client/app.py",
        "server/api.py",
        "server/fine_tune.py",
        "server/storage.py",
        "start_server.py",
        "start_client.py"
    ]

    all_good = True

    # 检查目录
    for dir_name in required_dirs:
        if os.path.isdir(dir_name):
            print(f"✅ 目录存在: {dir_name}/")
        else:
            print(f"❌ 目录缺失: {dir_name}/")
            all_good = False

    # 检查文件
    for file_path in required_files:
        if os.path.isfile(file_path):
            print(f"✅ 文件存在: {file_path}")
        else:
            print(f"❌ 文件缺失: {file_path}")
            all_good = False

    return all_good

def main():
    """运行所有测试"""
    print("🚀 开始测试新的client/server架构\n")

    tests = [
        ("目录结构", test_directory_structure),
        ("模块导入", test_imports),
        ("配置加载", test_config),
        ("角色配置", test_roles),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"{'='*50}")
        print(f"测试: {test_name}")
        print('='*50)
        result = test_func()
        results.append(result)

    print(f"\n{'='*50}")
    print("测试结果汇总")
    print('='*50)

    passed = sum(results)
    total = len(results)

    for i, (test_name, _) in enumerate(tests):
        status = "✅ 通过" if results[i] else "❌ 失败"
        print(f"{test_name}: {status}")

    print(f"\n总体结果: {passed}/{total} 个测试通过")

    if passed == total:
        print("🎉 所有测试通过！新的架构已准备就绪。")
        print("\n启动命令:")
        print("  后端: python start_server.py")
        print("  前端: python start_client.py")
        return 0
    else:
        print("⚠️  部分测试失败，请检查上述错误信息。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
