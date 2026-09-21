#!/usr/bin/env python3
"""Register published content in Feishu Base and notify its data specialist."""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
from pathlib import Path
from zoneinfo import ZoneInfo


BASE_TOKEN = "QrCcbrLwaaxpA0sQRjUcvQgVnDh"
BASE_URL = f"https://rcna76p1swzm.feishu.cn/base/{BASE_TOKEN}"
CONTENT_TABLE = "tblnkOdFevMax0DF"
BLOGGER_TABLE = "tblBcH0gqFr8NHpC"
TEAM_TABLE = "tblOvwr9eaOdnnhA"
TZ = ZoneInfo("Asia/Shanghai")
REQUIRED_SCOPES = "base:field:read base:record:read base:record:create im:message.send_as_user"
VERSION = "0.4.1"
TRUSTED_REPOSITORY = "https://github.com/lkwhcm/lark-content-publish.git"

PLATFORMS = {"抖音", "小红书", "视频号", "B站", "快手", "公众号"}
BUSINESS_UNITS = {"汽车第一机构", "云境引擎机构", "拉克自营AIGC"}
PROJECT_TYPES = {"搭建", "日更", "星图商单", "互选商单", "商单分发"}
RECORD_TYPES = {"正式数据", "演示数据", "待核实"}
MINIMUM_CONTENT_FIELDS = {
    "作品标题", "链接", "博主", "数据员", "发布日期", "平台",
    "业务板块", "记录性质", "达标标记", "采集状态",
}

ALIASES = {
    "作品标题": "title", "标题": "title", "title": "title",
    "链接": "url", "作品链接": "url", "url": "url",
    "博主": "blogger", "账号": "blogger", "博主ID": "blogger", "blogger": "blogger",
    "数据员": "data_staff", "data_staff": "data_staff",
    "发布日期": "publish_date", "发布时间": "publish_date", "publish_date": "publish_date",
    "平台": "platform", "platform": "platform",
    "业务板块": "business_unit", "板块": "business_unit", "business_unit": "business_unit",
    "项目属性": "project_type", "project_type": "project_type",
    "记录性质": "record_type", "record_type": "record_type",
    "客户预算": "customer_budget", "预算": "customer_budget", "customer_budget": "customer_budget",
    "备注": "notes", "notes": "notes",
    "点赞KPI": "like_kpi", "评论KPI": "comment_kpi", "收藏KPI": "favorite_kpi",
    "转发KPI": "share_kpi", "播放KPI": "play_kpi", "红心KPI": "heart_kpi",
    "大拇指KPI": "thumb_kpi", "双点KPI": "double_kpi",
    "计划采买点赞": "plan_like", "计划采买评论": "plan_comment",
    "计划采买收藏": "plan_favorite", "计划采买转发": "plan_share",
    "计划采买播放": "plan_play", "计划采买红心": "plan_heart",
    "计划采买大拇指": "plan_thumb", "计划采买双点": "plan_double",
}

FIELD_MAP = {
    "title": "作品标题", "url": "链接", "publish_date": "发布日期",
    "platform": "平台", "business_unit": "业务板块", "project_type": "项目属性",
    "customer_budget": "客户预算", "notes": "备注",
    "like_kpi": "点赞KPI", "comment_kpi": "评论KPI", "favorite_kpi": "收藏KPI",
    "share_kpi": "转发KPI", "play_kpi": "播放KPI", "heart_kpi": "红心KPI",
    "thumb_kpi": "大拇指KPI", "double_kpi": "双点KPI",
    "plan_like": "计划采买点赞", "plan_comment": "计划采买评论",
    "plan_favorite": "计划采买收藏", "plan_share": "计划采买转发",
    "plan_play": "计划采买播放", "plan_heart": "计划采买红心",
    "plan_thumb": "计划采买大拇指", "plan_double": "计划采买双点",
}

NUMERIC_KEYS = {
    "customer_budget", "like_kpi", "comment_kpi", "favorite_kpi", "share_kpi",
    "play_kpi", "heart_kpi", "thumb_kpi", "double_kpi", "plan_like",
    "plan_comment", "plan_favorite", "plan_share", "plan_play", "plan_heart",
    "plan_thumb", "plan_double",
}


class WorkflowError(RuntimeError):
    pass


