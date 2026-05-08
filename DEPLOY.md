# 隐私保护型日程助理 - 部署与运行指南

本项目是一个基于本地 LLM（通过 Ollama 驱动）的日程管理助手。为了保护您的隐私，所有的日程数据和 AI 推理均在您的本地环境运行，不调用任何外部云端 API。

## 环境要求

1. **Python**: 3.10+
2. **Node.js**: 18+ (用于前端构建与运行)
3. **Ollama**: 请确保已安装并运行 Ollama 环境 (https://ollama.com)
   * **Windows 用户注意**：在 Windows 上运行 Ollama 时，它的默认 API 地址通常是 `http://127.0.0.1:11434` 或 `http://localhost:11434`。如果后端无法连接，请确保 Ollama 托盘图标显示已运行。

## 快速启动步骤

### 1. 准备本地 AI 模型 (Ollama)
在终端运行以下命令，拉取本项目推荐的推理模型：
```bash
ollama pull qwen2.5:7b
```

### 2. 后端配置与运行
进入项目目录并安装 Python 依赖：
```bash
cd privacy_schedule_agent
# 建议创建并激活虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows 使用: .venv\Scripts\activate

pip install -r requirements.txt
```

**配置环境变量**：
在 `privacy_schedule_agent` 目录下新建 `.env` 文件，填入以下内容：
```env
BRAIN_MODEL=qwen2.5:7b
OLLAMA_HOST=http://localhost:11434
DATABASE_URL=sqlite+aiosqlite:///./data/schedule.db
LOG_LEVEL=INFO
```

**运行服务端**：
```bash
python main.py
```
后端服务将启动在 `http://0.0.0.0:8000`。

### 3. 前端配置与运行
在另一个终端中进入前端目录：
```bash
cd privacy_schedule_agent/frontend
npm install
npm run dev
```
前端开发服务器将启动，通常地址为 `http://localhost:5173`。

### 4. Windows 环境特别说明

如果对方在 Windows (非 WSL) 环境下运行，请注意以下几点：

1. **虚拟环境激活**：
   Windows 命令行 (CMD) 使用 `.venv\Scripts\activate`，PowerShell 使用 `.\.venv\Scripts\Activate.ps1`。
2. **C++ 构建工具**：
   安装 Python 依赖时，如果遇到 `aiosqlite` 或其他库编译错误，可能需要安装 [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)。
3. **网络访问**：
   首次运行 `main.py` 时，Windows 防火墙可能会弹出提醒，请务必勾选“允许访问”，否则前端无法连接到后端 API。
4. **路径编码**：
   本项目已适配跨平台路径，但在极少数情况下，如果数据库无法创建，请检查 `DATABASE_URL` 中的路径格式。

## 如何使用

1. 打开浏览器访问前端地址。
2. **登录**: 默认用户名为 `root`，密码为 `root`（目前为演示版，本地存储验证）。
3. **对话**: 使用右侧的 AI 面板，输入如 "帮我安排明天下午三点在公司开会" 即可。
4. **冲突检查**: AI 会自动检查该时间段是否有其他日程或是否有通勤时间冲突。

## 注意事项
- 首次添加日程时，后端会自动在 `data/` 目录下创建 `schedule.db` SQLite 数据库。
- 后端服务必须保持运行，前端才能正常进行 AI 对话和日程数据交互。
