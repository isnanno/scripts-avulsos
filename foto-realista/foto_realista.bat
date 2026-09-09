@echo off
setlocal EnableExtensions
title Foto Realista
cd /d "%~dp0"

set "PYEXE="
rem Resolve real python.exe (PATH often missing when double-clicking .bat)
where py >nul 2>&1 && for /f "delims=" %%I in ('py -3 -c "import sys; print(sys.executable)" 2^>nul') do set "PYEXE=%%I"
if not defined PYEXE if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PYEXE=%LocalAppData%\Programs\Python\Python312\python.exe"
if not defined PYEXE if exist "%LocalAppData%\Programs\Python\Python313\python.exe" set "PYEXE=%LocalAppData%\Programs\Python\Python313\python.exe"
if not defined PYEXE if exist "%LocalAppData%\Programs\Python\Python311\python.exe" set "PYEXE=%LocalAppData%\Programs\Python\Python311\python.exe"
if not defined PYEXE if exist "%ProgramFiles%\Python312\python.exe" set "PYEXE=%ProgramFiles%\Python312\python.exe"
if not defined PYEXE (
  for /d %%D in ("%LocalAppData%\Programs\Python\Python*") do (
    if not defined PYEXE if exist "%%~D\python.exe" set "PYEXE=%%~D\python.exe"
  )
)
if not defined PYEXE where python >nul 2>&1 && for /f "delims=" %%I in ('where python') do (
  echo %%I | find /i "WindowsApps" >nul || if not defined PYEXE set "PYEXE=%%I"
)
if not defined PYEXE (
  echo.
  echo   Python nao encontrado. Instale em https://python.org
  echo   Marque "Add Python to PATH" na instalacao.
  echo.
  pause
  exit /b 1
)

"%PYEXE%" -c "import PIL, numpy" 2>nul || (
  echo.
  echo   Instalando dependencias ^(Pillow, numpy^)... aguarde.
  echo.
  "%PYEXE%" -m pip install Pillow numpy
  if errorlevel 1 (
    echo.
    echo   Falha ao instalar. Tente: "%PYEXE%" -m pip install Pillow numpy
    echo.
    pause
    exit /b 1
  )
)
set "SCRIPT=%TEMP%\foto_real_%RANDOM%.py"
powershell -NoProfile -Command "$s=$false; Get-Content -LiteralPath '%~f0' | ForEach-Object { if ($_ -eq '#PYCODE#') { $s=$true; return }; if ($s) { $_ } } | Set-Content -LiteralPath '%SCRIPT%' -Encoding UTF8"
"%PYEXE%" "%SCRIPT%" %*
del "%SCRIPT%" 2>nul
if "%~1"=="" pause
exit /b 0
#PYCODE#
import io
import random
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple


def ensure_deps():
    try:
        from PIL import Image, ImageEnhance, ImageFilter
        import numpy as np
        return Image, ImageEnhance, ImageFilter, np
    except ImportError:
        print("\n  Instalando dependencias (Pillow, numpy)... aguarde.\n")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow", "numpy"])
        from PIL import Image, ImageEnhance, ImageFilter
        import numpy as np
        return Image, ImageEnhance, ImageFilter, np


Image, ImageEnhance, ImageFilter, np = ensure_deps()


def _jpeg_recompress(im: Image.Image, q: int) -> Image.Image:
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=q, optimize=False, subsampling=2)
    buf.seek(0)
    return Image.open(buf).convert("RGB")


def _to_yuv(arr: np.ndarray):
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    y = 0.299 * r + 0.587 * g + 0.114 * b
    u = -0.14713 * r - 0.28886 * g + 0.436 * b
    v = 0.615 * r - 0.51499 * g - 0.10001 * b
    return y, u, v


def _from_yuv(y: np.ndarray, u: np.ndarray, v: np.ndarray) -> np.ndarray:
    r = y + 1.13983 * v
    g = y - 0.39465 * u - 0.58060 * v
    b = y + 2.03211 * u
    return np.stack([r, g, b], axis=-1)


def _whatsapp_size(w: int, h: int, long_side: int = 1600) -> Tuple[int, int]:
    m = max(w, h)
    if m > long_side:
        s = long_side / m
        w, h = int(round(w * s)), int(round(h * s))
    # even dims help 4:2:0-ish chroma
    w -= w % 2
    h -= h % 2
    return max(w, 2), max(h, 2)