def maybe_auto_update() -> None:
    """Fast-forward a Git installation before use; failures never block publishing."""
    if os.environ.get("LARK_CONTENT_PUBLISH_DISABLE_AUTO_UPDATE") == "1":
        return
    if os.environ.get("LARK_CONTENT_PUBLISH_UPDATED") == "1":
        return
    root = Path(__file__).resolve().parents[1]
    if not (root / ".git").exists() or not shutil.which("git"):
        return

    def git(*args: str, timeout: int = 20) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(root), *args], text=True, encoding="utf-8",
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout,
        )

    try:
        remote = git("remote", "get-url", "origin")
        accepted = {
            TRUSTED_REPOSITORY,
            TRUSTED_REPOSITORY.removesuffix(".git"),
            "git@github.com:lkwhcm/lark-content-publish.git",
        }
        if remote.returncode != 0 or remote.stdout.strip() not in accepted:
            return
        dirty = git("status", "--porcelain")
        if dirty.returncode != 0 or dirty.stdout.strip():
            print("[lark-content-publish] 检测到本地修改，已跳过自动更新。", file=sys.stderr)
            return
        fetched = git("fetch", "--quiet", "origin", "main")
        if fetched.returncode != 0:
            return
        local = git("rev-parse", "HEAD")
        upstream = git("rev-parse", "origin/main")
        if local.returncode != 0 or upstream.returncode != 0:
            return
        if local.stdout.strip() == upstream.stdout.strip():
            return
        ancestor = git("merge-base", "--is-ancestor", "HEAD", "origin/main")
        if ancestor.returncode != 0:
            print("[lark-content-publish] 远端历史无法快进，已跳过自动更新。", file=sys.stderr)
            return
        updated = git("merge", "--ff-only", "--quiet", "origin/main")
        if updated.returncode != 0:
            return
        print("[lark-content-publish] 已自动更新到最新版，正在继续当前命令。", file=sys.stderr)
        env = os.environ.copy()
        env["LARK_CONTENT_PUBLISH_UPDATED"] = "1"
        os.execve(sys.executable, [sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]], env)
    except (OSError, subprocess.TimeoutExpired):
        return


def cli_path() -> str:
    path = shutil.which("lark-cli")
    if not path:
        raise WorkflowError("未找到 lark-cli；请先安装：https://github.com/larksuite/cli")
    return path


def run(args: list[str], *, cwd: str | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        [cli_path(), *args], cwd=cwd, text=True, encoding="utf-8",
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if check and proc.returncode != 0:
        detail = proc.stdout.strip() or proc.stderr.strip() or f"exit {proc.returncode}"
        raise WorkflowError(f"lark-cli 调用失败：{detail}")
    return proc


def run_json(args: list[str], *, cwd: str | None = None) -> dict:
    proc = run(args, cwd=cwd)
    try:
        value = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise WorkflowError(f"lark-cli 返回的不是 JSON：{proc.stdout[:500]}") from exc
    if isinstance(value, dict) and value.get("ok") is False:
        raise WorkflowError(json.dumps(value, ensure_ascii=False))
    return value


def list_records(table_id: str, fields: list[str]) -> list[dict]:
    with tempfile.TemporaryDirectory(prefix="lark-publish-") as temp_dir:
        args = [
            "base", "+record-list", "--base-token", BASE_TOKEN, "--table-id", table_id,
            "--as", "user", "--format", "ndjson", "--output", "records.ndjson", "--overwrite",
        ]
        for field in fields:
            args.extend(["--field-id", field])
        run(args, cwd=temp_dir)
        rows = []
        with open(Path(temp_dir) / "records.ndjson", encoding="utf-8") as stream:
            for line in stream:
                if line.strip():
                    rows.append(json.loads(line))
        return rows


def norm_text(value: object) -> str:
    return re.sub(r"[\s\-_—·()（）]+", "", str(value or "")).casefold()


def scalar(value: object) -> object:
    return value[0] if isinstance(value, list) and value else value


def user_value(row: dict, field: str) -> dict | None:
    values = row.get(field) or []
    return values[0] if values else None


def canonical_url(value: str) -> str:
    raw = value.strip().rstrip("。，,；;")
    parsed = urllib.parse.urlsplit(raw if "://" in raw else "https://" + raw)
    if not parsed.netloc:
        raise WorkflowError(f"链接无效：{value}")
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    tracking = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "share_token"}
    query = [(k, v) for k, v in query if k.lower() not in tracking]
    path = parsed.path.rstrip("/") or "/"
    return urllib.parse.urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), path, urllib.parse.urlencode(query), ""))


