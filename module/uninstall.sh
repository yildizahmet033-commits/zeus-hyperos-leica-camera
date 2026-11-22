#!/system/bin/sh
# HyperOS Leica Camera for Xiaomi 12 Pro (zeus) - by Ahmet033
# Clear Android's package cache so the ROM's own camera is picked up again on next boot.
rm -rf /data/system/package_cache/* 2>/dev/null
rm -rf /data/data/com.android.camera/cache /data/data/com.android.camera/code_cache 2>/dev/null
