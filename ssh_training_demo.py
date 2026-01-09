#!/usr/bin/env python3
"""
SSH自动化训练演示脚本

此脚本演示如何使用SSH管理器进行自动化文件上传和训练任务执行。
"""

import os
import sys
from pathlib import Path

# 加载环境变量配置
from config import config

def main():
    """演示SSH自动化训练流程"""
    print("🔧 SSH自动化训练演示")
    print("=" * 50)

    # 检查环境配置
    print("\n📋 检查SSH配置...")

    ssh_hostname = os.getenv("SSH_HOSTNAME")
    ssh_key_file = os.getenv("SSH_KEY_FILENAME")

    if not ssh_hostname:
        print("❌ SSH_HOSTNAME 未配置")
        print("请在 .env 文件中设置 SSH_HOSTNAME=your-autodl-server.com")
        return 1

    if not ssh_key_file:
        print("❌ SSH_KEY_FILENAME 未配置")
        print("请在 .env 文件中设置 SSH_KEY_FILENAME=~/.ssh/id_rsa_autodl")
        return 1

    print(f"✅ SSH主机: {ssh_hostname}")
    print(f"✅ SSH密钥: {ssh_key_file}")

    # 导入SSH管理器
    try:
        from server.ssh_manager import get_ssh_manager, TrainingConfig
        print("✅ SSH管理器导入成功")
    except ImportError as e:
        print(f"❌ 导入SSH管理器失败: {e}")
        print("请确保在senku环境下运行: conda activate senku")
        return 1

    # 创建SSH管理器
    print("\n🔗 创建SSH连接...")
    ssh_manager = get_ssh_manager()
    if not ssh_manager:
        print("❌ 创建SSH管理器失败")
        return 1

    try:
        # 测试连接
        print("🔍 测试SSH连接...")
        if not ssh_manager.connect():
            print("❌ SSH连接失败")
            print("请检查：")
            print("1. SSH密钥文件是否存在")
            print("2. SSH密钥是否有正确权限 (chmod 600)")
            print("3. Autodl服务器是否可访问")
            print("4. SSH配置是否正确")
            print("5. 是否配置了正确的SSH端口")
            return 1

        print("✅ SSH连接成功！")

        # 设置远程环境
        print("\n⚙️ 设置远程环境...")
        try:
            ssh_manager.setup_environment()
            print("✅ 远程环境设置完成")
        except Exception as e:
            print(f"⚠️ 远程环境设置警告: {e}")

        # 模拟训练配置
        print("\n🎯 模拟训练任务...")

        # 检查角色文件
        roles_dir = Path("roles")
        if not roles_dir.exists():
            print("❌ roles目录不存在")
            return 1

        role_files = list(roles_dir.glob("*.json"))
        if not role_files:
            print("❌ 没有找到角色配置文件")
            return 1

        # 使用第一个角色文件作为示例
        example_role = role_files[0]
        print(f"📄 使用示例角色: {example_role.name}")

        # 创建训练配置
        training_config = TrainingConfig(
            model_id="demo_training_001",
            role_file=str(example_role),
            batch_size=4,  # 小批量用于演示
            epochs=1,      # 只训练1个epoch用于演示
            learning_rate=2e-5,
            use_lora=True
        )

        print("📋 训练配置:")
        print(f"   模型ID: {training_config.model_id}")
        print(f"   角色文件: {example_role.name}")
        print(f"   批次大小: {training_config.batch_size}")
        print(f"   训练轮数: {training_config.epochs}")
        print(f"   使用LoRA: {training_config.use_lora}")

        # 询问用户是否要继续
        print("\n⚠️ 警告：这将启动真实的远程训练任务")
        response = input("是否继续？(y/N): ").strip().lower()

        if response != 'y':
            print("演示取消")
            return 0

        # 开始训练
        print("\n🚀 启动远程训练...")
        try:
            job_id = ssh_manager.start_training(training_config)
            print(f"✅ 训练任务已启动，任务ID: {job_id}")

            # 监控训练状态
            print("\n👀 监控训练状态...")
            import time

            for i in range(10):  # 监控10次，每次间隔30秒
                status = ssh_manager.check_training_status(job_id)
                print(f"状态检查 {i+1}/10: {status['status']}")

                if status['status'] in ['completed', 'failed']:
                    break

                time.sleep(30)  # 等待30秒

            final_status = ssh_manager.check_training_status(job_id)
            print(f"\n🏁 最终状态: {final_status['status']}")

            if final_status['status'] == 'completed':
                print("🎉 训练成功完成！")

                # 下载模型（如果需要）
                download = input("是否下载训练好的模型？(y/N): ").strip().lower()
                if download == 'y':
                    print("📥 下载模型...")
                    success = ssh_manager.download_trained_model(job_id, "models")
                    if success:
                        print("✅ 模型下载成功")
                    else:
                        print("❌ 模型下载失败")

            elif final_status['status'] == 'failed':
                print("❌ 训练失败")
                if 'error_log' in final_status:
                    print("错误日志:")
                    print(final_status['error_log'])

        except Exception as e:
            print(f"❌ 训练启动失败: {e}")
            return 1

    finally:
        # 断开连接
        print("\n🔌 断开SSH连接...")
        ssh_manager.disconnect()
        print("✅ SSH连接已断开")

    print("\n🎊 SSH自动化训练演示完成！")
    print("\n📚 使用说明:")
    print("1. 配置SSH密钥和Autodl服务器信息")
    print("2. 在前端界面选择'Autodl远程训练'模式")
    print("3. 系统将自动上传文件并启动远程训练")
    print("4. 训练完成后可以下载模型")

    return 0

if __name__ == "__main__":
    sys.exit(main())