def infer_platform(url: str) -> str | None:
    parsed = urllib.parse.urlsplit(url if "://" in url else "https://" + url)
    host, full = parsed.netloc.lower(), url.lower()
    if "douyin.com" in host:
        return "抖音"
    if "xiaohongshu.com" in host or "xhslink.com" in host:
        return "小红书"
    if "weixin.qq.com/sph" in full or "channels.weixin.qq.com" in host:
        return "视频号"
    if "mp.weixin.qq.com" in host:
        return "公众号"
    if "bilibili.com" in host or host.endswith("b23.tv"):
        return "B站"
    if "kuaishou.com" in host:
        return "快手"
    return None


def parse_number(value: object, name: str) -> int | float:
    if isinstance(value, bool):
        raise WorkflowError(f"{name} 必须是数字")
    if isinstance(value, (int, float)):
        return value
    text = str(value).strip().replace(",", "").replace("，", "")
    multiplier = 1
    if text.endswith("万"):
        multiplier, text = 10000, text[:-1]
    elif text.endswith("千"):
        multiplier, text = 1000, text[:-1]
    text = re.sub(r"(?:元|个|次|对)$", "", text.strip())
    try:
        number = float(text) * multiplier
    except ValueError as exc:
        raise WorkflowError(f"{name} 不是有效数字：{value}") from exc
    return int(number) if number.is_integer() else number


def parse_text(text: str) -> dict:
    result: dict[str, object] = {}
    for line in re.split(r"[\n\r]+", text):
        match = re.match(r"\s*([^:：]{1,20})\s*[:：]\s*(.*?)\s*$", line)
        if match and match.group(1).strip() in ALIASES:
            result[ALIASES[match.group(1).strip()]] = match.group(2).strip()
    url_match = re.search(r"https?://[^\s，,；;]+", text)
    if url_match and "url" not in result:
        result["url"] = url_match.group(0).rstrip("。.)）")
    for platform in PLATFORMS:
        if platform in text and "platform" not in result:
            result["platform"] = platform
            break
    date_match = re.search(r"\b(20\d{2})[-/.年](\d{1,2})[-/.月](\d{1,2})日?\b", text)
    if date_match and "publish_date" not in result:
        result["publish_date"] = f"{int(date_match.group(1)):04d}-{int(date_match.group(2)):02d}-{int(date_match.group(3)):02d}"
    return result


def normalize_keys(raw: dict) -> dict:
    return {ALIASES.get(key, key): value for key, value in raw.items()}


def load_payloads(args: argparse.Namespace) -> list[dict]:
    if args.json_file:
        with open(args.json_file, encoding="utf-8") as stream:
            raw = json.load(stream)
    else:
        raw = parse_text(args.text or "")
    if isinstance(raw, list):
        defaults, works = {}, raw
    elif isinstance(raw, dict) and any(key in raw for key in ("works", "作品列表", "作品")):
        defaults = raw.get("defaults", raw.get("公共信息", {}))
        works = raw.get("works", raw.get("作品列表", raw.get("作品")))
        if not isinstance(defaults, dict):
            raise WorkflowError("批量输入的 defaults/公共信息 必须是对象")
    elif isinstance(raw, dict):
        defaults, works = {}, [raw]
    else:
        raise WorkflowError("输入必须是单个作品对象、作品数组，或 defaults + works 批量对象")
    if not isinstance(works, list) or not works:
        raise WorkflowError("批量输入的 works/作品列表 必须是非空数组")
    if len(works) > 200:
        raise WorkflowError("单次最多提交 200 个作品")
    normalized_defaults = normalize_keys(defaults)
    payloads = []
    for index, work in enumerate(works, 1):
        if not isinstance(work, dict):
            raise WorkflowError(f"第 {index} 个作品必须是对象")
        payloads.append({**normalized_defaults, **normalize_keys(work)})
    return payloads


