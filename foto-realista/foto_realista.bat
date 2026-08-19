@echo off
setlocal
title Foto Realista
cd /d "%~dp0"
where python >nul 2>&1 || (
  echo.
  echo   Python nao encontrado. Instale em https://python.org
  echo   Marque "Add Python to PATH" na instalacao.
  echo.
  pause
  exit /b 1
)
python -c "import PIL, numpy" 2>nul || (
  echo.
  echo   Instalando dependencias ^(Pillow, numpy^)... aguarde.
  echo.
  python -m pip install Pillow numpy
  if errorlevel 1 (
    echo.
    echo   Falha ao instalar. Tente: python -m pip install Pillow numpy
    echo.
    pause
    exit /b 1
  )
)
set "SCRIPT=%TEMP%\foto_real_%RANDOM%.py"
powershell -NoProfile -Command "$s=$false; Get-Content -LiteralPath '%~f0' | ForEach-Object { if ($_ -eq '#PYCODE#') { $s=$true; return }; if ($s) { $_ } } | Set-Content -LiteralPath '%SCRIPT%' -Encoding UTF8"
python "%SCRIPT%" %*
del "%SCRIPT%" 2>nul
if "%~1"=="" pause
exit /b 0
#PYCODE#
import io
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


def degrade(img: Image.Image) -> Image.Image:
    quality, noise, blur, scale, passes = 45, 0.02, 0.75, 0.72, 3
    vignette = 0.12

    def jpeg_recompress(im, q):
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=q, optimize=False)
        buf.seek(0)
        return Image.open(buf).convert("RGB")

    result = img.convert("RGB")
    result = jpeg_recompress(result, 60)

    w, h = result.size
    result = result.resize((int(w * scale), int(h * scale)), Image.Resampling.BILINEAR)
    result = result.resize((w, h), Image.Resampling.BILINEAR)
    result = result.filter(ImageFilter.GaussianBlur(radius=blur))

    arr = np.array(result, dtype=np.float32)
    gh, gw = arr.shape[:2]
    arr += np.random.normal(0, noise * 255, arr.shape)
    gray = np.dot(arr[..., :3], [0.299, 0.587, 0.114])
    lum = np.random.normal(0, noise * 180, (gh, gw))
    mask = 1.0 - (gray / 255.0) * 0.6
    for c in range(3):
        arr[..., c] = np.clip(arr[..., c] + lum * mask, 0, 255)
    result = Image.fromarray(arr.astype(np.uint8))

    result = ImageEnhance.Contrast(result).enhance(1.05)
    result = ImageEnhance.Color(result).enhance(0.92)
    result = ImageEnhance.Sharpness(result).enhance(0.85)

    arr = np.array(result, dtype=np.float32)
    y, x = np.ogrid[:gh, :gw]
    cx, cy = gw / 2, gh / 2
    dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
    arr *= (1.0 - vignette * (dist / np.sqrt(cx**2 + cy**2)) ** 2)[..., np.newaxis]
    result = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

    for _ in range(passes):
        result = jpeg_recompress(result, quality)

    return result


def save_degraded(img: Image.Image, dest: Path) -> None:
    if dest.suffix.lower() in (".jpg", ".jpeg"):
        img.save(dest, format="JPEG", quality=45)
    elif dest.suffix.lower() == ".png":
        img.save(dest, format="PNG")
    else:
        img.save(dest, format="JPEG", quality=45)


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
