#!/usr/bin/env bash
# =============================================================================
#  OrangeFox 中文化补丁应用脚本
#  作用：把本仓库 source/twres/ 下的 7 个改过文件，注入编译出的 ramdisk，
#        让成品变成「默认中文 + 文泉驿字体 + 折叠菜单 + KSU 入口」的中文版。
#
#  用法（在编译产物目录执行）：
#     bash patches/apply-zh.sh <recovery.img>
#
#  依赖：python3（解包/打包 cpio + LZ4 + AVB 重算）
# =============================================================================
set -euo pipefail

IMG="${1:-out/target/product/sm87xx/recovery.img}"
[ -f "$IMG" ] || { echo "找不到镜像: $IMG" >&2; exit 1; }

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../source" && pwd)"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> 补丁源文件目录: $SRC_DIR"
echo "==> 目标镜像: $IMG"

python3 "$HERE/apply-zh.py" "$IMG" "$SRC_DIR"
echo "==> 完成，中文版已写出"
