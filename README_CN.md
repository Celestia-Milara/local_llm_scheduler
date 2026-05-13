# 本地大模型隐私日程管理系统（Local LLM Privacy Scheduler）

这是一个“隐私优先”的日程管理系统：通过**本地大模型**（Ollama）+ **Skill/工具调用框架**实现自然语言创建/查询日程，并遵循“**先检查冲突，冲突需用户确认后才保存**”的业务约束。

## 特性

- **本地推理**：默认不接入云端 LLM，面向离线/隐私场景
- **Skill/工具体系**：将日程操作、冲突检查等能力以工具形式提供给模型调用
- **冲突优先**：时间/通勤冲突会先提示，并在确认后才落库
- **敏感字段加密**：写入数据库前对 `title` / `description` 做加密处理
- **Web 界面**：Vue 3 前端，支持流式（Streaming）对话体验

## 目录结构

- `privacy_schedule_agent/`：后端（FastAPI）
- `privacy_schedule_agent/frontend/`：前端（Vue 3）

## 环境准备

- Python 3.10+（建议 3.11+）
- Node.js 18+
- Ollama 已安装并运行

## 快速开始（本地模式）

### 1）启动后端

```bash
cd privacy_schedule_agent
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

后端默认地址：`http://localhost:8000`

### 2）启动前端

```bash
cd privacy_schedule_agent/frontend
npm install
npm run dev
```

## 配置说明

项目支持本地单用户模式与可选的 cloud（多用户）模式。

### 本地模式（默认）

默认不启用鉴权中间件。

### Cloud 模式（可选）

你可以在 `privacy_schedule_agent/.env` 中设置（该文件已被 git 忽略，不会推送）：

```env
DEPLOY_MODE=cloud
JWT_SECRET=请改成随机高强度字符串
# 可选：应用层加密密钥（Fernet）
ENCRYPTION_KEY=
```

## 数据与隐私提示

- SQLite 数据库文件：`privacy_schedule_agent/data/schedule.db`（已被 git 忽略）
- 不要提交：`.env`、token、私钥、数据库文件等任何敏感内容

## License

TBD
