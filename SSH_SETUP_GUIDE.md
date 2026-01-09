# SSH配置和Autodl自动化训练指南

本文档介绍如何配置SSH连接，实现自动化文件上传和远程训练功能。

## 📋 前置条件

1. **Autodl账号**：注册Autodl云服务器账号
2. **SSH客户端**：macOS/Linux系统已内置OpenSSH
3. **Python环境**：已配置senku conda环境

## 🔐 第一步：生成SSH密钥

### 1. 生成新的SSH密钥对

```bash
# 生成专门用于Autodl的SSH密钥
ssh-keygen -t rsa -b 4096 -C "your-email@example.com" -f ~/.ssh/id_rsa_autodl

# 设置密钥密码（可选，但推荐）
# 输入两次相同的密码
```

### 2. 查看生成的公钥

```bash
cat ~/.ssh/id_rsa_autodl.pub
```

输出示例：
```
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ... your-email@example.com
```

## 🚀 第二步：配置Autodl服务器

### 1. 登录Autodl控制台

访问 [Autodl控制台](https://www.autodl.com/console)

### 2. 创建或选择实例

- 选择适合的GPU实例（如RTX 3090/4090）
- 确保实例状态为"运行中"

### 3. 配置SSH密钥

#### 方法一：通过Web界面添加公钥

1. 在实例详情页，找到"SSH密钥"设置
2. 点击"添加SSH密钥"
3. 粘贴刚才生成的公钥内容

#### 方法二：手动添加公钥到服务器

1. 连接到服务器（使用临时密码）
2. 创建authorized_keys文件：

```bash
# 在服务器上执行
mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo "你的公钥内容" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### 4. 测试SSH连接

```bash
# 替换 your-autodl-server.com 为实际的服务器地址
ssh -i ~/.ssh/id_rsa_autodl root@your-autodl-server.com

# 如果设置了密码，会提示输入密码
```

## ⚙️ 第三步：配置环境变量

### 1. 创建或编辑 .env 文件

```bash
cp config.example.env .env
```

### 2. 编辑 .env 文件，添加SSH配置

```bash
# SSH和Autodl配置
SSH_HOSTNAME=your-autodl-server.com
SSH_USERNAME=root
SSH_KEY_FILENAME=~/.ssh/id_rsa_autodl
SSH_REMOTE_WORKSPACE=/root/workspace

# 训练执行模式
TRAINING_MODE=remote
```

### 3. 验证配置

```bash
# 在senku环境下
conda activate senku
python -c "from config import config; print(f'SSH主机: {config.SSH_HOSTNAME}')"
```

## 🧪 第四步：测试SSH连接

### 1. 运行SSH状态检查

```bash
# 启动后端服务器
python start_server.py

# 在另一个终端，启动前端
python start_client.py

# 在浏览器中访问前端界面
# 点击"检查SSH连接"按钮
```

### 2. 运行演示脚本

```bash
conda activate senku
python ssh_training_demo.py
```

## 🎯 第五步：使用自动化训练

### 1. 启动服务

```bash
# 终端1：启动后端
conda activate senku && python start_server.py

# 终端2：启动前端
conda activate senku && CLIENT_PORT=5001 python start_client.py
```

### 2. 在Web界面中使用

1. **访问前端**：http://localhost:5001
2. **选择角色**：从角色列表中选择一个角色
3. **选择训练模式**：
   - ✅ 本地训练：直接在本机训练
   - 🌐 Autodl远程训练：使用SSH自动上传到云端训练
4. **配置参数**：
   - 批次大小
   - 训练轮数
   - 学习率
   - 是否使用LoRA
5. **开始训练**：点击"开始训练"按钮
6. **监控进度**：实时查看训练状态
7. **下载模型**：训练完成后下载模型

## 🔧 故障排除

### SSH连接失败

**问题**：`SSH连接失败`
**解决方法**：
1. 检查SSH密钥文件路径是否正确
2. 确认密钥文件权限：`chmod 600 ~/.ssh/id_rsa_autodl`
3. 验证服务器地址和端口
4. 检查防火墙设置

### 权限被拒绝

**问题**：`Permission denied (publickey)`
**解决方法**：
1. 确认公钥已添加到服务器的 `~/.ssh/authorized_keys`
2. 检查密钥文件权限
3. 确认使用正确的用户名（通常是root）

### 训练启动失败

**问题**：`Failed to start training`
**解决方法**：
1. 检查远程服务器是否有足够的磁盘空间
2. 确认Python和必要的包已安装
3. 查看服务器日志：`tail -f /root/workspace/training.log`

## 📊 监控和日志

### 本地日志

- 后端日志：查看终端输出
- 前端日志：浏览器开发者工具控制台

### 远程日志

```bash
# 连接到Autodl服务器
ssh -i ~/.ssh/id_rsa_autodl root@your-autodl-server.com

# 查看训练日志
tail -f /root/workspace/training.log

# 查看系统资源使用
nvidia-smi
htop
```

## 🚀 高级配置

### 多SSH密钥管理

如果您有多个Autodl实例，可以创建不同的密钥：

```bash
# 为不同实例创建不同密钥
ssh-keygen -t rsa -b 4096 -C "instance1" -f ~/.ssh/id_rsa_autodl_1
ssh-keygen -t rsa -b 4096 -C "instance2" -f ~/.ssh/id_rsa_autodl_2
```

### SSH配置优化

创建 `~/.ssh/config` 文件：

```bash
# ~/.ssh/config
Host autodl-1
    HostName your-server-1.com
    User root
    IdentityFile ~/.ssh/id_rsa_autodl_1
    IdentitiesOnly yes

Host autodl-2
    HostName your-server-2.com
    User root
    IdentityFile ~/.ssh/id_rsa_autodl_2
    IdentitiesOnly yes
```

然后可以在 `.env` 中使用：
```bash
SSH_HOSTNAME=autodl-1
```

## 📞 获取帮助

如果遇到问题，请：

1. 检查本文档的故障排除部分
2. 查看终端和浏览器控制台的错误信息
3. 运行演示脚本测试基本功能
4. 联系技术支持

---

🎉 配置完成后，您就可以享受全自动化的AI模型微调体验了！
