# CLAUDE.md

本文件是本仓库的 AI 代理执行规范（面向 Copilot CLI / Claude Code 一类代码代理）。

## 1. 核心规则

- **必须使用中文回答用户的所有问题。**
- 默认在 `privacy_schedule_agent/` 下开展实现、调试与验证工作。

## 2. 适用范围与优先级

- 本文件用于约束本仓库内的实现行为，不替代系统级安全与平台策略。
- 出现冲突时，遵循优先级：**系统/平台策略 > 用户当前明确指令 > 本文件**。
- 详细项目背景、架构、命令和环境变量不在本文件展开，统一放在 `docs/project-reference.md`。

## 3. 行为边界（Do / Don't）

### Do

- 保持“隐私优先”设计：LLM 推理应走本地 Ollama。
- 涉及日程创建逻辑时，保持“冲突先检查、冲突需明确确认后保存”的业务约束。
- 修改用户可见文案时，保持简体中文风格一致。
- SSE 流式端点（`/chat/stream`）使用 `text/event-stream` 格式，事件类型为 `step` / `token` / `done`。
- 新增 Skill 时遵循目录结构：`app/skill/skills/<skill-name>/` 下放 `.md` 指令 + `scripts/` 子目录。
- 涉及隐私字段（`title`、`description`）写入数据库前使用 `app.core.crypto.encrypt_dict()` 加密。

### Don't

- 不要默认接入外部云端 LLM API 替换本地推理链路。
- 不要绕过冲突确认机制直接落库。
- 不要在无必要情况下改动与当前任务无关的模块。
- 不要在 `DEPLOY_MODE=local` 时启用 JWT 认证中间件（纯本地单用户无需认证）。
- 不要修改加密字段的索引列（id、时间、user_id 不加密）。

## 4. 变更与验证要求

- 仅文档改动：无需额外运行构建或测试。
- 后端改动：至少执行与变更相关的后端测试（当前为 `pytest` 流程）。
- 前端改动：至少执行前端构建与相关测试（如 `npm run build`、`node --test tests/calendar.test.js`）。
- 若仓库新增标准化检查命令（lint/test/build），优先复用现有命令，不引入重复工具链。

## 5. 失败处理约定

- 命令失败时，先给出关键错误原因，再选择最小替代方案继续推进。
- 若失败由环境前置条件缺失导致（如 Ollama 未启动、模型未拉取），应明确指出缺失项。

## 6. 参考文档

- 项目参考总览：`docs/project-reference.md`
