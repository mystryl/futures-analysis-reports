#!/usr/bin/env python3
"""
批量回测并部署到 Vercel

功能：
1. 运行批量回测（batch_backtest.py）
2. 将报告复制到 public/ 目录
3. 提交到 GitHub
4. 触发 Vercel 自动部署
"""

import os
import sys
import subprocess
import shutil
from datetime import datetime
from pathlib import Path

# 配置
REPO_ROOT = Path(__file__).parent
OUTPUT_DIR = REPO_ROOT / "output"
PUBLIC_DIR = REPO_ROOT / "public"
KLINECHARTS_SRC = REPO_ROOT / "static" / "lib" / "klinecharts.min.js"
KLINECHARTS_PRO_CSS = REPO_ROOT / "static" / "lib" / "klinecharts-pro.css"
KLINECHARTS_PRO_JS = REPO_ROOT / "static" / "lib" / "klinecharts-pro.umd.js"


def log_info(msg):
    """输出信息"""
    print(f"[INFO] {msg}")


def log_error(msg):
    """输出错误"""
    print(f"[ERROR] {msg}")


def run_batch_analyze():
    """运行批量回测"""
    log_info("=" * 60)
    log_info("开始批量回测分析")
    log_info("=" * 60)

    # 导入 batch_backtest
    sys.path.insert(0, str(REPO_ROOT))
    import batch_backtest

    # 运行批量分析
    batch_backtest.batch_analyze()

    log_info("批量回测完成")


def prepare_public_dir():
    """准备 public 目录"""
    log_info("准备 public/ 目录...")

    # 创建 public 目录
    PUBLIC_DIR.mkdir(exist_ok=True)

    # 清理旧文件（保留 .gitkeep）
    for item in PUBLIC_DIR.glob("*"):
        if item.name != ".gitkeep":
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)

    # 复制 output 目录内容到 public
    if OUTPUT_DIR.exists():
        shutil.copytree(OUTPUT_DIR, PUBLIC_DIR, dirs_exist_ok=True)

    # 复制 klinecharts 相关文件
    files_to_copy = [
        (KLINECHARTS_SRC, "klinecharts.min.js"),
        (KLINECHARTS_PRO_CSS, "klinecharts-pro.css"),
        (KLINECHARTS_PRO_JS, "klinecharts-pro.umd.js")
    ]

    for src, target_name in files_to_copy:
        if src.exists():
            target_path = PUBLIC_DIR / target_name
            shutil.copy2(src, target_path)
            log_info(f"已复制 {target_name}")

    # 更新 HTML 中的路径引用
    update_html_references()

    log_info(f"public/ 目录已准备完成")


def update_html_references():
    """更新 HTML 文件中的资源引用路径"""
    for html_file in PUBLIC_DIR.glob("*.html"):
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # 将 ../klinecharts.min.js 替换为 ./klinecharts.min.js
        content = content.replace('src="../klinecharts.min.js"', 'src="./klinecharts.min.js"')

        # 处理 klinecharts-pro 的路径
        content = content.replace('href="../klinecharts-pro.css"', 'href="./klinecharts-pro.css"')
        content = content.replace('src="../klinecharts-pro.umd.js"', 'src="./klinecharts-pro.umd.js"')

        if content != original_content:
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(content)


def git_commit_and_push():
    """提交到 GitHub 并推送"""
    log_info("提交到 GitHub...")

    try:
        os.chdir(REPO_ROOT)

        # 检查 git 状态
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True,
            check=True
        )

        if not result.stdout.strip():
            log_info("没有更改需要提交")
            return True

        # 添加 public 目录
        subprocess.run(
            ['git', 'add', 'public/'],
            check=True,
            capture_output=True
        )

        # 生成提交信息
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        commit_msg = f'deploy: 更新批量回测报告\n\n更新时间: {timestamp}'

        # 提交
        subprocess.run(
            ['git', 'commit', '-m', commit_msg],
            check=True,
            capture_output=True
        )

        # 推送
        subprocess.run(
            ['git', 'push'],
            check=True,
            capture_output=True
        )

        log_info("已成功推送到 GitHub")
        return True

    except subprocess.CalledProcessError as e:
        log_error(f"Git 操作失败: {e}")
        return False


def main():
    """主函数"""
    log_info("=" * 60)
    log_info("期货分析批量部署工具")
    log_info("=" * 60)

    # 1. 运行批量回测
    run_batch_analyze()

    # 2. 准备 public 目录
    prepare_public_dir()

    # 3. 提交并推送
    success = git_commit_and_push()

    if success:
        log_info("=" * 60)
        log_info("部署流程完成！")
        log_info("Vercel 将自动开始部署（约 30 秒）")
        log_info("=" * 60)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
