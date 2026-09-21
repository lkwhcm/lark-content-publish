# Agent 兼容说明

本项目遵循 Agent Skills 的通用结构：根目录包含带 YAML frontmatter 的 `SKILL.md`，确定性操作位于 `scripts/`，详细资料位于 `references/`。

## 安装策略

唯一 Git 工作副本安装到：

```text
~/.agents/skills/lark-content-publish
```

`scripts/install.sh` 同时创建以下软链接，所有 Agent 共用同一份文件：

- `~/.codex/skills/lark-content-publish`
- `~/.claude/skills/lark-content-publish`
- `~/.cursor/skills/lark-content-publish`
- `~/.gemini/skills/lark-content-publish`
- `~/.config/opencode/skills/lark-content-publish`

Codex、Cursor、Gemini CLI 和 OpenCode可以直接发现 `~/.agents/skills/`；额外软链接用于兼容不同版本、明确个人 Skill 入口，以及 Claude Code。

## 通用调用

不支持自动发现 Agent Skills、但可以执行终端命令的 Agent，可以先读取仓库根目录的 `SKILL.md`，再调用：

```bash
python3 ~/.agents/skills/lark-content-publish/scripts/publish_work.py status
python3 ~/.agents/skills/lark-content-publish/scripts/publish_work.py preflight
python3 ~/.agents/skills/lark-content-publish/scripts/publish_work.py preview --json-file ./publish-input.json
python3 ~/.agents/skills/lark-content-publish/scripts/publish_work.py submit --json-file ./publish-input.json
```

Agent 必须具备读取本地 Skill 文件和运行 Python/`lark-cli` 的能力。纯网页聊天、没有本地文件或终端权限的 Agent 无法直接执行写表流程。

## 自动更新

自动更新通过 GitHub 公开仓库进行，不需要 GitHub 登录。离线时继续使用本机现有版本，不会阻止作品登记。
