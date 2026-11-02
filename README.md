# OrangeFox Ace 5 Pro 中文版

一加 Ace 5 Pro（PKR110 / OP60EBL1，Android 17）的 OrangeFox Recovery R12 中文化改版。

> 由 **Sakura** 编译 · 非官方构建 · 刷机有风险

---

## 特性

| 项目 | 说明 |
|---|---|
| **全中文界面** | 中文语言包注入默认语言槽 `en.xml`，开箱即中文，不需进设置手选 |
| **字体修正** | 主题 `themes/font.xml` 等 26 处字体引用换成 `wqy-microhei.ttf`，中文不再显示方块 |
| **附加功能折叠** | 「更多」页里的附加功能整组可展开/收起（`adv_open` 变量控制） |
| **语言入口** | 「更多 → 语言 / Language」，返回走 `lang_back`，不会卡住 |
| **截屏入口** | 「更多 → 截屏 / Screenshot」 |
| **KernelSU / SukiSU 入口** | 「更多 → 安装 KernelSU / 安装 SukiSU Ultra」，走内置 zip 安装流程 |
| **修复启动校验** | 重算 AVB `hash` descriptor 的 digest 并更新 footer，改完主题仍能正常启动 |

## 下载

- **仓库内**：`OrangeFox-Ace5Pro-中文版.img.xz`（33.9 MB），解压后即为完整镜像
- **Releases**：完整未压缩镜像（100 MB），可直接刷入

解压：

```sh
# Linux / macOS
xz -d OrangeFox-Ace5Pro-中文版.img.xz

# Windows（资源管理器右键「全部解压」需装 7-Zip；或用命令行）
7z x OrangeFox-Ace5Pro-中文版.img.xz
```

## 刷入

设备为 A/B + 虚拟 A/B，`recovery_a` / `recovery_b` 各 100 MB，镜像为纯 ramdisk（`kernel_size = 0`，内核在 `boot` 分区），**不需要内核**。

### 方式一：fastboot（推荐）

```sh
fastboot flash recovery_a OrangeFox-Ace5Pro-中文版.img
fastboot flash recovery_b OrangeFox-Ace5Pro-中文版.img
fastboot reboot recovery
```

### 方式二：已有 root 的 recovery / 系统内

```sh
adb push OrangeFox-Ace5Pro-中文版.img /data/local/tmp/ofox.img
adb shell su -c "dd if=/data/local/tmp/ofox.img of=/dev/block/by-name/recovery_a bs=1M; sync"
adb shell su -c "dd if=/data/local/tmp/ofox.img of=/dev/block/by-name/recovery_b bs=1M; sync"
```

刷完读回校验头部：

```sh
adb exec-out "dd if=/dev/block/by-name/recovery_a bs=4096 count=1" | hexdump -C | head -4
```

应能看到 `ANDROID!`，且 `0x0C` 处的 ramdisk 长度与镜像一致。

## 回退

刷之前先备份原分区，出问题能立刻恢复：

```sh
adb shell su -c "dd if=/dev/block/by-name/recovery_a bs=1M" > recovery_a_stock.img
```

恢复：

```sh
fastboot flash recovery_a recovery_a_stock.img
```

## 校验

```
文件大小  104857600 字节
sha256    bed4c709b0942a4665bcf9e5c7cadca7c319fb0645102d4c1b459ed0fafb42a6
```

## 已知限制

- **不支持 WiFi**：本构建未编译 `TW_INCLUDE_WIFI`，`fox wlan` 返回 `WLAN support is not available in this recovery build.`，恢复内也没有 `wpa_supplicant`。要在恢复里联网必须重新编译。
- **没有「音量下 + 电源」截屏组合键**：原生未实现，主题层也接收不到音量键事件。截屏请用「更多 → 截屏」。
- **KSU / SukiSU 入口是引导脚本**：内置的 zip 只做环境检测、读取 KMI、备份 boot 并给出官方流程提示，不会直接替换 root。真装请用官方 zip。
- 截屏保存位置依赖内部存储挂载状态。

## 免责声明

- 本项目仅对**一加 Ace 5 Pro（PKR110）**验证，其他机型刷入后果自负。
- 修改 recovery 分区不影响系统启动，但操作失误仍可能造成数据丢失。
- 请自行承担刷机风险，务必先备份。

## 致谢

- [OrangeFox Recovery Project](https://orangefox.download/)
- 文泉驿微米黑字体
- KernelSU / SukiSU 团队
