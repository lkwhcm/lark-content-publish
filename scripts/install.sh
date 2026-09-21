#!/usr/bin/env bash
set -euo pipefail

repository="https://github.com/lkwhcm/lark-content-publish.git"
agent_user_home="${AGENT_SKILLS_USER_HOME:-$HOME}"
canonical_dir="$agent_user_home/.agents/skills/lark-content-publish"

if ! command -v git >/dev/null 2>&1; then
  echo "错误：未找到 git。" >&2
  exit 1
fi

mkdir -p "$agent_user_home/.agents/skills"

if [ -e "$canonical_dir" ] || [ -L "$canonical_dir" ]; then
  if [ ! -d "$canonical_dir/.git" ]; then
    echo "错误：$canonical_dir 已存在且不是本 Skill 的 Git 工作副本；为避免覆盖，安装已停止。" >&2
    exit 1
  fi
  existing_remote="$(git -C "$canonical_dir" remote get-url origin 2>/dev/null || true)"
  case "$existing_remote" in
    "$repository"|"https://github.com/lkwhcm/lark-content-publish"|"git@github.com:lkwhcm/lark-content-publish.git") ;;
    *)
      echo "错误：现有目录的 origin 不是 lkwhcm/lark-content-publish；安装已停止。" >&2
      exit 1
      ;;
  esac
  if [ -n "$(git -C "$canonical_dir" status --porcelain)" ]; then
    echo "错误：现有 Skill 有本地修改；为避免覆盖，安装已停止。" >&2
    exit 1
  fi
  git -C "$canonical_dir" pull --ff-only origin main
else
  if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
    gh auth setup-git
    gh repo clone lkwhcm/lark-content-publish "$canonical_dir"
  else
    git clone "$repository" "$canonical_dir"
  fi
fi

link_skill() {
  link_path="$1"
  mkdir -p "$(dirname "$link_path")"
  if [ -L "$link_path" ]; then
    current_target="$(readlink "$link_path")"
    if [ "$current_target" = "$canonical_dir" ]; then
      return
    fi
    echo "警告：$link_path 已是其他软链接，未覆盖。" >&2
    return
  fi
  if [ -e "$link_path" ]; then
    echo "警告：$link_path 已存在，未覆盖。" >&2
    return
  fi
  ln -s "$canonical_dir" "$link_path"
}

link_skill "$agent_user_home/.codex/skills/lark-content-publish"
link_skill "$agent_user_home/.claude/skills/lark-content-publish"
link_skill "$agent_user_home/.cursor/skills/lark-content-publish"
link_skill "$agent_user_home/.gemini/skills/lark-content-publish"
link_skill "$agent_user_home/.config/opencode/skills/lark-content-publish"

python3 "$canonical_dir/scripts/publish_work.py" version
echo "安装完成。请重启或刷新 Agent 的 Skills 列表。"
