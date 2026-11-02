# OrangeFox Recovery — OnePlus Ace 5 Pro (sm87xx)

[中文说明](README.md) | English

An **OrangeFox R12.0 (Android 16 / fox_16.0)** recovery with **data decryption support** for OPLUS sm87xx devices.

- Device tree: [kmiit/twrp_device_oplus_sm87xx](https://github.com/kmiit/twrp_device_oplus_sm87xx) (branch `twrp-16.0`)
- Build system: [OrangeFox/Manifest](https://gitlab.com/OrangeFox/Manifest) (branch `fox_16.0`)
- Devices: OPLUS sm87xx platform (**OnePlus Ace 5 Pro** / OnePlus 13 / 13T / Ace 6 / Turbo 6 / Realme GT7 Pro, etc.)

> This repo only provides the *build entry point* (manifest + one-click script). Full source is fetched from OrangeFox / AOSP via `repo sync`.

---

## Supported devices

| Brand   | Devices |
|---------|---------|
| OnePlus | Ace 5 Pro, 13, 13T, 13s, Ace 6, Turbo 6, Pad 2 Pro |
| Realme  | GT7 Pro, GT7 Pro Speed, GT8 |

## Features

- ✅ **Data decryption** (full decryption stack, see below)
- ✅ ADB / Fastbootd / MTP / Sideload / USB OTG
- ✅ Touch / Display / Vibrator
- ✅ Full partition tools, 7z, repacktools, resetprop
- ✅ F2FS / ext4 / exFAT / NTFS filesystems

---

## Requirements

| Item   | Requirement |
|--------|-------------|
| OS     | Linux (Ubuntu 22.04 / Debian 12 recommended) |
| RAM    | >= 8GB (16GB recommended) |
| Disk   | >= 200GB free |
| Tools  | git, repo, python3, rsync |

Install dependencies (Ubuntu / Debian):

```bash
sudo apt-get update
sudo apt-get install -y git repo python3 rsync zip unzip \
    build-essential bc bison flex libssl-dev curl \
    libncurses-dev libxml2-utils
```

---

## Quick start (one-click build)

```bash
# 1. Clone this repo
git clone https://github.com/asdfghjkl123852/orangefox-ace5pro-recovery.git
cd orangefox-ace5pro-recovery

# 2. Run the build script (first run syncs all source, ~1-2 hours)
bash build.sh
```

Low-memory machines (8GB) should enable the low-memory mode to avoid soong OOM:

```bash
LOW_MEMORY=1 bash build.sh
```

> Note: run `build.sh` inside an **empty source directory** (the script runs `repo init` there). Output paths are printed when the build finishes.

---

## Manual build (step by step)

```bash
# 1. Init the OrangeFox manifest
mkdir orangefox && cd orangefox
repo init -u https://gitlab.com/OrangeFox/Manifest.git -b fox_16.0

# 2. Add the device-tree local manifest (local_manifests/ace5pro.xml from this repo)
mkdir -p .repo/local_manifests
cp /path/to/ace5pro.xml .repo/local_manifests/

# 3. Sync source
repo sync -j$(nproc) --force-sync

# 4. Build
export FOX_BUILD_DEVICE=sm87xx
export ALLOW_MISSING_DEPENDENCIES=true
export LC_ALL=C
source build/envsetup.sh
lunch twrp_sm87xx-eng
mka recoveryimage -j$(nproc)
```

Output:

```
out/target/product/sm87xx/recovery.img
out/target/product/sm87xx/OrangeFox-R12.0-Unofficial-sm87xx.img
out/target/product/sm87xx/OrangeFox-R12.0-Unofficial-sm87xx.zip
```

---

## Automated build (GitHub Actions)

Two workflows are provided:

| Workflow | Runner | Purpose |
|----------|--------|---------|
| `.github/workflows/ci-checks.yml` | free `ubuntu-latest` | Validates script/XML/file integrity on every push |
| `.github/workflows/build-recovery.yml` | **self-hosted** | Full recovery build (manual trigger) |

**Why self-hosted?** A trimmed Android source tree still needs ~81GB disk, while the free GitHub runner only has 14GB disk / 7GB RAM — far too small to build a recovery.

### Set up a self-hosted runner

On your build machine (>=200GB disk, >=16GB RAM):

```bash
# 1. In the GitHub repo: Settings -> Actions -> Runners -> New self-hosted runner
#    Follow the instructions shown there, e.g.:
mkdir actions-runner && cd actions-runner
curl -o actions-runner-linux-x64.tar.gz -L https://github.com/actions/runner/releases/download/v2.XXX/actions-runner-linux-x64-2.XXX.tar.gz
tar xzf actions-runner-linux-x64.tar.gz
./config.sh --url https://github.com/asdfghjkl123852/orangefox-ace5pro-recovery --token <TOKEN>
./run.sh
```

Then in the repo's **Actions** tab, run the **"Build Recovery (self-hosted)"** workflow manually. It will sync the source (once, then reused) and produce the recovery, downloadable as a build artifact.

---

## Decryption stack

This recovery includes the full data-decryption stack for OPLUS sm87xx stock firmware:

| Component  | Detail |
|------------|--------|
| **KeyMint (QTI)** | `android.hardware.security.keymint-service-qti` + `libqtikeymint.so` |
| **Strongbox (NXP)** | `keymint-service.strongbox-nxp` + eSE libs |
| **weaver** | `vendor.oplus.hardware.weaver` AIDL service (eSE-backed key gating) |
| **SSG** | `ssgtzd` daemon + `vendor/etc/ssg` config |
| **keystore2** | V3/V4/V5, with AAID / crypto / gatekeeper |

> The decryption capability comes entirely from the device tree's bundled `prebuilt/` and `recovery/root/`; no extra config needed.

---

## Flashing

```bash
# fastboot (recommended)
fastboot flash recovery OrangeFox-R12.0-Unofficial-sm87xx.img

# A/B devices (recovery in _a/_b)
fastboot flash recovery_a OrangeFox-R12.0-Unofficial-sm87xx.img
fastboot flash recovery_b OrangeFox-R12.0-Unofficial-sm87xx.img
```

Or flash the `OrangeFox-R12.0-Unofficial-sm87xx.zip` from an existing recovery.

---

## FAQ

**1. soong gets killed (log shows `Killed`)**
Not enough RAM. Use `LOW_MEMORY=1 bash build.sh` (injects `GOMEMLIMIT=4GiB` into soong), or `JOBS=4 bash build.sh`.

**2. `repo sync` is slow / fails**
For slow GitHub access from China, switch the fetch URL in `local_manifests/ace5pro.xml`:
```xml
<remote name="kmiit" fetch="https://ghfast.top/https://github.com/kmiit" />
```

**3. `lunch twrp_sm87xx-eng` can't find the product**
Make sure the device tree is synced to `device/oplus/sm87xx` (BoardConfig.mk exists), then re-run `source build/envsetup.sh`.

**4. Can't decrypt data on first boot**
Check the "Mount" screen; on some firmware versions a weaver/KeyMint handshake glitch can be fixed by removing the lockscreen password once and rebooting.

---

## License

- This repo (manifest + scripts): Apache-2.0
- Device tree: Apache-2.0 ([kmiit/twrp_device_oplus_sm87xx](https://github.com/kmiit/twrp_device_oplus_sm87xx))
- OrangeFox / TWRP source: their respective upstream licenses (GPL-3.0, etc.)
