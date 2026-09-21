# 输入字段

Agent 将发布员的自然语言转成一个 JSON 对象，再交给脚本校验。键名如下。

## 核心字段

| JSON 键 | 对应列 | 规则 |
|---|---|---|
| `title` | 作品标题 | 必填，保留完整标题 |
| `url` | 链接 | 必填，平台作品链接 |
| `blogger` | 博主 | 必填，按博主库 `博主ID`/别名匹配 |
| `data_staff` | 数据员 | 可省略；提供时按团队成员 `姓名` 或飞书显示名精确匹配 |
| `publish_date` | 发布日期 | `YYYY-MM-DD`；默认上海时区今天 |
| `platform` | 平台 | 抖音 / 小红书 / 视频号 / B站 / 快手 / 公众号 |
| `business_unit` | 业务板块 | 汽车第一机构 / 云境引擎机构 / 拉克自营AIGC |
| `project_type` | 项目属性 | 搭建 / 日更 / 星图商单 / 互选商单 / 商单分发 |
| `customer_budget` | 客户预算 | 数字；未知不要填 0 |
| `notes` | 备注 | 可选自由文本 |

## KPI 与计划采买量

KPI 键：`like_kpi`、`comment_kpi`、`favorite_kpi`、`share_kpi`、`play_kpi`、`heart_kpi`、`thumb_kpi`、`double_kpi`。

计划量键：`plan_like`、`plan_comment`、`plan_favorite`、`plan_share`、`plan_play`、`plan_heart`、`plan_thumb`、`plan_double`。

视频号双点单位为“对”。KPI 是客户验收要求，计划采买量是准备下单的数量，两者不能互相推断。

## 示例

发布员可以自然表达：

> 超感帧AIGC 今天在视频号发了《AI 让旧照片重新说话》，链接 https://weixin.qq.com/sph/example，数据员熊莉，日更，播放 KPI 50 万、评论 KPI 100。

Agent 整理为：

```json
{
  "title": "AI 让旧照片重新说话",
  "url": "https://weixin.qq.com/sph/example",
  "blogger": "超感帧AIGC",
  "data_staff": "熊莉",
  "publish_date": "2026-09-21",
  "platform": "视频号",
  "project_type": "日更",
  "play_kpi": 500000,
  "comment_kpi": 100
}
```

也接受中文列名作为 JSON 键，例如 `作品标题`、`链接`、`博主`、`数据员`、`发布日期`、`平台`、`业务板块`、`项目属性`、`点赞KPI`。

## 批量输入

如果多件作品共用博主、数据员、发布日期、业务板块或项目属性，把相同信息放在 `defaults`，每件作品只写差异项。每条作品都可以覆盖默认值：

```json
{
  "defaults": {
    "blogger": "超感帧AIGC",
    "data_staff": "熊莉",
    "publish_date": "2026-09-21",
    "business_unit": "拉克自营AIGC",
    "project_type": "日更"
  },
  "works": [
    {
      "title": "作品一",
      "url": "https://weixin.qq.com/sph/example-1",
      "play_kpi": 500000
    },
    {
      "title": "作品二",
      "url": "https://v.douyin.com/example-2",
      "platform": "抖音",
      "data_staff": "赵恒"
    }
  ]
}
```

也可直接传作品对象数组。单批最多 200 条。脚本先校验整批，发现已有链接、批内重复、人员或平台冲突时不会写入任何一条。

平台通常不必填写，脚本从链接域名识别：

- 抖音：`douyin.com`；
- 小红书：`xiaohongshu.com`、`xhslink.com`；
- 视频号：`weixin.qq.com/sph`、`channels.weixin.qq.com`；
- 公众号：`mp.weixin.qq.com`；
- B站：`bilibili.com`、`b23.tv`；
- 快手：`kuaishou.com`。

如果手填平台与链接识别结果冲突，停止提交并要求核对。无法识别链接域名时，才回退到博主库的主平台。