def resolve_blogger(name: str, rows: list[dict]) -> dict:
    active = [row for row in rows if "合作中" in (row.get("合作状态") or [])]
    needle, exact = norm_text(name), []
    for row in active:
        values = [row.get("博主ID")]
        values += re.split(r"[,，、;/；\n]+", str(row.get("别名/历史写法") or ""))
        if any(norm_text(value) == needle for value in values if value):
            exact.append(row)
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        raise WorkflowError(f"博主“{name}”匹配到多条档案，请先清理博主库重复项")
    names = [str(row.get("博主ID")) for row in active]
    close = difflib.get_close_matches(name, names, n=5, cutoff=0.4)
    hint = f"；相近候选：{', '.join(close)}" if close else ""
    raise WorkflowError(f"博主库找不到合作中的“{name}”{hint}。新博主需先明确建档。")


def resolve_staff(name: str | None, inherited: dict | None, rows: list[dict]) -> tuple[str, str]:
    active = [row for row in rows if "启用" in (row.get("成员状态") or []) and "数据员" in (row.get("角色") or [])]
    if name:
        needle, matches = norm_text(name), []
        for row in active:
            member = user_value(row, "飞书成员") or {}
            if needle in {norm_text(row.get("姓名")), norm_text(member.get("name"))}:
                matches.append(row)
        if len(matches) != 1:
            candidates = [str(row.get("姓名")) for row in matches or active]
            raise WorkflowError(f"数据员“{name}”没有唯一匹配；可用数据员：{', '.join(candidates)}")
        member = user_value(matches[0], "飞书成员")
    else:
        member = inherited
        if not member:
            raise WorkflowError("未提供数据员，且博主档案没有默认数据员")
        matches = [row for row in active if (user_value(row, "飞书成员") or {}).get("id") == member.get("id")]
        if len(matches) != 1:
            raise WorkflowError("博主默认数据员不在启用的团队数据员名单中")
    if not member or not member.get("id"):
        raise WorkflowError("数据员缺少有效飞书 open_id")
    display = str(matches[0].get("姓名") or member.get("name") or member["id"])
    return str(member["id"]), display


def load_context() -> dict:
    response = run_json([
        "base", "+field-list", "--base-token", BASE_TOKEN, "--table-id", CONTENT_TABLE,
        "--as", "user", "--format", "json",
    ])
    return {
        "bloggers": list_records(BLOGGER_TABLE, [
            "博主ID", "别名/历史写法", "合作状态", "主平台", "业务板块", "数据员", "负责人",
        ]),
        "staff": list_records(TEAM_TABLE, ["姓名", "成员状态", "角色", "飞书成员"]),
        "content": list_records(CONTENT_TABLE, ["作品标题", "链接"]),
        "fields": {item["name"]: item for item in response.get("data", {}).get("fields", [])},
    }


def check_fields(record: dict, fields: dict) -> None:
    missing = [name for name in record if name not in fields]
    if missing:
        raise WorkflowError(f"内容表缺少字段：{', '.join(missing)}")
    readonly = {"formula", "lookup", "created_at", "updated_at", "created_by", "updated_by", "auto_number", "button"}
    invalid = [name for name in record if fields[name].get("type") in readonly]
    if invalid:
        raise WorkflowError(f"尝试写入只读字段：{', '.join(invalid)}")


def find_duplicate(url: str, rows: list[dict]) -> dict | None:
    target = canonical_url(url)
    for row in rows:
        if row.get("链接") and canonical_url(str(row["链接"])) == target:
            return row
    return None


