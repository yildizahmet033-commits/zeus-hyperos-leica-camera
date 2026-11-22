#!/usr/bin/env python3
"""
HyperOS Leica Camera for Xiaomi 12 Pro (zeus) - patcher
by Ahmet033 - https://github.com/yildizahmet033-commits/zeus-hyperos-leica-camera

Takes the original HyperOS Camera 1+6.2.000360.1 APK, applies the zeus / AOSP
fixes, signs it and builds a flashable KernelSU / Magisk / APatch module zip.

Usage:
  python3 patch.py --apk "Camera 1+6.2.000360.1 com.android.camera.apk" \
                   --smali smali.jar --baksmali baksmali.jar \
                   [--key key.pk8 --cert cert.x509.pem] [--out out_dir]

Required tools on PATH: java, keytool (if no key given), zipalign, apksigner, zip.
"""
import argparse, hashlib, os, re, shutil, struct, subprocess, sys, tempfile, zipfile, zlib

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

# The only APK these byte offsets are valid for.
APK_SHA256 = "662c76d61f2fbe5fb9c66454ffa7a0b42fcb1b05849657ba3f1f50649415bed3"

# (dex, offset, original bytes, new bytes, reason)
BYTE_PATCHES = [
    # --- Beautify: the old "3D beauty" tab types ("1", "2") are not supported by
    #     this camera version on zeus; type "11" loads Smooth / Slender / Big eyes.
    ("classes.dex", 0x849930, "1a01df10", "1a010211", "f0.a0.l(): beauty tab type \"1\" -> \"11\""),
    ("classes.dex", 0x849c3e, "1a013e11", "1a010211", "f0.a0.v(): beauty tab type \"2\" -> \"11\""),
    # --- Zoom (w5.E.P0 = applyZoomRatio)
    ("classes2.dex", 0x862a4a, "38020600", "28060000", "applyZoomRatio: skip Math.max(zoom, 1.0) clamp"),
    ("classes2.dex", 0x862bd4, "6e30661e7d06", "000000000000", "applyZoomRatio: do not override zoomRatio with SCALER_CROP_REGION"),
    ("classes2.dex", 0x862c5a, "380f4200", "00000000", "applyZoomRatio: always use CONTROL_ZOOM_RATIO (enables 0.6x ultra-wide)"),
    ("classes2.dex", 0x862dae, "6e30661efd0e", "000000000000", "applyZoomRatio: do not reset SCALER_CROP_REGION to full array"),
    # --- Beautify parameters (MiCameraCompatBaseImpl.applyBeautyParameter)
    ("classes2.dex", 0x5a6774, "3801e6ff", "00000000", "applyBeautyParameter: send xiaomi.beauty.* ratios without the tag-set check"),
    # --- Vendor tag discovery (w5.c constructor): on non-HyperOS ROMs the camera only
    #     looked at getAvailableCaptureRequestKeys(), so bokeh, 60 FPS, beautify,
    #     smoothTransition, MFNR... were never sent. Always use getAllVendorKeys().
    ("classes2.dex", 0x880a96, "38042a00", "00000000", "w5.c: always discover all vendor request keys"),
    # --- Portrait capture (w5.s0.x): on zeus the parallel-still path asked for output
    #     stream 5, which the portrait session does not have -> null Size -> capture hang.
    #     Use stream 1, like devices where G6.c.M() is true.
    ("classes2.dex", 0x897b6a, "39020d00", "280d0000", "w5.s0.x: portrait capture uses an existing output stream"),
]

# smali edit on classes3.dex: zeus zoom lists start at 0.5x, the HAL's minimum is 0.65x.
SMALI_CLASS = "zeus.smali"
SMALI_METHODS = ("i1", "n1", "q0")
SMALI_FROM = re.compile(r"const/high16 (v\d+), 0x3f000000(\s+# 0\.5f)?")

