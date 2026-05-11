# 隐私保护型日程助理 - 部署与运行指南

本项目是一个基于本地 LLM（通过 Ollama 驱动）的日程管理助手。为了保护您的隐私，所有的日程数据和 AI 推理均在您的本地环境运行，不调用任何外部云端 API。系统支持两种部署模式。

## 环境要求

1. **Python**: 3.10+
2. **Node.js**: 18+（用于前端构建与运行）
3. **Ollama**: 请确保已安装并运行 Ollama 环境 (https://ollama.com)
   - **Windows 用户注意**：Ollama 默认 API 地址为 `http://127.0.0.1:11434`。如果后端无法连接，请确保 Ollama 托盘图标显示已运行。

## 快速启动（本地模式，默认）

### 1. 准备本地 AI 模型
```bash
ollama pull qwen2.5:7b
```

### 2. 后端配置与运行
```bash
cd privacy_schedule_agent
# 建议创建并激活虚拟环境
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate

pip install -r requirements.txt
```

**配置环境变量**：
在 `privacy_schedule_agent/` 下新建 `.env` 文件（可全部省略，使用默认值）：
```env
# 必要：模型配置
BRAIN_MODEL=qwen2.5:7b
OLLAMA_HOST=http://localhost:11434

# 非必要：数据存储路径
DATABASE_URL=sqlite+aiosqlite:///./data/schedule.db

# 非必要：部署模式（local / cloud）
DEPLOY_MODE=local

LOG_LEVEL=INFO
```

**运行服务端**：
```bash
python main.py
```
后端服务将启动在 `http://0.0.0.0:8000`，同时托管前端静态页面。

### 3. 前端构建（首次或前端代码变更后）
```bash
cd privacy_schedule_agent/frontend
npm install
npm run build
```
构建产物输出到 `frontend/dist/`，由 FastAPI 自动托管。构建一次后除非前端代码变更，无需重复执行。

### 4. 访问
浏览器打开 `http://localhost:8000`，local 模式自动进入主界面，无需登录。

## 云端部署模式（DEPLOY_MODE=cloud）

用于多用户场景（如团队共享服务器），需额外配置 JWT 认证和可选加密。

### 1. 同本地模式的步骤 1-3

### 2. 配置 `.env` 增加：
```env
DEPLOY_MODE=cloud

# JWT 签名密钥（必须修改为随机字符串，用于 Token 签发）
JWT_SECRET=your-random-secret-please-change-in-production

# 可选：应用层加密密钥（不设置则使用会话级临时密钥）
# 可使用 python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 生成
ENCRYPTION_KEY=
```

### 3. 启动
```bash
python main.py
```

### 4. 使用
浏览器打开 `http://<服务器地址>:8000`，显示登录页，需要注册账号后登录使用。
用户数据通过 JWT 隔离，各自只能访问自己的日程。

### 5. 生产环境注意事项

| 项 | 说明 |
|---|---|
| `JWT_SECRET` | 必须设置为高强度随机字符串，不要使用默认值 |
| `ENCRYPTION_KEY` | 建议设置固定密钥，否则密钥随进程重启变化导致历史数据无法解密 |
| 端口暴露 | 默认 8000，建议使用 Nginx 反代并配置 HTTPS |
| 数据库备份 | SQLite 文件在 `data/schedule.db`，定期备份该文件即可 |
| Ollama 管理 | 生产环境建议配置 Ollama 为系统服务，确保开机自启 |

## Windows 环境特别说明

1. **虚拟环境激活**：CMD 使用 `.venv\Scripts\activate`，PowerShell 使用 `.\.venv\Scripts\Activate.ps1`
2. **C++ 构建工具**：如果遇到编译错误，安装 [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
3. **防火墙**：首次运行 `main.py` 时，Windows 防火墙可能弹出提醒，请允许访问
4. **路径编码**：项目已适配跨平台路径，若数据库无法创建请检查 `DATABASE_URL` 路径

## 如何使用

1. 浏览器打开前端地址（local 模式自动进入，cloud 模式需先注册/登录）
2. **对话**: 使用右侧 AI 面板，输入如 "帮我安排明天下午三点在公司开会"。支持流式打字机效果输出。
3. **快捷操作**: 输入框上方提供 5 个快捷按钮（添加日程、查看本周、查找空闲、周总结、导出日程）。
4. **冲突检查**: AI 自动检查时间/通勤冲突，发现冲突时要求用户确认后才保存。
5. **离线降级**: 如果 Ollama 未启动，前端会显示友好错误提示，不会白屏。

## 注意事项
- 首次运行时，后端自动在 `data/` 目录下创建 `schedule.db` SQLite 数据库。
- 后端服务必须保持运行，前端才能正常进行 AI 对话和日程数据交互。
- 所有 LLM 推理均在本地完成（Ollama），数据不出设备。
- 查看完整 API 路由和架构文档：`docs/project-reference.md`
