# 中文化补丁

把编译出的 recovery 自动变成「默认中文版」的一键补丁。

## 文件

| 文件 | 作用 |
|---|---|
| `apply-zh.py` | 核心：解包 cpio → 注入 7 个主题文件 → 重算 sha256sum → LZ4 HC12 重压 → 重算 AVB digest |
| `apply-zh.sh` | 外壳脚本，包装上面那个，方便命令行调用 |

## 用法

```bash
# 方式一：直接用 python
pip install lz4
python3 patches/apply-zh.py <编译出的 recovery.img> <仓库 source 目录> [输出.img]

# 方式二：用外壳脚本
bash patches/apply-zh.sh out/target/product/sm87xx/recovery.img
```

输出默认写到 `<输入>.zh.img`，或指定的输出路径。

## 它做了什么

1. 按 Android boot image v4 解析输入镜像，解出 LZ4 legacy 帧里的 cpio(newc)
2. 把 `source/twres/` 下 7 个文件注入对应路径：
   - `languages/en.xml`（中文语言包）
   - `themes/font.xml`、`resources/images.xml`（字体换微米黑）
   - `resources/vars.xml`（`lang_back` / `adv_open`）
   - `pages/advanced.xml`（菜单入口 / 折叠 / WiFi 页 / install_back）
   - `pages/settings.xml`（语言页返回变量化、署名）
   - `splash.xml`（首屏署名）
3. 同步 `ramdisk-files.sha256sum` 里 `en.xml` 的摘要
4. cpio 重打包（512 对齐）→ LZ4 HC level 12 重压（8MB 一块）
5. 重算 AVB：定位 vbmeta 里的 recovery hash descriptor，重算
   `sha256(salt + 镜像前 vbmeta 偏移字节)`，更新 image_size / digest / footer 指针

## 为什么需要第 5 步

官方镜像尾部有 AVB 校验结构，`algorithm_type = 0`（无签名），所以 digest 可以自己算、不需要密钥。**但如果不重算，bootloader 校验 recovery 分区失败会直接跳 fastboot**。这是能不能启动的关键。

## 已验证

- 用原始英文镜像 → 输出中文版，AVB digest 验算通过、中文/折叠/KSU 内容齐全
- 用成品镜像 → 输出内容等价，AVB digest 验算通过

## 依赖

- Python 3.8+
- `lz4`（`pip install lz4`）