# Expected results (identical to the tested module build). classes3.dex is rebuilt
# by smali, whose metadata layout can vary; its code is checked by the smali step.
EXPECTED = {
    "classes.dex": "9ac575a474b5595ea2d91d8619f22538196c0d64cb0c963505975524acd3d187",
    "classes2.dex": "bfafa2e434b42aad71e9f479aa7d206d0241c1e21b4a2bbf6ade6c4338829874",
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def run(cmd, **kw):
    print("  $", " ".join(cmd))
    subprocess.run(cmd, check=True, **kw)


def fix_dex_header(d):
    d[12:32] = hashlib.sha1(d[32:]).digest()
    d[8:12] = zlib.adler32(bytes(d[12:])).to_bytes(4, "little")


def patch_bytes(work):
    by_dex = {}
    for dex, off, old, new, why in BYTE_PATCHES:
        by_dex.setdefault(dex, []).append((off, bytes.fromhex(old), bytes.fromhex(new), why))
    for dex, items in by_dex.items():
        p = os.path.join(work, dex)
        d = bytearray(open(p, "rb").read())
        for off, old, new, why in items:
            cur = bytes(d[off:off + len(old)])
            if cur != old:
                sys.exit(f"ERROR: {dex} @ {hex(off)}: expected {old.hex()}, found {cur.hex()} - wrong APK?")
            d[off:off + len(new)] = new
            print(f"  [ok] {dex} {hex(off)}  {why}")
        fix_dex_header(d)
        open(p, "wb").write(d)


def patch_smali(work, java, smali, baksmali):
    out = os.path.join(work, "classes3_smali")
    run([java, "-Xmx6g", "-jar", baksmali, "d", os.path.join(work, "classes3.dex"), "-o", out])
    p = os.path.join(out, SMALI_CLASS)
    lines = open(p).read().split("\n")
    method, done = None, set()
    for i, l in enumerate(lines):
        m = re.match(r"\.method .* (\w+)\(\)Landroid/util/SparseArray;", l)
        if m:
            method = m.group(1)
        elif l.startswith(".end method"):
            method = None
        elif method in SMALI_METHODS and method not in done and SMALI_FROM.search(l):
            lines[i] = SMALI_FROM.sub(r"const \1, 0x3f266666    # 0.65f", l)
            done.add(method)
            print(f"  [ok] classes3.dex zeus.{method}(): ultra-wide zoom 0.5 -> 0.65")
    if done != set(SMALI_METHODS):
        sys.exit(f"ERROR: smali patch incomplete, patched: {sorted(done)}")
    open(p, "w").write("\n".join(lines))
    run([java, "-Xmx8g", "-jar", smali, "a", out, "--api", "29", "-o", os.path.join(work, "classes3.dex")])
    shutil.rmtree(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apk", required=True, help="original HyperOS Camera 1+6.2.000360.1 APK")
    ap.add_argument("--smali", required=True, help="path to smali.jar (2.3.x tested)")
    ap.add_argument("--baksmali", required=True, help="path to baksmali.jar (2.3.x tested)")
    ap.add_argument("--key", help="signing key (.pk8); a throwaway key is created if omitted")
    ap.add_argument("--cert", help="signing certificate (.x509.pem)")
    ap.add_argument("--java", default="java")
    ap.add_argument("--out", default=os.path.join(REPO, "out"))
    a = ap.parse_args()

    print("[1/6] Checking input APK")
    got = sha256(a.apk)
    if got != APK_SHA256:
        sys.exit(f"ERROR: APK sha256 {got} != expected {APK_SHA256}")
    print("  [ok] HyperOS Camera 1+6.2.000360.1")

    os.makedirs(a.out, exist_ok=True)
    work = tempfile.mkdtemp(prefix="leica-zeus-")
    try:
        with zipfile.ZipFile(a.apk) as z:
            for n in ("classes.dex", "classes2.dex", "classes3.dex"):
                z.extract(n, work)

        print("[2/6] Byte patches (classes.dex, classes2.dex)")
        patch_bytes(work)
        print("[3/6] smali patch (classes3.dex)")
        patch_smali(work, a.java, a.smali, a.baksmali)

        for n, h in EXPECTED.items():
            if sha256(os.path.join(work, n)) != h:
                sys.exit(f"ERROR: {n} does not match the tested build")
            print(f"  [ok] {n} matches the tested build")

        print("[4/6] Building APK (+ HyperOS stub classes as classes8.dex)")
        shutil.copy(os.path.join(HERE, "stubs", "hyperos-stubs.dex"), os.path.join(work, "classes8.dex"))
        raw = os.path.join(work, "raw.apk")
        shutil.copy(a.apk, raw)
        subprocess.run(["zip", "-q", "-d", raw, "META-INF/*"], check=False)
        run(["zip", "-q", "-0", "-j", raw] + [os.path.join(work, n) for n in
             ("classes.dex", "classes2.dex", "classes3.dex", "classes8.dex")])
        aligned = os.path.join(work, "MiuiCamera.apk")
        run(["zipalign", "-f", "-P", "16", "4", raw, aligned])

        print("[5/6] Signing")
        key, cert = a.key, a.cert
        if not (key and cert):
            ks = os.path.join(work, "tmp.jks")
            run(["keytool", "-genkeypair", "-keystore", ks, "-storepass", "android", "-keypass", "android",
                 "-alias", "leica", "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000",
                 "-dname", "CN=zeus-hyperos-leica-camera"], stdout=subprocess.DEVNULL)
            run(["apksigner", "sign", "--ks", ks, "--ks-pass", "pass:android", "--ks-key-alias", "leica", aligned])
        else:
            run(["apksigner", "sign", "--key", key, "--cert", cert, aligned])
        run(["apksigner", "verify", aligned])

        print("[6/6] Building module zip")
        mod = os.path.join(work, "module")
        shutil.copytree(os.path.join(REPO, "module"), mod)
        dst = os.path.join(mod, "system", "priv-app", "MiuiCamera")
        os.makedirs(dst, exist_ok=True)
        shutil.copy(aligned, os.path.join(dst, "MiuiCamera.apk"))
        ver = re.search(r"^version=(.*)$", open(os.path.join(mod, "module.prop")).read(), re.M).group(1)
        zip_out = os.path.join(a.out, f"zeus-hyperos-leica-camera-aosp-{ver}.zip")
        if os.path.exists(zip_out):
            os.remove(zip_out)
        run(["zip", "-qr9", zip_out, "."], cwd=mod)
        shutil.copy(aligned, os.path.join(a.out, "MiuiCamera.apk"))
        print(f"\nDone:\n  {zip_out}\n  {os.path.join(a.out, 'MiuiCamera.apk')}")
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
