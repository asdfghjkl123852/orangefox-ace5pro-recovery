#!/usr/bin/env bash
# =============================================================================
#  一加 Ace 5 Pro（OPLUS sm87xx）橙狐 Recovery 一键编译脚本
#
#  用法：
#     在源码树根目录执行  bash build.sh
#     低内存机器（8GB）执行  LOW_MEMORY=1 bash build.sh
#
#  产物：
#     out/target/product/sm87xx/recovery.img
#     out/target/product/sm87xx/OrangeFox-R12.0-Unofficial-sm87xx.img
#     out/target/product/sm87xx/OrangeFox-R12.0-Unofficial-sm87xx.zip
#
#  产物支持 data 分区解密（KeyMint/QTI + NXP Strongbox + weaver + SSG）。
# =============================================================================
set -euo pipefail

DEVICE="sm87xx"
MANIFEST_URL="https://gitlab.com/OrangeFox/Manifest.git"
MANIFEST_BRANCH="fox_16.0"
NJOBS="${JOBS:-$(nproc)}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log() { echo -e "\033[1;32m==>\033[0m $*"; }
warn() { echo -e "\033[1;33m[!]\033[0m $*"; }

# 低内存模式：给 soong 注入 Go 内存上限，防止 8GB 内存机器在分析阶段被 OOM 杀掉。
# soong_build 会在 bootstrap 后生成，这里把它包装一层注入 GOMEMLIMIT。
ensure_soong_wrapper() {
  local sb="out/host/linux-x86/bin/soong_build"
  if [ -f "$sb" ] && head -c 20 "$sb" 2>/dev/null | grep -q 'ELF'; then
    mv -f "$sb" "$sb.real"
    cat > "$sb" <<'WRAPPER'
#!/bin/bash
export GOMEMLIMIT=4GiB
export GOGC=20
exec "$(dirname "$0")/soong_build.real" "$@"
WRAPPER
    chmod +x "$sb"
    log "已注入 soong 内存优化 wrapper（GOMEMLIMIT=4GiB）"
  fi
}

# ---------- 1. 初始化橙狐 manifest ----------
if [ ! -d .repo ]; then
  log "[1/6] 初始化橙狐 manifest（${MANIFEST_BRANCH}）"
  repo init -u "$MANIFEST_URL" -b "$MANIFEST_BRANCH"
else
  log "[1/6] 已存在 .repo，跳过 init"
fi

# ---------- 2. 写入设备树 local_manifest ----------
log "[2/6] 写入设备树 local_manifest"
mkdir -p .repo/local_manifests
cp "$SCRIPT_DIR/local_manifests/ace5pro.xml" .repo/local_manifests/

# ---------- 3. 同步源码 ----------
log "[3/6] 同步源码（首次同步体积较大，请耐心等待）"
repo sync -j"$NJOBS" --force-sync

# ---------- 4. 校验设备树 ----------
if [ ! -f "device/oplus/sm87xx/BoardConfig.mk" ]; then
  warn "设备树未同步成功，请检查网络后重试：repo sync"
  exit 1
fi

# ---------- 5. 配置编译环境 ----------
log "[4/6] 配置编译环境"
export FOX_BUILD_DEVICE="$DEVICE"
export ALLOW_MISSING_DEPENDENCIES=true
export LC_ALL=C
source build/envsetup.sh

# ---------- 6. 内存优化（复跑时生效） ----------
if [ "${LOW_MEMORY:-0}" = "1" ]; then
  ensure_soong_wrapper
fi

lunch "twrp_${DEVICE}-eng"

# ---------- 7. 编译 ----------
log "[6/6] 开始编译 recoveryimage（jobs=${NJOBS}）"
mka recoveryimage -j"$NJOBS"

log "编译完成，产物如下："
ls -lh "out/target/product/${DEVICE}/recovery.img" \
       "out/target/product/${DEVICE}/"OrangeFox*.img \
       "out/target/product/${DEVICE}/"OrangeFox*.zip 2>/dev/null || true
