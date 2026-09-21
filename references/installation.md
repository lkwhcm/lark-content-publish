# 安装与初始化

## 发布员电脑准备

1. 安装 `lark-cli`，确认终端运行 `lark-cli --version` 有正常输出。
2. 通过 Git 克隆安装，才能获得自动更新：

   ```bash
   git clone https://github.com/lkwhcm/lark-content-publish.git ~/.codex/skills/lark-content-publish
   ```

   如果目标目录已经存在，不要覆盖；先确认它是否为本仓库的 Git 克隆。手工复制 ZIP 可以使用，但不会自动更新。
3. 用管理员单独提供的飞书应用 App ID 和 App Secret 初始化 CLI。App Secret 不得写入 Skill、聊天消息、命令参数或共享文件；通过标准输入传递：

   ```bash
   lark-cli config init --app-id '<APP_ID>' --app-secret-stdin --brand feishu
   ```

4. 让 Agent 运行：

   ```bash
   python3 ~/.codex/skills/lark-content-publish/scripts/publish_work.py auth-start
   ```

5. 发布员用共享飞书账号打开验证链接并确认。再把“已授权”告诉 Agent，由 Agent 执行 `auth-complete`。
6. 运行 `status`；只有返回 `ready: true` 才表示 CLI、登录和四项最小权限全部就绪。
7. 运行 `preflight`；`trial_ready: true` 和 `registration_ready: true` 表示登记流程前置条件已满足。数据采集器不在此检查范围内。

如果 Agent 运行环境要求使用 `lark-cli config bind`，按该环境已有应用绑定流程操作，不要在 Skill 包里分发 App Secret。

## 权限范围

本 Skill 只申请：

- `base:field:read`：读取内容表字段定义；
- `base:record:read`：查询博主、团队成员和重复链接；
- `base:record:create`：新增作品记录；
- `im:message.send_as_user`：写表成功后通知数据员。

共享飞书账号本身还必须拥有目标 Base 的访问和新增记录权限。权限 scope 不会绕过 Base 的资源访问控制。

## 不随包分发

- App Secret；
- OAuth access/refresh token；
- 二维码、device code 或临时授权链接；
- 本机 `~/.lark-cli` 配置；
- 发布员或管理员的个人信息缓存。
