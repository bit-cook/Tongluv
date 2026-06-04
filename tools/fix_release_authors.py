# -*- coding: utf-8 -*-
"""修复 GitHub Release 作者：删除 github-actions[bot] 的 release 并以 weidaozhong 身份重建。"""
import io
import json
import os
import sys
import urllib.request
import urllib.error

# 强制 stdout 使用 UTF-8，避免 Windows GBK 编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PAT = os.environ.get("GH_PAT", "")
if not PAT:
    print("错误：请先设置环境变量 GH_PAT")
    print('  $env:GH_PAT = "你的token"')
    sys.exit(1)

REPO = "weidaozhong/Tongluv"
API = f"https://api.github.com/repos/{REPO}"
HEADERS = {
    "Authorization": f"Bearer {PAT}",
    "Accept": "application/vnd.github+json",
}

BODY_V100 = "**Full Changelog**: https://github.com/weidaozhong/Tongluv/commits/v1.0.0"

BODY_V102 = """\
### ✨ 快捷倒计时（新功能）

- 新增快捷倒计时功能：预设时间 / 自定义时长 / 标签分类
- 新增桌宠头顶倒计时浮窗，实时显示剩余时间
- 新增到点提醒气泡，支持持久显示与堆叠管理
- 新增提醒窗口，支持时 / 分 / 秒精确输入 + 暂停 / 重置
- 托盘菜单新增快捷倒计时入口
- 头顶浮窗元素防重叠堆叠优化

### 🐛 修复

- 修复体力值消耗过快导致桌宠频繁入睡的问题
- 清醒体力消耗：`0.008/s` → `0.003/s`（满体力可撑约 7.4 小时）
- 睡眠体力恢复：`0.02/s` → `0.06/s`（入睡后约 17 分钟自动醒来）
"""

BODY_V103 = """\
### 🍅 番茄钟（新功能）

- 新增完整番茄钟功能：专注 → 短休 → 专注 → …… → 长休，自动循环
- 内置 4 种预设模式：经典 25/5、深度 50/10、轻量 15/3、长时 45/15
- 支持自定义专注 / 短休 / 长休时长及每几轮后长休，配置自动持久化
- 标题栏重置按钮 ↺ 一键还原默认时长（25/5/15/4）
- 番茄钟配置独立存储为 `pomodoro_config.json`，迁移友好、可单独删除不影响其它数据

### 🐾 桌宠联动

- 专注期间桌宠自动切换学习姿势（抑制自动走动 / 说话 / 睡觉）
- 被打断回到 idle 时自动重新埋头学习
- 专注期间偶尔冒出 1~2 句鼓励气泡（不触发动画，不打断学习姿势）
- 阶段切换自动播报
- 专注阶段桌宠 study 动画，休息阶段 wake 动画

### 🪟 界面改版

- 提醒窗口改为左右两栏布局：快捷倒计时（左）/ 番茄钟（右），去除滚动条
- 番茄钟状态小字移到按钮上方，使两侧主按钮上边对齐
- 头顶浮窗实时显示番茄钟阶段与剩余时间
- 提醒入口从托盘菜单迁移到桌宠右键菜单（不透明度下方），做成同款行样式

### 🔀 前台互斥

- 番茄钟与快捷倒计时为前台计时器二选一：启动一个自动停止另一个
"""

RELEASES = [
    {"tag": "v1.0.0", "name": "\u84dd\u8272\u5c0f\u55f5 v1.0.0", "body": BODY_V100},
    {"tag": "v1.0.2", "name": "\u84dd\u8272\u5c0f\u55f5 v1.0.2", "body": BODY_V102},
    {"tag": "v1.0.3", "name": "\u84dd\u8272\u5c0f\u55f5 v1.0.3", "body": BODY_V103},
]


def api_request(url, method="GET", data=None):
    """发送 GitHub API 请求。"""
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, method=method)
    for k, v in HEADERS.items():
        req.add_header(k, v)
    if body:
        req.add_header("Content-Type", "application/json; charset=utf-8")
    try:
        with urllib.request.urlopen(req) as resp:
            if resp.status == 204:
                return None
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        print(f"  API 错误 {e.code}: {error_body}")
        raise


def main():
    for rel in RELEASES:
        tag = rel["tag"]
        print(f"\n{'='*10} 处理 {tag} {'='*10}")

        # 获取现有 release
        try:
            existing = api_request(f"{API}/releases/tags/{tag}")
            release_id = existing["id"]
            author = existing["author"]["login"]
            print(f"  找到现有 release: id={release_id}, author={author}")

            if author == "weidaozhong":
                print(f"  {tag} 的作者已经是 weidaozhong，跳过")
                continue

            assets = [a["name"] for a in existing.get("assets", [])]
            if assets:
                print(f"  现有 assets: {', '.join(assets)}")
                print("  ⚠ 删除 release 后 assets 也会被删除，需要重新上传！")

            # 删除旧 release
            print(f"  删除旧 release (id={release_id})...")
            api_request(f"{API}/releases/{release_id}", method="DELETE")
            print("  已删除旧 release")

        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"  未找到 {tag} 的 release，将直接创建")
            else:
                raise

        # 创建新 release
        print("  以 weidaozhong 身份创建新 release...")
        new_release = api_request(f"{API}/releases", method="POST", data={
            "tag_name": tag,
            "name": rel["name"],
            "body": rel["body"],
            "draft": False,
            "prerelease": False,
        })
        print(f"  新 release 已创建: id={new_release['id']}, author={new_release['author']['login']}")
        print(f"  链接: {new_release['html_url']}")

    print(f"\n{'='*10} 完成 {'='*10}")
    print("所有 release 已重建为 weidaozhong 身份。")
    print("请到 GitHub Release 页面为每个版本重新上传 .exe 文件。")


if __name__ == "__main__":
    main()
