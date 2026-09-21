# 更新记录

## 0.4.2

- 仓库改为公开可读，方便 WorkBuddy 和其他 Agent 直接发现、安装和更新；
- 安装与自动更新不再要求 GitHub 组织成员身份或 GitHub 登录。

## 0.4.1

- 安装私有仓库前主动配置 GitHub CLI 的 Git 凭证；
- 支持隔离目录安装测试，不影响正式用户目录。

## 0.4.0

- 仓库改为 `lkwhcm` 组织私有仓库；
- 从 Codex 专用安装改为通用 Agent Skills 安装；
- 统一安装到 `~/.agents/skills/`，适配 Codex、Claude Code、Cursor、Gemini CLI 和 OpenCode；
- 新增安全的多 Agent 安装器和兼容说明；
- 所有 Agent 共用同一 Git 工作副本和自动更新链路。

## 0.3.0

- 发布到 `lkwhcm/lark-content-publish`；
- Git 安装后每次使用前自动安全更新；
- 新增版本查询命令；
- 明确负责人为外部文字归属，不要求飞书账号；
- 明确数据采集器与作品登记分阶段上线。

## 0.2.1

- 新增只读上线预检；
- 支持负责人文字归属；
- 支持单条、批量、平台识别和按数据员合并通知。