def _chroma420(y: np.ndarray, u: np.ndarray, v: np.ndarray):
    h, w = y.shape
    cw, ch = max(w // 2, 1), max(h // 2, 1)

    def down_up(ch_arr):
        im = Image.fromarray(np.clip(ch_arr + 128, 0, 255).astype(np.uint8), mode="L")
        im = im.resize((cw, ch), Image.Resampling.BILINEAR)
        im = im.resize((w, h), Image.Resampling.BILINEAR)
        return np.array(im, dtype=np.float32) - 128.0

    return y, down_up(u), down_up(v)


def _blob_noise(shape, sigma: float, blob: int) -> np.ndarray:
    h, w = shape
    sh, sw = max(h // blob, 1), max(w // blob, 1)
    n = np.random.normal(0, sigma, (sh, sw)).astype(np.float32)
    im = Image.fromarray(np.clip(n * 8 + 128, 0, 255).astype(np.uint8), mode="L")
    im = im.resize((w, h), Image.Resampling.BILINEAR)
    return (np.array(im, dtype=np.float32) - 128.0) / 8.0


def degrade(img: Image.Image) -> Image.Image:
    # Subtle WhatsApp phone look — match amostras (esp. 3): fine grain, not TV static
    jpeg_pass_q, final_feel_q = 58, 70
    passes = 2
    soft_scale = 0.78
    blur = 0.55
    vignette = 0.035
    lum_noise = 0.018
    chroma_noise = 0.032

    result = img.convert("RGB")

    # 1) WhatsApp-ish long side
    tw, th = _whatsapp_size(*result.size, 1600)
    if (tw, th) != result.size:
        result = result.resize((tw, th), Image.Resampling.BILINEAR)

    # 2) micro tilt (handheld)
    angle = random.uniform(-0.28, 0.28)
    if abs(angle) > 0.05:
        tilted = result.rotate(angle, resample=Image.Resampling.BILINEAR, expand=True, fillcolor=(0, 0, 0))
        cw, ch = result.size
        left = max((tilted.width - cw) // 2, 0)
        top = max((tilted.height - ch) // 2, 0)
        result = tilted.crop((left, top, left + cw, top + ch))

    result = _jpeg_recompress(result, 82)

    # soft optic: down/up + blur, then cheap ISP sharpen
    w, h = result.size
    small = result.resize((max(int(w * soft_scale), 2), max(int(h * soft_scale), 2)), Image.Resampling.BILINEAR)
    result = small.resize((w, h), Image.Resampling.BILINEAR)
    result = result.filter(ImageFilter.GaussianBlur(radius=blur))
    result = ImageEnhance.Sharpness(result).enhance(1.08)

    arr = np.array(result, dtype=np.float32)

    # 3) white-balance cast + weak R<->B crosstalk
    warm = random.uniform(-0.03, 0.045)
    arr[..., 0] *= 1.0 + warm
    arr[..., 1] *= 1.0 + warm * 0.2
    arr[..., 2] *= 1.0 - warm * 0.55
    rb = random.uniform(0.012, 0.028)
    r0, b0 = arr[..., 0].copy(), arr[..., 2].copy()
    arr[..., 0] = r0 * (1.0 - rb) + b0 * rb
    arr[..., 2] = b0 * (1.0 - rb) + r0 * rb

    # 4) dirty-lens bloom on highlights (gentle)
    gray = np.dot(arr[..., :3], [0.299, 0.587, 0.114])
    hi = np.clip((gray - 185.0) / 65.0, 0.0, 1.0)[..., None]
    bloom_img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(radius=random.uniform(3.5, 5.5))
    )
    bloom = np.array(bloom_img, dtype=np.float32)
    arr = arr + bloom * hi * random.uniform(0.10, 0.18)

    # 5) YUV noise: mostly fine luma; chroma subtle (avoid RGB static)
    y, u, v = _to_yuv(arr)
    mean_y = float(np.mean(y))
    # Dark AI scenes amplify any noise into rainbow static — scale down hard
    scene = 0.45 if mean_y < 40 else (0.65 if mean_y < 70 else 1.0)
    shadow = np.clip(1.0 - (y / 255.0), 0.0, 1.0)
    shadow_w = (0.50 + 0.35 * shadow) * scene
    y = y + np.random.normal(0, lum_noise * 255, y.shape).astype(np.float32) * shadow_w
    # fine mottling (higher blob = smaller grain)
    y = y + _blob_noise(y.shape, lum_noise * 40 * scene, blob=random.randint(12, 18)) * (0.2 + 0.2 * shadow)
    u = u + _blob_noise(u.shape, chroma_noise * 40 * scene, blob=random.randint(10, 16)) * (0.35 + 0.4 * shadow)
    v = v + _blob_noise(v.shape, chroma_noise * 40 * scene, blob=random.randint(10, 16)) * (0.35 + 0.4 * shadow)
    # light chroma pepper (kept low so it stays grayish, not neon)
    u += np.random.normal(0, chroma_noise * 12 * scene, u.shape).astype(np.float32) * shadow_w
    v += np.random.normal(0, chroma_noise * 12 * scene, v.shape).astype(np.float32) * shadow_w

    # 6) fake 4:2:0 chroma subsample (mosquito-ish)
    y, u, v = _chroma420(y, u, v)
    arr = _from_yuv(y, u, v)

    # 7) lift crushed blacks (phones leave muddy darks, not pure 0)
    lift = random.uniform(4.0, 7.0)
    if mean_y < 40:
        lift += 3.0  # keep some muddy detail instead of void + snow
    arr = arr + lift * np.clip(1.0 - arr / 255.0, 0.0, 1.0) ** 1.35

    # mild banding in low luma
    band = np.clip(1.0 - y / 140.0, 0.0, 1.0)[..., None]
    levels = 80.0
    quantized = np.round(arr / 255.0 * levels) / levels * 255.0
    arr = arr * (1.0 - 0.08 * band) + quantized * (0.08 * band)

    result = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    result = ImageEnhance.Color(result).enhance(random.uniform(0.93, 0.99))
    result = ImageEnhance.Contrast(result).enhance(random.uniform(0.98, 1.03))
    # Slight mid lift on very dark frames so subject stays readable like WA night selfies
    if mean_y < 45:
        result = ImageEnhance.Brightness(result).enhance(1.06)

    # mild vignette (WhatsApp samples barely have one)
    arr = np.array(result, dtype=np.float32)
    gh, gw = arr.shape[:2]
    yy, xx = np.ogrid[:gh, :gw]
    cx, cy = gw / 2.0, gh / 2.0
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    arr *= (1.0 - vignette * (dist / (np.sqrt(cx**2 + cy**2) + 1e-6)) ** 2)[..., None]
    result = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

    for i in range(passes):
        q = jpeg_pass_q + (0 if i else 6)
        result = _jpeg_recompress(result, q)
        # tiny late chroma (skip on very dark scenes — was the rainbow culprit)
        if i == 0 and mean_y >= 40:
            a = np.array(result, dtype=np.float32)
            yy2, uu, vv = _to_yuv(a)
            sh = np.clip(1.0 - (yy2 / 255.0), 0.0, 1.0)
            uu = uu + _blob_noise(uu.shape, 1.6, blob=14) * (0.3 + 0.3 * sh)
            vv = vv + _blob_noise(vv.shape, 1.6, blob=14) * (0.3 + 0.3 * sh)
            a = _from_yuv(yy2, uu, vv)
            result = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

    # final recompress near typical WA quality feel
    result = _jpeg_recompress(result, final_feel_q)
    return result


def save_degraded(img: Image.Image, dest: Path) -> None:
    q = 68
    if dest.suffix.lower() in (".jpg", ".jpeg"):
        img.save(dest, format="JPEG", quality=q, optimize=False, subsampling=2)
    elif dest.suffix.lower() == ".png":
        # still save as jpeg-like degradation path for png sources
        img.save(dest, format="PNG")
    else:
        img.save(dest, format="JPEG", quality=q, optimize=False, subsampling=2)


def process(path: Path) -> Tuple[Path, Path]:
    path = path.resolve()
    img = Image.open(path)
    result = degrade(img)

    if path.stem.endswith(" (Original)"):
        # Original fica intacta; saida = mesmo nome sem "(Original)"
        out = path.with_stem(path.stem[: -len(" (Original)")])
        if out.exists():
            out.unlink()
        save_degraded(result, out)
        return out, path

    # Foto normal: original vira "(Original)", saida fica com o nome de antes
    backup = path.with_stem(f"{path.stem} (Original)")
    if backup.exists():
        backup.unlink()
    out = path
    path.rename(backup)
    save_degraded(result, out)
    return out, backup


def notify(msg: str, erro: bool = False) -> None:
    try:
        import ctypes
        icon = 0x10 if erro else 0x40
        ctypes.windll.user32.MessageBoxW(0, msg, "Foto Realista", icon)
    except Exception:
        print(msg)


def ask_drag() -> Optional[Path]:
    print()
    print("  Arraste a imagem para ESTA janela e pressione Enter")
    print("  (ou arraste direto em cima do foto_realista.bat no Explorer)")
    print()
    raw = input("  > ").strip().strip('"').strip("'")
    return Path(raw) if raw else None


def main():
    dragged = len(sys.argv) > 1

    if dragged:
        paths = [Path(p.strip('"').strip("'")) for p in sys.argv[1:]]
    else:
        path = ask_drag()
        paths = [path] if path else []

    if not paths:
        if dragged:
            notify("Nenhuma imagem informada.", erro=True)
        else:
            print("\n  Nenhuma imagem informada.")
        sys.exit(1)

    outputs = []
    for path in paths:
        if not path.exists():
            msg = f"Nao achei:\n{path}"
            if dragged:
                notify(msg, erro=True)
            else:
                print(f"\n  {msg}")
            sys.exit(1)
        if not dragged:
            print("\n  Processando...")
        out, backup = process(path)
        if not dragged:
            outputs.append(f"{out.name}\n(Original: {backup.name})")

    if not dragged:
        for out in outputs:
            print(f"\n  Pronto! Salvo em:\n  {out}\n")


if __name__ == "__main__":
    main()
