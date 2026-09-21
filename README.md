# 飞书作品登记 Skill

供发布员通过 Agent 将单个或多个作品登记到飞书「数据部门 · 内容数据采买与投流台账」，自动识别平台、匹配博主和数据员，并在写入成功后通知对应数据员。

## 安装

需要 Git、Python 3、Codex 和已配置的 `lark-cli`：

```bash
git clone https://github.com/lkwhcm/lark-content-publish.git ~/.codex/skills/lark-content-publish
python3 ~/.codex/skills/lark-content-publish/scripts/publish_work.py status
python3 ~/.codex/skills/lark-content-publish/scripts/publish_work.py preflight
```

飞书应用初始化、共享账号授权和最小权限说明见 [安装与初始化](references/installation.md)。Skill 仓库不包含 App Secret、OAuth Token 或本机 CLI 配置。

## 自动更新

通过 Git 克隆安装后，每次运行 Skill 命令前都会检查本仓库的 `main` 分支。有新提交时只执行安全的 fast-forward 更新，并自动重新运行当前命令。

- 断网或 GitHub 暂时不可用不会阻止现有版本工作；
- 本地文件被修改时不会覆盖，会提示跳过自动更新；
- 如需临时禁用，设置环境变量 `LARK_CONTENT_PUBLISH_DISABLE_AUTO_UPDATE=1`；
- ZIP 手工复制的安装没有 `.git`，因此不能自动更新。需要自动更新时必须使用上面的 `git clone` 安装方式。

## 使用

发布员直接向 Agent 提供作品标题、链接和博主即可；支持单条、批量以及公共字段复用。完整输入说明见 [输入字段](references/input-fields.md)。

```bash
python3 ~/.codex/skills/lark-content-publish/scripts/publish_work.py version
python3 ~/.codex/skills/lark-content-publish/scripts/publish_work.py preview --json-file ./publish-input.json
python3 ~/.codex/skills/lark-content-publish/scripts/publish_work.py submit --json-file ./publish-input.json
```