def prepare(payload: dict, context: dict, batch_urls: set[str]) -> dict:
    labels = {"title": "作品标题", "url": "链接", "blogger": "博主"}
    for key, label in labels.items():
        if not str(payload.get(key) or "").strip():
            raise WorkflowError(f"缺少必填信息：{label}")
    title, url = str(payload["title"]).strip(), canonical_url(str(payload["url"]))
    blogger = resolve_blogger(str(payload["blogger"]).strip(), context["bloggers"])
    duplicate = find_duplicate(url, context["content"])
    if duplicate:
        raise WorkflowError(f"该链接已登记：{duplicate.get('作品标题')}（record_id={duplicate.get('record_id')}）")
    if url in batch_urls:
        raise WorkflowError(f"本批次内链接重复：{url}")
    batch_urls.add(url)

    inherited_platform = scalar(blogger.get("主平台"))
    detected_platform = infer_platform(url)
    supplied_platform = str(payload.get("platform") or "")
    if supplied_platform and detected_platform and supplied_platform != detected_platform:
        raise WorkflowError(f"填写的平台“{supplied_platform}”与链接识别结果“{detected_platform}”冲突")
    platform = str(supplied_platform or detected_platform or inherited_platform or "")
    if platform not in PLATFORMS:
        raise WorkflowError(f"无法确定平台或平台无效：{platform or '空'}")
    inherited_unit = scalar(blogger.get("业务板块"))
    business_unit = str(payload.get("business_unit") or inherited_unit or "")
    if business_unit not in BUSINESS_UNITS:
        raise WorkflowError(f"无法确定业务板块或业务板块无效：{business_unit or '空'}")
    if inherited_unit and payload.get("business_unit") and business_unit != inherited_unit:
        raise WorkflowError(f"业务板块“{business_unit}”与博主档案“{inherited_unit}”冲突")
    project_type = payload.get("project_type")
    if project_type and str(project_type) not in PROJECT_TYPES:
        raise WorkflowError(f"项目属性无效：{project_type}")
    record_type = str(payload.get("record_type") or "正式数据")
    if record_type not in RECORD_TYPES:
        raise WorkflowError(f"记录性质无效：{record_type}")
    date_value = str(payload.get("publish_date") or dt.datetime.now(TZ).date().isoformat())
    try:
        dt.date.fromisoformat(date_value)
    except ValueError as exc:
        raise WorkflowError(f"发布日期必须是 YYYY-MM-DD：{date_value}") from exc

    staff_id, staff_name = resolve_staff(
        str(payload.get("data_staff")).strip() if payload.get("data_staff") else None,
        user_value(blogger, "数据员"), context["staff"],
    )
    record: dict[str, object] = {
        "作品标题": title, "链接": url, "博主": [{"id": blogger["record_id"]}],
        "数据员": [{"id": staff_id}], "发布日期": date_value, "平台": [platform],
        "业务板块": [business_unit], "记录性质": [record_type],
        "达标标记": ["未达标"], "采集状态": ["待采集"],
    }
    warnings = []
    owner_label = scalar(blogger.get("负责人"))
    if project_type:
        record["项目属性"] = [str(project_type)]
    for key, field in FIELD_MAP.items():
        if key in {"title", "url", "publish_date", "platform", "business_unit", "project_type"}:
            continue
        value = payload.get(key)
        if value is None or value == "":
            continue
        record[field] = parse_number(value, field) if key in NUMERIC_KEYS else str(value)
    check_fields(record, context["fields"])
    return {"record": record, "resolved": {
        "blogger": blogger.get("博主ID"), "blogger_record_id": blogger["record_id"],
        "data_staff": staff_name, "data_staff_open_id": staff_id,
        "platform": platform, "business_unit": business_unit,
        "owner": owner_label,
    }, "warnings": warnings}


def notification(prepared: dict, record_id: str) -> str:
    record, resolved = prepared["record"], prepared["resolved"]
    link = f"{BASE_URL}?table={CONTENT_TABLE}&record={record_id}"
    kpis = [f"{key} {value}" for key, value in record.items() if key.endswith("KPI")]
    lines = [
        f"📌 新作品已登记，请跟进数据：{record['作品标题']}",
        f"博主：{resolved['blogger']}｜平台：{resolved['platform']}｜发布日期：{record['发布日期']}",
        f"业务板块：{resolved['business_unit']}",
    ]
    if kpis:
        lines.append("客户 KPI：" + "；".join(kpis))
    lines.append(f"记录：{link}")
    return "\n".join(lines)


def grouped_notification(items: list[dict], record_ids: list[str]) -> str:
    if len(items) == 1:
        return notification(items[0], record_ids[0])
    lines = [f"📌 已登记 {len(items)} 个新作品，请跟进数据："]
    for index, (prepared, record_id) in enumerate(zip(items, record_ids), 1):
        record, resolved = prepared["record"], prepared["resolved"]
        link = f"{BASE_URL}?table={CONTENT_TABLE}&record={record_id}"
        lines.append(
            f"{index}. {record['作品标题']}｜{resolved['blogger']}｜{resolved['platform']}｜"
            f"{record['发布日期']}\n{link}"
        )
    return "\n".join(lines)


