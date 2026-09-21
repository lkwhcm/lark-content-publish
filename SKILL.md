---
name: lark-content-publish
description: 将发布员提供的单个或多个作品标题、链接、博主、数据员、发布日期、平台、业务板块、项目属性和 KPI 等信息登记到飞书「数据部门 · 内容数据采买与投流台账」的「内容表」，并在成功后通知对应数据员。用户说“登记作品”“批量上传作品”“录入发布内容”“把这些作品填进多维表格”“通知数据员”或提供新发布作品信息时使用；不用于回填每日实际数据或采买明细。
---

# 飞书作品登记

把发布员的自然语言整理为一条可追踪的正式内容记录。调用本 Skill 代表用户要完成整条工作流：校验、写表，以及写入成功后通知该记录的数据员。

## 固定目标

- Base：`数据部门 · 内容数据采买与投流台账`
- `base_token`：`QrCcbrLwaaxpA0sQRjUcvQgVnDh`
- 内容表：`tblnkOdFevMax0DF`
- 博主库：`tblBcH0gqFr8NHpC`
- 团队成员：`tblOvwr9eaOdnnhA`

表结构可能变化。每次提交前由脚本读取真实字段并校验，不凭本文件猜测新增字段。

## 执行入口

```bash
SKILL_DIR="$HOME/.agents/skills/lark-content-publish"
python3 "$SKILL_DIR/scripts/publish_work.py" status
python3 "$SKILL_DIR/scripts/publish_work.py" preflight
```

此 Skill 采用通用 Agent Skills 的 `SKILL.md + scripts + references` 结构。标准安装位置是 `~/.agents/skills/lark-content-publish`，安装脚本会为 Codex、Claude Code、Cursor、Gemini CLI 和 OpenCode 创建兼容入口。其他能够读取 `SKILL.md` 并执行 Python/终端命令的 Agent 也可直接使用。

通过私有 GitHub 仓库安装时，脚本会在每次命令开始前检查 `main` 分支，仅接受 fast-forward 更新。本地有改动或网络不可用时不会覆盖，也不会阻止现有版本运行。ZIP 复制安装无法自动更新。

若当前项目直接包含此 Skill，也可把 `SKILL_DIR` 指向项目中的 `lark-content-publish` 目录。

### 首次授权

全新电脑先按 [安装与初始化](references/installation.md) 安装通用 Agent Skill 并配置 `lark-cli`。Skill 包不包含飞书应用密钥或任何登录凭证。

`status` 显示用户身份未就绪时：

```bash
python3 "$SKILL_DIR/scripts/publish_work.py" auth-start
```

把返回的验证网址和验证码交给用户。用户完成网页授权后，再执行：

```bash
python3 "$SKILL_DIR/scripts/publish_work.py" auth-complete --device-code '<device_code>'
```

只申请本流程所需的精确权限：读取字段、读取记录、新建记录、以用户身份发消息。不要改成 `--domain base,contact,im`，域级授权会额外申请删表、改角色、群管理等本流程不需要的权限。不要切换或删除用户的 CLI profile。

## 从发布员输入提取信息

优先把自然语言整理为 JSON；不要要求发布员使用固定模板。单个作品使用一个对象；多个作品使用数组，或用 `defaults + works` 抽取共同信息。字段说明与批量示例见 [references/input-fields.md](references/input-fields.md)。

至少要得到：

- `title`：作品完整标题
- `url`：作品链接
- `blogger`：博主账号名

以下字段可自动补全：

- `publish_date` 未提供时使用上海时区今天；用户说“昨天/前天”时换算成明确日期。
- `platform` 优先从链接自动识别，否则继承博主主平台；手填平台与链接识别结果冲突时停止。
- `business_unit` 可从博主库继承。
- `data_staff` 未提供时继承博主库默认数据员；发布员明确提供时，以团队成员表中唯一、启用、角色含“数据员”的成员为准。
- `record_type` 固定为“正式数据”，除非用户明确说是演示或测试。

不要把客户 KPI 当成计划采买量。未提到的 KPI 和计划量一律留空；明确的 0 才写 0。

## 上线前置检查

首次安装、人员调整或表结构变化后运行 `preflight`。它只读检查内容表字段、合作中博主档案、启用数据员和飞书成员身份。返回含义见 [上线检查](references/preflight.md)。

- `trial_ready: true`：允许用真实但低风险的作品做一条端到端试运行；
- `registration_ready: true`：作品登记所需字段、博主和数据员身份完整，可使用登记流程；
- `production_ready: true`：与 `registration_ready` 同义，仅表示本 Skill 的登记与通知前置条件完整，不代表数据采集器已运行；
- `blockers` 非空：停止提交，先由管理员修复；

账号负责人是博主库中的业务文字归属，不要求本人加入飞书。不要尝试把负责人文字写入人员字段，也不要把负责人是否有飞书账号作为提交条件。

## 预览与提交

将整理后的 JSON 写到当前工作目录的临时文件（不要放到 Skill 目录），先预览：

```bash
python3 "$SKILL_DIR/scripts/publish_work.py" preview --json-file ./publish-input.json
```

预览会一次读取表结构和基础数据，校验整批作品，并返回每条最终写入字段、博主匹配、数据员身份和分组通知文案。出现以下任一情况时整批停止并一次性向发布员询问：

- 缺少标题、链接或博主；
- 博主库无匹配或匹配不唯一；新博主必须先明确要求建档；
- 数据员不存在、停用、重名或不具备数据员角色；
- 业务板块与博主档案冲突；
- 链接已存在于内容表。
- 同一批次内出现重复链接。

用户的“登记/录入/提交这个作品”请求已经授权创建这一条记录和通知匹配到的数据员；预览无歧义时直接提交，不再重复索取确认：

```bash
python3 "$SKILL_DIR/scripts/publish_work.py" submit --json-file ./publish-input.json
```

单批最多 200 个作品。每个作品独立成为一条记录；公共字段只是输入复用，不会把多件作品合并成一条。多个作品可以共用同一博主、数据员和负责人文字归属，也可以逐条不同。

成功后回报所有记录 ID、写入的关键字段和已通知的数据员。脚本保证先批量写表、后发消息；同一数据员的作品合并为一条通知（超过 20 个时分段），不同数据员分别通知。通知失败时记录仍然有效，明确报告“已写表但通知失败”，不要重建记录。

## 安全与一致性

- 始终以 `--as user` 读写和发消息。
- 不写公式、查找引用、创建时间、按钮等只读字段。
- 用规范化后的完整链接查重；命中已有记录时不创建重复项。
- 整批校验全部通过后才写入，避免已知错误造成部分提交。
- 只有表格创建成功才通知数据员。
- 通知使用记录 ID 派生的幂等键，避免同一记录重复发送。
- 不因通知失败删除已创建记录。
- 不自动创建博主、团队成员、字段、表或工作流；这些是独立的管理动作。
