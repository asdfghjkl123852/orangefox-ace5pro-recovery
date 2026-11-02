# 源文件说明

这里是从 OrangeFox R12（一加 Ace 5 Pro / PKR110）中提取并修改过的**主题源文件**，可直接替换回自己的 ramdisk 复现本改版。

对应镜像内路径为 `source/twres/...` → `/twres/...`。

## 改动清单

| 文件 | 改了什么 |
|---|---|
| `twres/languages/en.xml` | 中文语言包（`zh_CN.xml` 的 1107 条）整份写入默认语言槽，补了 2 个缺失键。**改完要同步更新 `ramdisk-files.sha256sum` 里该文件的摘要**，否则 OrangeFox 自检报错 |
| `twres/themes/font.xml` | 26 处 `filename="*.ttf"` 全部换成 `wqy-microhei.ttf`。主题字体在语言包的 `fontoverride` 之后加载，不换这里中文会显示成方块 |
| `twres/resources/images.xml` | 字体预览项 `font1`~`font7` 同步换成 `wqy-microhei.ttf` |
| `twres/splash.xml` | 首屏 "Recovery" 下方加一行「由 Sakura 编译」，34 号字 `#9aa0a6` |
| `twres/resources/vars.xml` | 新增变量：`lang_back`（语言页返回目标，默认 `ext_time`）、`adv_open`（附加功能折叠状态，默认 `1`） |
| `twres/pages/settings.xml` | 语言页 `ext_time_lang` 的返回从写死 `ext_time` 改为 `%lang_back%`；「关于」页版本行追加署名 |
| `twres/pages/advanced.xml` | ① 「更多」菜单加「语言 / Language」「WiFi 网络 / WiFi」「截屏 / Screenshot」三项；② 附加功能整组改为可折叠（`adv_open` 控制，折叠头 `[ + ] 展开` / `[ - ] 收起`）；③ 新增 `wifi_menu` 页面（状态说明 + 跳到终端）；④ 修复安装确认页返回：入口页必须设 `install_back=advanced` |

## 关键坑（改主题前先看）

1. **`install_back` 必须由调用方设置**
   `fox_modules_confirm` 页面的返回是 `<action function="page">%install_back%</action>`，变量为空会跳到不存在的页面 → 表现为「返回没反应」。任何跳这个页面的自定义入口都要先 `set install_back=<目标页>`。

2. **`<background>` 只认 `color`**
   给它加 `resource="xxx"` 会让整份主题加载失败，开机停在非主界面、点什么都没反应。要图片背景请用独立的 `<image>` 对象。

3. **主题动作里不要调 `fox` / `twrp` CLI**
   `<action function="ftls">fox wlan info</action>` 会递归回 GUI，日志报
   `E:Another threaded action is already running` 并卡死界面。安全做法：只做纯 shell，或只做页面跳转。

4. **`<condition>` 里的 `&` 要写成 `&amp;`**
   否则 XML 解析失败、主题不加载（我就因为这个让恢复重启后无界面）。

## 复现步骤

```sh
# 1. 解出官方 ramdisk（Android boot image v4，LZ4 legacy 帧，偏移 4096）
# 2. cpio 解包
# 3. 用本目录 twres/ 覆盖解包后的同名文件
# 4. 同步 ramdisk-files.sha256sum 中 en.xml 的 sha256
# 5. cpio 重新打包（保持 512 对齐）
# 6. LZ4 HC level 12 重新压缩（8MB 一块，legacy 帧）
# 7. 重算 AVB：sha256(salt + 镜像前 original_image_size 字节) 写回 hash descriptor，
#    vbmeta 移到新位置（4096 对齐），更新尾部 AVBf footer 指针
```

第 7 步是能不能启动的关键：官方镜像尾部的 AVB 结构不能补零，`algorithm_type = 0`（无签名），所以 digest 可以自己算，不需要密钥。

## 备份

改之前先备份分区：

```sh
adb shell su -c "dd if=/dev/block/by-name/recovery_a bs=1M" > recovery_a_stock.img
```