def create_records(prepared_items: list[dict]) -> list[str]:
    with tempfile.TemporaryDirectory(prefix="lark-publish-submit-") as temp_dir:
        payload_path = Path(temp_dir) / "payload.json"
        payload_path.write_text(json.dumps({
            "create_records": [item["record"] for item in prepared_items],
        }, ensure_ascii=False), encoding="utf-8")
        response = run_json([
            "base", "+record-batch-create", "--base-token", BASE_TOKEN, "--table-id", CONTENT_TABLE,
            "--json", "@payload.json", "--as", "user", "--format", "json",
        ], cwd=temp_dir)
    data = response.get("data") or response
    record_ids = data.get("record_id_list") or []
    if not record_ids and data.get("records"):
        record_ids = [item.get("record_id") for item in data["records"]]
    record_ids = [str(value) for value in record_ids if value]
    if len(record_ids) != len(prepared_items):
        raise WorkflowError(f"创建响应记录数不一致：{json.dumps(response, ensure_ascii=False)}")
    return record_ids


def send_group_notification(items: list[dict], record_ids: list[str]) -> None:
    staff_id = items[0]["resolved"]["data_staff_open_id"]
    key_source = "content-publish:" + ":".join(record_ids)
    key = hashlib.sha256(key_source.encode()).hexdigest()[:32]
    run_json([
        "im", "+messages-send", "--user-id", staff_id,
        "--text", grouped_notification(items, record_ids), "--idempotency-key", key,
        "--as", "user", "--format", "json",
    ])


def notification_groups(items: list[dict], record_ids: list[str], chunk_size: int = 20):
    grouped: dict[str, list[tuple[dict, str]]] = {}
    for item, record_id in zip(items, record_ids):
        staff_id = item["resolved"]["data_staff_open_id"]
        grouped.setdefault(staff_id, []).append((item, record_id))
    for pairs in grouped.values():
        for start in range(0, len(pairs), chunk_size):
            chunk = pairs[start:start + chunk_size]
            yield [pair[0] for pair in chunk], [pair[1] for pair in chunk]


def cmd_status() -> int:
    doctor = run(["doctor"], check=False)
    whoami = run(["whoami", "--as", "user"], check=False)
    scopes = run(["auth", "check", "--scope", REQUIRED_SCOPES, "--json"], check=False)
    def decode(proc: subprocess.CompletedProcess[str]) -> object:
        try:
            return json.loads(proc.stdout)
        except json.JSONDecodeError:
            return proc.stdout.strip() or proc.stderr.strip()
    ready = doctor.returncode == 0 and whoami.returncode == 0 and scopes.returncode == 0
    print(json.dumps({
        "doctor": decode(doctor), "whoami": decode(whoami),
        "required_scopes": decode(scopes), "ready": ready,
    }, ensure_ascii=False, indent=2))
    return 0 if ready else 1


def cmd_preflight() -> int:
    context = load_context()
    active_bloggers = [row for row in context["bloggers"] if "合作中" in (row.get("合作状态") or [])]
    active_staff = [
        row for row in context["staff"]
        if "启用" in (row.get("成员状态") or []) and "数据员" in (row.get("角色") or [])
    ]
    missing_fields = sorted(MINIMUM_CONTENT_FIELDS - set(context["fields"]))
    blogger_issues = {
        "missing_platform": [row.get("博主ID") for row in active_bloggers if not scalar(row.get("主平台"))],
        "missing_business_unit": [row.get("博主ID") for row in active_bloggers if not scalar(row.get("业务板块"))],
        "missing_data_staff": [row.get("博主ID") for row in active_bloggers if not user_value(row, "数据员")],
    }
    staff_without_identity = [row.get("姓名") for row in active_staff if not user_value(row, "飞书成员")]
    blockers = []
    if missing_fields:
        blockers.append("内容表缺少必需字段：" + "、".join(missing_fields))
    if not active_bloggers:
        blockers.append("博主库没有合作中的博主")
    if not active_staff:
        blockers.append("团队成员表没有启用的数据员")
    if blogger_issues["missing_platform"]:
        blockers.append("合作中博主缺少主平台")
    if blogger_issues["missing_business_unit"]:
        blockers.append("合作中博主缺少业务板块")
    if blogger_issues["missing_data_staff"]:
        blockers.append("合作中博主缺少默认数据员")
    if staff_without_identity:
        blockers.append("启用数据员缺少飞书成员身份")
    warnings = []
    print(json.dumps({
        "ok": not blockers,
        "trial_ready": not blockers,
        "registration_ready": not blockers,
        "production_ready": not blockers,
        "base_url": BASE_URL,
        "counts": {
            "active_bloggers": len(active_bloggers),
            "active_data_staff": len(active_staff),
            "existing_content_records": len(context["content"]),
        },
        "missing_content_fields": missing_fields,
        "blogger_issues": blogger_issues,
        "staff_without_identity": staff_without_identity,
        "blockers": blockers,
        "warnings": warnings,
        "notes": [
            "此命令只读，不检查内容采集器是否运行，也不验证自动化在 API 新建记录后是否触发。",
            "账号负责人按博主库中的文字归属展示，不要求本人加入飞书，也不写入人员字段。",
            "数据采集器属于后续数据链路；尚未运行不影响作品登记和通知数据员。",
        ],
    }, ensure_ascii=False, indent=2))
    return 0 if not blockers else 1


