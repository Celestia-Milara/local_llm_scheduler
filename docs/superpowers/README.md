# Superpowers 文档规范

## 目录结构

```
docs/superpowers/
├── README.md          # 本文件：规范说明
├── plans/             # 实施计划（implementation plan）
└── specs/             # 设计规格（design spec）
```

## 命名规范

```
/*.md 文件仅允许以下例外：*/
CLAUDE.md          # 项目指导文档
design.md          # 技术设计与实现规格说明书（全局架构）

/*.md 文件不允许出现在根目录：*/
plan*.md → docs/superpowers/plans/
spec*.md → docs/superpowers/specs/
design*.md → docs/superpowers/specs/
```

### 文件命名

```
YYYY-MM-DD-<version>-<topic>-<type>.md
```

| 段 | 说明 | 示例 |
| :--- | :--- | :--- |
| `YYYY-MM-DD` | 创建日期 | `2026-04-29` |
| `<version>` | 版本标识 | `v2.0`, `v3.0` |
| `<topic>` | 内容简述，kebab-case | `frontend-v2-ui`, `full-implementation` |
| `<type>` | 类型 | `design`, `implementation-plan` |

完整示例：
- `2026-04-29-frontend-v2-ui-design.md`
- `2026-04-29-v2.0-full-implementation-plan.md`
- `2026-05-04-frontend-v3-design.md`
- `2026-05-04-frontend-v3-implementation-plan.md`
