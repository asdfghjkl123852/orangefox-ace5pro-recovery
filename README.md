# OrangeFox Recovery — 一加 Ace 5 Pro（sm87xx）

中文 | [English](README_EN.md)

基于**橙狐 OrangeFox R12.0（Android 16 / fox_16.0）**构建的 recovery，**支持解密 data 分区**。

- 设备树：[kmiit/twrp_device_oplus_sm87xx](https://github.com/kmiit/twrp_device_oplus_sm87xx)（分支 `twrp-16.0`）
- 构建系统：[OrangeFox/Manifest](https://gitlab.com/OrangeFox/Manifest)（分支 `fox_16.0`）
- 适用机型：OPLUS sm87xx 平台全系（**一加 Ace 5 Pro** / OnePlus 13 / OnePlus 13T / Ace 6 / Turbo 6 / Realme GT7 Pro 等）

> 本项目只提供「编译入口」（manifest + 一键脚本）。完整源码通过 `repo sync` 从橙狐与 AOSP 官方仓库拉取。

---

## 支持的机型

| 品牌 | 机型 |
|------|------|
| OnePlus | Ace 5 Pro、13、13T、13s、Ace 6、Turbo 6、Pad 2 Pro |
| Realme | GT7 Pro、GT7 Pro Speed、GT8 |

## 已实现功能

- ✅ **data 分区解密**（完整解密栈，见下文）
- ✅ ADB / Fastbootd / MTP / Sideload / USB OTG
- ✅ 触摸 / 显示 / 震动
- ✅ 全分区工具、7z、repacktools、resetprop
- ✅ F2FS / ext4 / exFAT / NTFS 文件系统

---

## 环境要求

| 项目 | 要求 |
|------|------|
| 系统 | Linux（推荐 Ubuntu 22.04 / Debian 12） |
| 内存 | ≥ 8GB（16GB 更佳） |
| 磁盘 | ≥ 300GB 可用空间 |
| 工具 | git、repo、python3、rsync |

安装依赖（Ubuntu / Debian）：

```bash
sudo apt-get update
sudo apt-get install -y git repo python3 rsync zip unzip \
    build-essential bc bison flex libssl-dev curl \
    libncurses-dev libxml2-utils
```

---

## 快速开始（一键编译）

```bash
# 1. 克隆本项目
git clone https://github.com/asdfghjkl123852/orangefox-ace5pro-recovery.git
cd orangefox-ace5pro-recovery

# 2. 执行编译脚本（首次会同步全部源码，约 1~2 小时）
bash build.sh
```

低内存机器（8GB）建议开启低内存模式，防止 soong 分析阶段 OOM：

```bash
LOW_MEMORY=1 bash build.sh
```

> 注意：`build.sh` 必须在**空的源码目录**里运行（脚本会在此目录 `repo init`）。产物生成后会自动列出路径。

---

## 手动编译（分步）

如果你更想手动控制每一步：

```bash
# 1. 建目录并初始化橙狐 manifest
mkdir orangefox && cd orangefox
repo init -u https://gitlab.com/OrangeFox/Manifest.git -b fox_16.0

# 2. 加入设备树 local_manifest（本仓库的 local_manifests/ace5pro.xml）
mkdir -p .repo/local_manifests
cp /path/to/ace5pro.xml .repo/local_manifests/

# 3. 同步源码
repo sync -j$(nproc) --force-sync

# 4. 配置环境并编译
export FOX_BUILD_DEVICE=sm87xx
export ALLOW_MISSING_DEPENDENCIES=true
export LC_ALL=C
source build/envsetup.sh
lunch twrp_sm87xx-eng
mka recoveryimage -j$(nproc)
```

编译成功后，产物位于：

```
out/target/product/sm87xx/recovery.img
out/target/product/sm87xx/OrangeFox-R12.0-Unofficial-sm87xx.img
out/target/product/sm87xx/OrangeFox-R12.0-Unofficial-sm87xx.zip
```

---

## 自动编译（GitHub Actions）

本仓库提供了两个 workflow：

| workflow | 运行环境 | 用途 |
|----------|----------|------|
| `.github/workflows/ci-checks.yml` | 免费 `ubuntu-latest` | 每次 push 校验脚本/XML/文件完整性 |
| `.github/workflows/build-recovery.yml` | **自托管 runner** | 手动触发，完整编译出 rec |

**为什么需要自托管？** 精简后的 Android 源码树也要约 81GB 磁盘，而 GitHub 免费 runner 只有 14GB 磁盘 / 7GB 内存，完全不够编译 recovery。

### 部署自托管 runner

在编译机（≥200GB 磁盘、≥16GB 内存）上：

```bash
# 1. 仓库 Settings -> Actions -> Runners -> New self-hosted runner，按页面提示操作，例如：
mkdir actions-runner && cd actions-runner
curl -o actions-runner-linux-x64.tar.gz -L https://github.com/actions/runner/releases/download/v2.XXX/actions-runner-linux-x64-2.XXX.tar.gz
tar xzf actions-runner-linux-x64.tar.gz
./config.sh --url https://github.com/asdfghjkl123852/orangefox-ace5pro-recovery --token <TOKEN>
./run.sh
```

然后在仓库 **Actions** 页手动运行 **"Build Recovery (self-hosted)"**。它会自动 sync 源码（首次后复用）并编译，产物作为 artifact 下载。

---

## 解密能力说明

该 recovery 内置了 OPLUS sm87xx 平台完整的 data 解密栈，能解密出厂固件的用户数据：

| 组件 | 说明 |
|------|------|
| **KeyMint（QTI）** | `android.hardware.security.keymint-service-qti` + `libqtikeymint.so` |
| **Strongbox（NXP）** | `keymint-service.strongbox-nxp` + eSE 相关库 |
| **weaver** | `vendor.oplus.hardware.weaver` AIDL 服务，配合 eSE 做密钥门控 |
| **SSG** | `ssgtzd` 守护进程 + `vendor/etc/ssg` 配置 |
| **keystore2** | V3/V4/V5 全套，含 AAID / crypto / gatekeeper |

> 解密能力完全来自 kmiit 设备树自带的 `prebuilt/` 与 `recovery/root/`，无需额外配置。

---

## 刷入方式

编译出的 `OrangeFox-R12.0-Unofficial-sm87xx.img` 可直接刷入：

```bash
# fastboot 方式（推荐）
fastboot flash recovery OrangeFox-R12.0-Unofficial-sm87xx.img

# A/B 分区机型（recovery 在 _a/_b）
fastboot flash recovery_a OrangeFox-R12.0-Unofficial-sm87xx.img
fastboot flash recovery_b OrangeFox-R12.0-Unofficial-sm87xx.img
```

或使用 `OrangeFox-R12.0-Unofficial-sm87xx.zip` 卡刷包，在已有 recovery 中刷入。

---

## 常见问题

### 1. soong 分析阶段被 OOM 杀掉（日志出现 `Killed`）
内存不足导致。解决办法：
- 使用 `LOW_MEMORY=1 bash build.sh`（脚本会自动给 soong 注入 `GOMEMLIMIT=4GiB`）；
- 或减少并行数：`JOBS=4 bash build.sh`。

### 2. `repo sync` 很慢 / 下载失败
- 国内访问 GitHub 慢时，可把 `local_manifests/ace5pro.xml` 里的 fetch 改为镜像加速：
  ```xml
  <remote name="kmiit" fetch="https://ghfast.top/https://github.com/kmiit" />
  ```
- AOSP 源码默认走清华镜像（橙狐 manifest 已内置），无需额外配置。

### 3. `lunch twrp_sm87xx-eng` 报找不到产品
确认设备树已同步到 `device/oplus/sm87xx`，且 `BoardConfig.mk` 存在。然后重新 `source build/envsetup.sh`。

### 4. 首次进入 recovery 无法解密 data
- 在「挂载」界面确认 data 分区能否解密挂载；
- 若个别固件版本导致 weaver/KeyMint 握手异常，可尝试清除一次锁屏密码后重进。

---

## 许可证

- 本项目（manifest + 脚本）：Apache-2.0
- 设备树：Apache-2.0（[kmiit/twrp_device_oplus_sm87xx](https://github.com/kmiit/twrp_device_oplus_sm87xx)）
- OrangeFox / TWRP 源码：各自遵循其上游许可证（GPL-3.0 等）