def main() -> int:
    maybe_auto_update()
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="检查 CLI、配置和用户授权")
    sub.add_parser("version", help="显示 Skill 版本")
    sub.add_parser("preflight", help="只读检查目标表、人员和博主档案是否可用")
    sub.add_parser("auth-start", help="启动飞书设备授权")
    complete = sub.add_parser("auth-complete", help="完成飞书设备授权")
    complete.add_argument("--device-code", required=True)
    for name in ("preview", "submit"):
        command = sub.add_parser(name, help="只读预览" if name == "preview" else "写入并通知")
        source = command.add_mutually_exclusive_group(required=True)
        source.add_argument("--json-file")
        source.add_argument("--text")
        if name == "submit":
            command.add_argument("--no-notify", action="store_true", help="仅在用户明确要求时跳过通知")
    args = parser.parse_args()
    try:
        if args.command == "status":
            return cmd_status()
        if args.command == "version":
            print(json.dumps({"name": "lark-content-publish", "version": VERSION}, ensure_ascii=False))
            return 0
        if args.command == "preflight":
            return cmd_preflight()
        if args.command == "auth-start":
            print(run([
                "auth", "login", "--scope", REQUIRED_SCOPES, "--no-wait", "--json",
            ]).stdout.strip())
            return 0
        if args.command == "auth-complete":
            print(run(["auth", "login", "--device-code", args.device_code, "--json"]).stdout.strip())
            return 0
        payloads = load_payloads(args)
        context, batch_urls, prepared_items = load_context(), set(), []
        for index, payload in enumerate(payloads, 1):
            try:
                prepared_items.append(prepare(payload, context, batch_urls))
            except WorkflowError as exc:
                raise WorkflowError(f"第 {index} 个作品：{exc}") from exc
        if args.command == "preview":
            placeholder_ids = [f"<创建后生成-{index}>" for index in range(1, len(prepared_items) + 1)]
            previews = [
                {
                    "data_staff": group[0]["resolved"]["data_staff"],
                    "work_count": len(group),
                    "message": grouped_notification(group, ids),
                }
                for group, ids in notification_groups(prepared_items, placeholder_ids)
            ]
            print(json.dumps({
                "ok": True, "mode": "preview", "work_count": len(prepared_items),
                "items": prepared_items, "notification_previews": previews,
            }, ensure_ascii=False, indent=2))
            return 0
        record_ids = create_records(prepared_items)
        records = [
            {
                "record_id": record_id,
                "record_url": f"{BASE_URL}?table={CONTENT_TABLE}&record={record_id}",
                "title": item["record"]["作品标题"],
                "resolved": item["resolved"],
                "warnings": item["warnings"],
            }
            for item, record_id in zip(prepared_items, record_ids)
        ]
        result = {
            "ok": True, "records_created": len(records), "records": records,
            "notifications_sent": 0, "notification_errors": [],
        }
        if len(records) == 1:
            result.update(record_id=records[0]["record_id"], record_url=records[0]["record_url"])
        if not args.no_notify:
            for group, ids in notification_groups(prepared_items, record_ids):
                try:
                    send_group_notification(group, ids)
                    result["notifications_sent"] += 1
                except WorkflowError as exc:
                    result["notification_errors"].append({
                        "data_staff": group[0]["resolved"]["data_staff"],
                        "record_ids": ids,
                        "error": str(exc),
                    })
            if result["notification_errors"]:
                result.update(ok=False, partial_success=True)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["ok"] else 2
    except (WorkflowError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
