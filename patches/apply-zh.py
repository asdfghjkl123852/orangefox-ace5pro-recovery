#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OrangeFox 中文化补丁核心脚本。

把 source/twres/ 下的 7 个改过文件，注入一个已编译好的 recovery.img，
并正确处理三件容易翻车的事：

  1. cpio(newc) 解包/重打包，保持 512 字节对齐
  2. 同步 ramdisk-files.sha256sum 里被改文件的摘要
  3. LZ4 legacy 帧重压（HC level 12，8MB 一块，与官方参数一致）
  4. 重算 AVB hash descriptor 的 digest（algorithm_type=0 无签名，可自行重算）

用法：
    python3 apply-zh.py <recovery.img> <source_twres_dir> [输出.img]

输出默认写到 <recovery.img>.zh.img
"""
import os
import re
import sys
import struct
import hashlib
import lz4.block


MAGIC_LZ4 = 0x184C2102
BLOCK = 8 * 1024 * 1024
PAGE = 4096


def log(*a):
    print(*a, file=sys.stderr)


def walk_cpio(buf):
    """解析 cpio newc，返回 [(name, header_fields, data_start, size, entry_start, entry_end)]"""
    out = []
    off = 0
    n = len(buf)
    while off + 110 <= n:
        if buf[off:off + 6] != b"070701":
            nxt = buf.find(b"070701", off + 1)
            if nxt < 0:
                break
            off = nxt
            continue
        f = [int(buf[off + 6 + i * 8: off + 14 + i * 8], 16) for i in range(13)]
        ns, sz = f[11], f[6]
        name = buf[off + 110: off + 110 + ns - 1].decode("utf-8", "replace")
        pad = (4 - ((110 + ns) % 4)) % 4
        data_start = off + 110 + ns + pad
        entry_end = data_start + ((sz + 3) // 4) * 4
        out.append((name, f, data_start, sz, off, entry_end))
        off = entry_end
        if name == "TRAILER!!!":
            break
    return out


def emit_entry(name, fields, data):
    nb = name.encode("utf-8") + b"\x00"
    f = list(fields)
    f[6] = len(data)
    hdr = b"070701" + b"".join(b"%08x" % x for x in f)
    assert len(hdr) == 110
    pad1 = b"\x00" * ((4 - ((110 + len(nb)) % 4)) % 4)
    pad2 = b"\x00" * ((4 - (len(data) % 4)) % 4)
    return hdr + nb + pad1 + data + pad2


def lz4_legacy_compress(data):
    buf = [struct.pack("<I", MAGIC_LZ4)]
    for i in range(0, len(data), BLOCK):
        chunk = data[i:i + BLOCK]
        c = lz4.block.compress(chunk, mode="high_compression",
                               compression=12, store_size=False)
        buf.append(struct.pack("<I", len(c)))
        buf.append(c)
    return b"".join(buf)


def lz4_legacy_decompress(d, size):
    pos, end, out = PAGE, PAGE + size, []
    magic, = struct.unpack_from("<I", d, pos)
    if magic == MAGIC_LZ4:
        pos += 4
    while pos < end:
        n, = struct.unpack_from("<I", d, pos)
        pos += 4
        out.append(lz4.block.decompress(d[pos:pos + n], uncompressed_size=BLOCK))
        pos += n
    return b"".join(out)


def parse_avb(img):
    """解析 AVB 结构，返回 vbmeta 偏移、salt、digest 相关字段。

    AVB footer 在文件末尾 64 字节，含 vbmeta_offset / vbmeta_size。
    vbmeta 内 descriptor 区按 tag 遍历，找到 tag=2 的 hash descriptor：
      头 128 字节，字段 image_size@+16, algo@+24(32B),
      pn_len@+56, salt_len@+60, dig_len@+64
      数据区 @+128 = partition_name + salt + digest
    """
    if len(img) < 64 or img[-64:-60] != b"AVBf":
        return None
    vm_off, = struct.unpack_from(">Q", img, len(img) - 64 + 20)
    vm_size, = struct.unpack_from(">Q", img, len(img) - 64 + 28)
    if img[vm_off:vm_off + 4] != b"AVB0":
        return None
    vm = img[vm_off:vm_off + vm_size]
    auth_size, aux_size = struct.unpack_from(">2Q", vm, 12)
    pos = 192 + auth_size
    end = pos + aux_size
    while pos + 16 <= end:
        tag, nbf = struct.unpack_from(">2Q", vm, pos)
        if tag == 0 and nbf == 0:
            pos += 16  # 跳过前导零 padding，继续找真正的 descriptor
            continue
        if tag == 2:  # hash descriptor
            image_size, = struct.unpack_from(">Q", vm, pos + 16)
            # 数据区（name+salt+digest）名字前可能有 4 字节对齐 padding，
            # 用 find 精确定位 "recovery" 字符串
            name_idx = vm.find(b"recovery", pos, pos + 256)
            if name_idx < 0:
                pos += nbf + 16
                continue
            salt = vm[name_idx + 8: name_idx + 40]
            if len(salt) == 32:
                return {
                    "vm_off": vm_off, "vm_size": vm_size,
                    "salt": salt, "image_size": image_size,
                    "desc_pos": pos,
                    "dig_rel": (name_idx + 40) - pos,
                }
        pos += nbf + 16
    return None


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    img_path = sys.argv[1]
    src_dir = sys.argv[2]
    out_path = sys.argv[3] if len(sys.argv) > 3 else img_path + ".zh.img"

    d = open(img_path, "rb").read()
    log("输入镜像 %d 字节" % len(d))
    assert d[:8] == b"ANDROID!", "不是 Android boot 镜像"

    ramdisk_size, = struct.unpack_from("<I", d, 0x0C)
    log("ramdisk 压缩大小 %d" % ramdisk_size)

    cpio = lz4_legacy_decompress(d, ramdisk_size)
    log("解出 cpio %d 字节" % len(cpio))

    entries = walk_cpio(cpio)
    by_name = {e[0]: e for e in entries}
    log("cpio 条目 %d" % len(entries))

    # 待注入文件（镜像内路径）
    target_files = [
        "twres/languages/en.xml",
        "twres/pages/advanced.xml",
        "twres/pages/settings.xml",
        "twres/resources/images.xml",
        "twres/resources/vars.xml",
        "twres/splash.xml",
        "twres/themes/font.xml",
    ]

    # src_dir 可能直接就是 twres 目录本身，也可能包含 twres 子目录
    new_blobs = {}
    for rel in target_files:
        p = os.path.join(src_dir, rel)
        if not os.path.exists(p):
            # 尝试 src_dir 已经是 twres 上级的情况
            p2 = os.path.join(src_dir, "twres", rel)
            if os.path.exists(p2):
                p = p2
            else:
                log("警告：源文件缺失 %s，跳过" % rel)
                continue
        data = open(p, "rb").read()
        new_blobs[rel] = data
        log("  注入 %-32s %d 字节" % (rel, len(data)))

    sums = {k: hashlib.sha256(v).hexdigest() for k, v in new_blobs.items()}

    # 重建 cpio
    parts = []
    changed = 0
    for name, f, data_start, sz, start, end in entries:
        if name in new_blobs:
            parts.append(emit_entry(name, f, new_blobs[name]))
            changed += 1
        elif name == "ramdisk-files.sha256sum":
            body = cpio[data_start:data_start + sz].decode("utf-8", "replace")
            for rel, h in sums.items():
                body = re.sub(r"^[0-9a-f]{64}(\s+\./" + re.escape(rel) + r")$",
                              h + r"\1", body, flags=re.M)
            parts.append(emit_entry(name, f, body.encode("utf-8")))
            changed += 1
        else:
            parts.append(cpio[start:end])

    new_cpio = b"".join(parts)
    # 512 对齐（官方镜像是对齐的）
    if len(new_cpio) % 512:
        new_cpio += b"\x00" * (512 - len(new_cpio) % 512)
    log("cpio 重建：改动 %d 文件，%d -> %d 字节" % (changed, len(cpio), len(new_cpio)))

    comp = lz4_legacy_compress(new_cpio)
    log("压缩：%d -> %d 字节" % (len(new_cpio), len(comp)))

    # 组装头部 + 新压缩数据
    header = bytearray(d[:PAGE])
    struct.pack_into("<I", header, 0x0C, len(comp))
    body = bytes(header) + comp

    # 处理 AVB
    avb = parse_avb(d)
    if avb:
        new_v = (len(body) + PAGE - 1) // PAGE * PAGE  # vbmeta 新位置（4096 对齐）
        salt = avb["salt"]
        # digest 必须覆盖补齐到 new_v 的完整内容（含零填充），
        # 不能只用 body[:new_v]（body 短于 new_v 时切片会漏掉填充）
        padded = body + b"\x00" * (new_v - len(body))
        digest = hashlib.sha256(salt + padded).digest()

        # 复制原 vbmeta 整块，改 image_size 和 digest
        vm = bytearray(d[avb["vm_off"]: avb["vm_off"] + avb["vm_size"]])
        dp = avb["desc_pos"]
        struct.pack_into(">Q", vm, dp + 16, new_v)
        vm[dp + avb["dig_rel"]: dp + avb["dig_rel"] + 32] = digest

        out = padded + bytes(vm)

        # 更新 footer
        nf = bytearray(d[-64:])
        struct.pack_into(">Q", nf, 12, new_v)   # original_image_size
        struct.pack_into(">Q", nf, 20, new_v)   # vbmeta_offset
        out += bytes(nf)
        log("AVB：vbmeta 移到 %d，digest 已重算" % new_v)
    else:
        out = body
        log("未发现 AVB 结构，跳过 digest 重算")

    open(out_path, "wb").write(out)
    log("已写入 %s (%d 字节)" % (out_path, len(out)))
    # 自校验
    chk = open(out_path, "rb").read()
    assert chk[:8] == b"ANDROID!"
    got, = struct.unpack_from("<I", chk, 0x0C)
    assert got == len(comp), "ramdisk 长度字段不符"
    log("自校验通过")


if __name__ == "__main__":
    main()
