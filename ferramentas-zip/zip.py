#!/usr/bin/env python3
"""
Ferramentas ZIP — menu interativo.

Uso: python zip.py

  1. Adivinhar Senha      — força bruta numérica
  2. Extrair Arquivos     — extrai .zip, .rar, .7z e outros da pasta
  3. Criar Vários Zips    — zipa cada subpasta com senha AES
  4. Renumerar Arquivos   — numera arquivos em cada subpasta (1, 2, 3…)
  5. Dividir ZIP          — extrai e recria vários ZIPs até um tamanho máx. (GB)
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    import msvcrt
else:
    import termios
    import tty

# ---------------------------------------------------------------------------
# Dependências
# ---------------------------------------------------------------------------

DEPENDENCIAS = ("pyzipper", "rarfile", "py7zr")

TENTATIVAS_POR_SEGUNDO = 700


def log(nivel: str, mensagem: str) -> None:
    hora = datetime.now().strftime("%H:%M:%S")
    print(f"[{hora}] {nivel}: {mensagem}", flush=True)


def garantir_dependencias() -> None:
    """Instala pacotes ausentes automaticamente."""
    import importlib.util

    faltando = [
        pkg for pkg in DEPENDENCIAS
        if importlib.util.find_spec(pkg) is None
    ]
    if not faltando:
        return

    log("INFO", f"Instalando dependências: {', '.join(faltando)}")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", *faltando, "-q"],
    )
    log("OK", "Dependências instaladas com sucesso.")


garantir_dependencias()

import pyzipper  # noqa: E402
import py7zr  # noqa: E402
import rarfile  # noqa: E402
import tarfile  # noqa: E402

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def log_linha() -> None:
    print("-" * 52, flush=True)


def fmt_bytes(n: int) -> str:
    for unidade, tamanho in (("GB", 1024**3), ("MB", 1024**2), ("KB", 1024)):
        if n >= tamanho:
            return f"{n / tamanho:.1f} {unidade}"
    return f"{n} B"


# ---------------------------------------------------------------------------
# Entrada do usuário
# ---------------------------------------------------------------------------


def pedir_opcao() -> str:
    print()
    print("=" * 52)
    print("  Ferramentas ZIP")
    print("=" * 52)
    print("  1. Adivinhar Senha")
    print("  2. Extrair Arquivos")
    print("  3. Criar Vários Zips")
    print("  4. Renumerar Arquivos")
    print("  5. Dividir ZIP")
    print("  0. Sair")
    print("=" * 52)
    return input("Escolha (0-5): ").strip()


def pedir_tamanho_gb() -> float:
    while True:
        entrada = input("Tamanho máximo por ZIP (GB): ").strip().replace(",", ".")
        if not entrada:
            log("AVISO", "Informe um valor (ex: 2 ou 1.5).")
            continue
        try:
            gb = float(entrada)
        except ValueError:
            log("AVISO", "Digite um número válido (ex: 2).")
            continue
        if gb <= 0:
            log("AVISO", "O tamanho precisa ser maior que zero.")
            continue
        if gb > 100:
            log("AVISO", "Valor muito alto. Use algo como 1, 2 ou 4 GB.")
            continue
        return gb

def pedir_caminho_arquivo(extensao: str = ".zip") -> Path:
    while True:
        caminho = input(f"Caminho do arquivo {extensao}: ").strip().strip('"')
        if not caminho:
            log("AVISO", "Informe um caminho válido.")
            continue
        arquivo = Path(caminho)
        if not arquivo.is_file():
            log("ERRO", f"Arquivo não encontrado: {arquivo}")
            continue
        if arquivo.suffix.lower() != extensao:
            log("ERRO", f"O arquivo precisa ter extensão {extensao}")
            continue
        return arquivo


def pedir_caminho_pasta() -> Path:
    while True:
        caminho = input("Caminho da pasta: ").strip().strip('"')
        if not caminho:
            log("AVISO", "Informe um caminho válido.")
            continue
        pasta = Path(caminho)
        if not pasta.is_dir():
            log("ERRO", f"Pasta não encontrada: {pasta}")
            continue
        return pasta


def pedir_sim_nao(pergunta: str) -> bool:
    while True:
        resp = input(f"{pergunta} (s/n): ").strip().lower()
        if resp in ("s", "sim"):
            return True
        if resp in ("n", "nao", "não"):
            return False
        log("AVISO", "Responda com s ou n.")


def _ler_senha_mascarada(prompt: str) -> str:
    """Lê senha mostrando * a cada tecla (com suporte a Backspace)."""
    print(prompt, end="", flush=True)
    chars: list[str] = []

    if sys.platform == "win32":
        while True:
            tecla = msvcrt.getwch()
            if tecla in ("\r", "\n"):
                print(flush=True)
                break
            if tecla in ("\b", "\x08"):
                if chars:
                    chars.pop()
                    print("\b \b", end="", flush=True)
                continue
            if tecla in ("\x00", "\xe0"):
                msvcrt.getwch()  # tecla especial (setas etc.) — ignora
                continue
            if tecla == "\x03":  # Ctrl+C
                print(flush=True)
                raise KeyboardInterrupt
            chars.append(tecla)
            print("*", end="", flush=True)
    else:
        fd = sys.stdin.fileno()
        antigo = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            while True:
                tecla = sys.stdin.read(1)
                if tecla in ("\r", "\n"):
                    print(flush=True)
                    break
                if tecla in ("\x7f", "\b"):
                    if chars:
                        chars.pop()
                        print("\b \b", end="", flush=True)
                    continue
                if tecla == "\x03":
                    print(flush=True)
                    raise KeyboardInterrupt
                if ord(tecla) < 32:
                    continue
                chars.append(tecla)
                print("*", end="", flush=True)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, antigo)

    return "".join(chars)


def pedir_senha(motivo: str = "Senha", confirmar: bool = False) -> str:
    while True:
        senha = _ler_senha_mascarada(f"{motivo}: ").strip()
        if not senha:
            log("AVISO", "A senha não pode ser vazia.")
            continue

        if confirmar:
            senha2 = _ler_senha_mascarada("Confirme a senha: ").strip()
            if senha != senha2:
                log("AVISO", "As senhas não coincidem. Tente de novo.")
                continue

        return senha


def pedir_quantidade_digitos() -> int:
    while True:
        entrada = input("Quantos dígitos tem a senha? ").strip()
        if not entrada.isdigit():
            log("AVISO", "Digite apenas números (ex: 4, 6, 8).")
            continue
        digitos = int(entrada)
        if digitos < 1:
            log("AVISO", "Precisa ser pelo menos 1 dígito.")
            continue
        if digitos > 12:
            log("AVISO", "Máximo de 12 dígitos (acima disso levaria meses/anos).")
            continue
        return digitos


# ---------------------------------------------------------------------------
# Utilitários ZIP
# ---------------------------------------------------------------------------


def senha_funciona(arquivo: Path, senha: str) -> bool:
    try:
        with pyzipper.AESZipFile(arquivo, "r") as zf:
            zf.pwd = senha.encode("utf-8")
            for nome in zf.namelist():
                if not nome.endswith("/"):
                    zf.read(nome)
                    return True
    except (RuntimeError, Exception):
        return False
    return False


def estimar_tempo(total: int) -> str:
    segundos = total / TENTATIVAS_POR_SEGUNDO
    if segundos < 60:
        return f"~{segundos:.0f} segundos"
    if segundos < 3600:
        return f"~{segundos / 60:.0f} minutos"
    if segundos < 86400:
        return f"~{segundos / 3600:.1f} horas"
    return f"~{segundos / 86400:.1f} dias"


# ---------------------------------------------------------------------------
# Opção 1 — Adivinhar Senha
# ---------------------------------------------------------------------------


def opcao_adivinhar() -> None:
    log_linha()
    log("INFO", "Modo: Adivinhar Senha (força bruta numérica)")
    log_linha()

    arquivo = pedir_caminho_arquivo()
    digitos = pedir_quantidade_digitos()

    total = 10**digitos
    senha_min = "0" * digitos
    senha_max = "9" * digitos
    intervalo = max(500, total // 200)

    log("INFO", f"Arquivo: {arquivo.name}")
    log("INFO", f"Dígitos: {digitos}")
    log("INFO", f"Combinações: {total:,} ({senha_min} a {senha_max})")
    log("INFO", f"Tempo estimado (pior caso): {estimar_tempo(total)}")
    log("INFO", "Iniciando tentativas...")

    inicio = time.perf_counter()
    senha_encontrada = None
    tentativas = 0
    ultimo_progresso = 0

    for numero in range(total):
        senha = str(numero).zfill(digitos)
        tentativas += 1

        if senha_funciona(arquivo, senha):
            senha_encontrada = senha
            break

        if numero - ultimo_progresso >= intervalo or numero == total - 1:
            elapsed = time.perf_counter() - inicio
            pct = (numero + 1) / total * 100
            vel = (numero + 1) / elapsed if elapsed > 0 else 0
            print(
                f"  [{datetime.now().strftime('%H:%M:%S')}] "
                f"Progresso: {numero + 1:,}/{total:,} ({pct:.1f}%) "
                f"— {vel:.0f}/s — testando: {senha}",
                end="\r",
                flush=True,
            )
            ultimo_progresso = numero

    print()
    duracao = time.perf_counter() - inicio
    log_linha()

    if senha_encontrada:
        log("OK", f"A senha é {senha_encontrada}")
        log("INFO", f"Encontrada em {duracao:.2f}s ({tentativas:,} tentativas)")
    else:
        log("AVISO", f"Nenhuma senha encontrada entre {senha_min} e {senha_max}")
        log("INFO", f"Tempo total: {duracao:.2f}s ({tentativas:,} tentativas)")

    log_linha()


# ---------------------------------------------------------------------------
# Opção 2 — Extrair Arquivos Compactados
# ---------------------------------------------------------------------------

# Extensões suportadas (ordem: nomes compostos primeiro na checagem)
EXTENSOES_COMPACTADOS = (
    ".tar.gz", ".tar.bz2",
    ".zip", ".zipx", ".rar", ".7z",
    ".tar", ".tgz", ".tbz2",
    ".cbz", ".cbr",
)


def _extensao_arquivo(nome: str) -> str | None:
    nome = nome.lower()
    for ext in sorted(EXTENSOES_COMPACTADOS, key=len, reverse=True):
        if nome.endswith(ext):
            return ext
    return None


def nome_pasta_destino(arquivo: Path) -> str:
    """Remove a extensão composta (.tar.gz) para nomear a pasta de destino."""
    nome = arquivo.name
    for ext in sorted(EXTENSOES_COMPACTADOS, key=len, reverse=True):
        if nome.lower().endswith(ext):
            return nome[: -len(ext)]
    return arquivo.stem


def listar_compactados(pasta: Path) -> list[Path]:
    arquivos = []
    for item in sorted(pasta.iterdir()):
        if item.is_file() and _extensao_arquivo(item.name):
            arquivos.append(item)
    return arquivos


def achar_7z() -> Path | None:
    candidatos = [
        Path(r"C:\Program Files\7-Zip\7z.exe"),
        Path(r"C:\Program Files (x86)\7-Zip\7z.exe"),
    ]
    for caminho in candidatos:
        if caminho.is_file():
            return caminho
    return None


def achar_unrar() -> Path | None:
    candidatos = [
        Path(r"C:\Program Files\WinRAR\UnRAR.exe"),
        Path(r"C:\Program Files\WinRAR\UnRAR64.exe"),
        Path(r"C:\Program Files (x86)\WinRAR\UnRAR.exe"),
        Path(r"C:\Program Files (x86)\WinRAR\UnRAR64.exe"),
    ]
    for caminho in candidatos:
        if caminho.is_file():
            return caminho
    return None


def extrair_com_7z(arquivo: Path, destino: Path, senha: str | None) -> None:
    cmd = [str(achar_7z()), "x", str(arquivo), f"-o{destino}", "-y"]
    cmd.append(f"-p{senha}" if senha else "-p-")
    resultado = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if resultado.returncode != 0:
        msg = (resultado.stderr or resultado.stdout or "7-Zip falhou").strip()
        raise RuntimeError(msg)


def extrair_zip(arquivo: Path, destino: Path, senha: str | None) -> None:
    with pyzipper.AESZipFile(arquivo, "r") as zf:
        if senha:
            zf.pwd = senha.encode("utf-8")
        zf.extractall(destino)


def extrair_rar(arquivo: Path, destino: Path, senha: str | None) -> None:
    unrar = achar_unrar()
    if unrar is None:
        raise RuntimeError("UnRAR não encontrado. Instale WinRAR ou 7-Zip.")
    rarfile.UNRAR_TOOL = str(unrar)
    with rarfile.RarFile(arquivo) as rf:
        rf.extractall(destino, pwd=senha)


def extrair_7z(arquivo: Path, destino: Path, senha: str | None) -> None:
    senha_bytes = senha.encode("utf-8") if senha else None
    with py7zr.SevenZipFile(arquivo, mode="r", password=senha_bytes) as arq:
        arq.extractall(path=destino)


def extrair_tar(arquivo: Path, destino: Path, ext: str) -> None:
    modos = {
        ".tar": "r",
        ".tar.gz": "r:gz",
        ".tgz": "r:gz",
        ".tar.bz2": "r:bz2",
        ".tbz2": "r:bz2",
    }
    modo = modos.get(ext, "r")
    with tarfile.open(arquivo, modo) as tf:
        try:
            tf.extractall(destino, filter="data")
        except TypeError:
            tf.extractall(destino)


def extrair_arquivo(arquivo: Path, destino: Path, senha: str | None) -> str:
    """Extrai um compactado. Retorna o nome do método usado."""
    ext = _extensao_arquivo(arquivo.name)
    if ext is None:
        raise ValueError(f"Formato não suportado: {arquivo.name}")

    seven_zip = achar_7z()

    # 7-Zip extrai quase tudo (zip, rar, 7z…) com senha
    if seven_zip and ext in {".zip", ".zipx", ".rar", ".7z", ".cbz", ".cbr"}:
        extrair_com_7z(arquivo, destino, senha)
        return "7-Zip"

    if ext in {".zip", ".zipx", ".cbz"}:
        extrair_zip(arquivo, destino, senha)
        return "pyzipper"
    if ext in {".rar", ".cbr"}:
        extrair_rar(arquivo, destino, senha)
        return "UnRAR"
    if ext == ".7z":
        extrair_7z(arquivo, destino, senha)
        return "py7zr"
    if ext in {".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tbz2"}:
        if senha:
            log("AVISO", f"{arquivo.name}: formato TAR não usa senha, extraindo mesmo assim.")
        extrair_tar(arquivo, destino, ext)
        return "tarfile"

    raise ValueError(f"Formato não suportado: {arquivo.name}")


def opcao_extrair() -> None:
    log_linha()
    log("INFO", "Modo: Extrair Arquivos Compactados")
    log_linha()

    extensoes_txt = ", ".join(sorted({e.lstrip(".") for e in EXTENSOES_COMPACTADOS}))
    log("INFO", f"Formatos: {extensoes_txt}")

    pasta = pedir_caminho_pasta()
    tem_senha = pedir_sim_nao("Os arquivos têm senha?")
    senha = pedir_senha("Informe a senha") if tem_senha else None

    arquivos = listar_compactados(pasta)
    if not arquivos:
        log("AVISO", f"Nenhum arquivo compactado encontrado em: {pasta}")
        return

    log("INFO", f"Encontrados {len(arquivos)} arquivo(s)")
    ok = 0
    falhas = 0

    for i, arquivo in enumerate(arquivos, 1):
        destino = pasta / nome_pasta_destino(arquivo)
        log("INFO", f"[{i}/{len(arquivos)}] Extraindo: {arquivo.name}")

        try:
            destino.mkdir(parents=True, exist_ok=True)
            metodo = extrair_arquivo(arquivo, destino, senha)
            qtd = sum(1 for _ in destino.rglob("*") if _.is_file())
            log("OK", f"Extraído em: {destino} ({qtd} arquivo(s), via {metodo})")
            ok += 1

        except RuntimeError:
            log("ERRO", f"Senha incorreta ou arquivo corrompido: {arquivo.name}")
            falhas += 1
            if destino.exists() and not any(destino.iterdir()):
                destino.rmdir()
        except Exception as exc:
            log("ERRO", f"Falha ao extrair {arquivo.name}: {exc}")
            falhas += 1
            if destino.exists() and not any(destino.iterdir()):
                destino.rmdir()

    log_linha()
    log("INFO", f"Concluído: {ok} extraído(s), {falhas} falha(s)")
    log_linha()


# ---------------------------------------------------------------------------
# Opção 3 — Criar Vários Zips
# ---------------------------------------------------------------------------


def zipar_pasta(origem: Path, destino: Path, senha: str) -> int:
    """Compacta uma pasta em ZIP com AES-256. Retorna bytes escritos."""
    arquivos = sorted(f for f in origem.rglob("*") if f.is_file())
    total = len(arquivos)
    if total == 0:
        log("AVISO", f"  Pasta vazia: {origem.name}/")
        return 0

    total_bytes = sum(f.stat().st_size for f in arquivos)
    bytes_feitos = 0

    with pyzipper.AESZipFile(
        destino,
        "w",
        compression=pyzipper.ZIP_DEFLATED,
        encryption=pyzipper.WZ_AES,
    ) as zf:
        zf.setpassword(senha.encode("utf-8"))
        for i, arquivo in enumerate(arquivos, 1):
            arcname = arquivo.relative_to(origem).as_posix()
            tamanho = arquivo.stat().st_size
            zf.write(arquivo, arcname)
            bytes_feitos += tamanho
            pct = bytes_feitos / total_bytes * 100 if total_bytes else 100
            nome_curto = arcname if len(arcname) <= 40 else "…" + arcname[-39:]
            print(
                f"  Progresso: {i}/{total} ({pct:5.1f}%) — {nome_curto}"
                + " " * 10,
                end="\r",
                flush=True,
            )

    print(flush=True)
    return total_bytes


def opcao_criar() -> None:
    log_linha()
    log("INFO", "Modo: Criar Vários Zips (AES-256)")
    log_linha()

    pasta = pedir_caminho_pasta()
    senha = pedir_senha("Senha para proteger os ZIPs", confirmar=True)

    subpastas = sorted(p for p in pasta.iterdir() if p.is_dir())
    if not subpastas:
        log("AVISO", f"Nenhuma subpasta encontrada em: {pasta}")
        return

    log("INFO", f"Encontradas {len(subpastas)} subpasta(s)")
    criados = 0
    pulados = 0
    falhas = 0

    for i, subpasta in enumerate(subpastas, 1):
        destino = pasta / f"{subpasta.name}.zip"
        log("INFO", f"[{i}/{len(subpastas)}] Compactando: {subpasta.name}/")

        if destino.exists():
            if not pedir_sim_nao(f"  {destino.name} já existe. Sobrescrever?"):
                log("AVISO", f"Pulado: {destino.name}")
                pulados += 1
                continue

        try:
            inicio = time.perf_counter()
            bytes_origem = zipar_pasta(subpasta, destino, senha)
            duracao = time.perf_counter() - inicio
            tamanho_zip = destino.stat().st_size

            log(
                "OK",
                f"Criado: {destino.name} "
                f"({fmt_bytes(tamanho_zip)}, origem: {fmt_bytes(bytes_origem)}, "
                f"{duracao:.1f}s)",
            )
            criados += 1

        except Exception as exc:
            print(flush=True)
            log("ERRO", f"Falha ao zipar {subpasta.name}: {exc}")
            if destino.exists():
                destino.unlink()
            falhas += 1

    log_linha()
    log("INFO", f"Concluído: {criados} criado(s), {pulados} pulado(s), {falhas} falha(s)")
    log_linha()


# ---------------------------------------------------------------------------
# Opção 4 — Renumerar Arquivos
# ---------------------------------------------------------------------------


def renumerar_subpasta(subpasta: Path) -> int:
    """Renomeia todos os arquivos da subpasta para 1, 2, 3… preservando extensão."""
    arquivos = sorted(
        (f for f in subpasta.rglob("*") if f.is_file()),
        key=lambda p: str(p.relative_to(subpasta)).lower(),
    )
    if not arquivos:
        return 0

    nomes_originais = [a.relative_to(subpasta) for a in arquivos]

    # Fase 1: nomes temporários (evita conflito se já existir 1.jpg, 2.png etc.)
    temporarios: list[Path] = []
    for i, arquivo in enumerate(arquivos):
        temp = arquivo.parent / f"__renum_temp_{i:06d}{arquivo.suffix}"
        arquivo.rename(temp)
        temporarios.append(temp)

    # Fase 2: nomes numéricos finais
    for i, temp in enumerate(temporarios, start=1):
        destino = temp.parent / f"{i}{temp.suffix}"
        temp.rename(destino)
        log("OK", f"  {nomes_originais[i - 1]} → {destino.relative_to(subpasta)}")

    return len(arquivos)


def opcao_renumerar() -> None:
    log_linha()
    log("INFO", "Modo: Renumerar Arquivos")
    log_linha()

    pasta = pedir_caminho_pasta()
    subpastas = sorted(p for p in pasta.iterdir() if p.is_dir())

    if not subpastas:
        log("AVISO", f"Nenhuma subpasta encontrada em: {pasta}")
        return

    log("INFO", f"Encontradas {len(subpastas)} subpasta(s)")
    total_renomeados = 0
    vazias = 0

    for i, subpasta in enumerate(subpastas, 1):
        log("INFO", f"[{i}/{len(subpastas)}] Processando: {subpasta.name}/")
        qtd = renumerar_subpasta(subpasta)
        if qtd == 0:
            log("AVISO", f"  Nenhum arquivo em {subpasta.name}/")
            vazias += 1
        else:
            log("OK", f"  {qtd} arquivo(s) renumerado(s) em {subpasta.name}/")
            total_renomeados += qtd

    log_linha()
    log(
        "INFO",
        f"Concluído: {total_renomeados} arquivo(s) renumerado(s) "
        f"em {len(subpastas) - vazias} subpasta(s)"
        + (f", {vazias} vazia(s)" if vazias else ""),
    )
    log_linha()


# ---------------------------------------------------------------------------
# Opção 5 — Dividir ZIP
# ---------------------------------------------------------------------------


def agrupar_por_tamanho(
    arquivos: list[Path],
    max_bytes: int,
) -> list[list[Path]]:
    """Agrupa arquivos em lotes cujo tamanho total (descompactado) ≤ max_bytes."""
    # Margem para cabeçalhos do ZIP/AES não ultrapassarem o limite no arquivo final
    limite = max(1, int(max_bytes * 0.95))
    grupos: list[list[Path]] = []
    atual: list[Path] = []
    atual_bytes = 0

    for arquivo in arquivos:
        tam = arquivo.stat().st_size
        if tam > limite:
            if atual:
                grupos.append(atual)
                atual = []
                atual_bytes = 0
            grupos.append([arquivo])
            continue
        if atual and atual_bytes + tam > limite:
            grupos.append(atual)
            atual = []
            atual_bytes = 0
        atual.append(arquivo)
        atual_bytes += tam

    if atual:
        grupos.append(atual)
    return grupos


def proximo_destino_livre(pasta: Path, prefixo: str, inicio: int = 1) -> Path:
    """Retorna prefixo-N.zip, pedindo sobrescrita se o nome já existir."""
    n = inicio
    while True:
        destino = pasta / f"{prefixo}-{n}.zip"
        if not destino.exists():
            return destino
        if pedir_sim_nao(f"  {destino.name} já existe. Sobrescrever?"):
            return destino
        log("AVISO", f"Mantido existente: {destino.name} — tentando próximo número…")
        n += 1


def criar_zip_lote(
    arquivos: list[Path],
    base: Path,
    destino: Path,
    senha: str | None,
) -> int:
    """Cria um ZIP (AES se houver senha) com os arquivos do lote. Retorna bytes origem."""
    if not arquivos:
        return 0

    total_bytes = 0
    kwargs: dict = {
        "compression": pyzipper.ZIP_DEFLATED,
    }
    if senha:
        kwargs["encryption"] = pyzipper.WZ_AES

    with pyzipper.AESZipFile(destino, "w", **kwargs) as zf:
        if senha:
            zf.setpassword(senha.encode("utf-8"))
        for i, arquivo in enumerate(arquivos, 1):
            arcname = arquivo.relative_to(base).as_posix()
            tamanho = arquivo.stat().st_size
            zf.write(arquivo, arcname)
            total_bytes += tamanho
            pct = i / len(arquivos) * 100
            nome_curto = arcname if len(arcname) <= 40 else "…" + arcname[-39:]
            print(
                f"  Progresso: {i}/{len(arquivos)} ({pct:5.1f}%) — {nome_curto}"
                + " " * 8,
                end="\r",
                flush=True,
            )
    print(flush=True)
    return total_bytes


def opcao_dividir() -> None:
    log_linha()
    log("INFO", "Modo: Dividir ZIP")
    log_linha()

    arquivo = pedir_caminho_arquivo(".zip")
    tem_senha = pedir_sim_nao("O ZIP tem senha?")
    senha = pedir_senha("Informe a senha") if tem_senha else None
    max_gb = pedir_tamanho_gb()
    max_bytes = int(max_gb * (1024**3))

    pasta_saida = arquivo.parent
    prefixo = arquivo.stem
    pasta_tmp = pasta_saida / f".{prefixo}_tmp_dividir"

    tam_origem = arquivo.stat().st_size
    log("INFO", f"Arquivo: {arquivo.name} ({fmt_bytes(tam_origem)})")
    log("INFO", f"Tamanho máximo por parte: {max_gb:g} GB ({fmt_bytes(max_bytes)})")
    log("INFO", f"Saída: {pasta_saida} → {prefixo}-1.zip, {prefixo}-2.zip, …")
    log(
        "AVISO",
        "É necessário espaço livre ≈ tamanho do ZIP + conteúdo extraído "
        "(temporário). Em um arquivo grande, isso pode ser o dobro.",
    )

    if pasta_tmp.exists():
        log("INFO", "Limpando pasta temporária antiga…")
        shutil.rmtree(pasta_tmp, ignore_errors=True)

    pasta_tmp.mkdir(parents=True, exist_ok=True)

    try:
        log("INFO", "Extraindo arquivo original…")
        inicio = time.perf_counter()
        metodo = extrair_arquivo(arquivo, pasta_tmp, senha)
        log("OK", f"Extraído via {metodo} em {time.perf_counter() - inicio:.1f}s")

        arquivos = sorted(
            (f for f in pasta_tmp.rglob("*") if f.is_file()),
            key=lambda p: str(p.relative_to(pasta_tmp)).lower(),
        )
        if not arquivos:
            log("AVISO", "Nenhum arquivo encontrado dentro do ZIP.")
            return

        total_origem = sum(f.stat().st_size for f in arquivos)
        log("INFO", f"{len(arquivos)} arquivo(s), total {fmt_bytes(total_origem)}")

        grupos = agrupar_por_tamanho(arquivos, max_bytes)
        log("INFO", f"Serão criados {len(grupos)} ZIP(s)")

        for g in grupos:
            tamanho_g = sum(f.stat().st_size for f in g)
            if tamanho_g > max_bytes:
                log(
                    "AVISO",
                    f"Um arquivo sozinho ({fmt_bytes(tamanho_g)}) ultrapassa "
                    f"{max_gb:g} GB — irá sozinho em um ZIP maior que o limite.",
                )

        criados = 0
        proximo_num = 1
        for idx, grupo in enumerate(grupos, 1):
            destino = proximo_destino_livre(pasta_saida, prefixo, proximo_num)
            # Próximo candidato após o número usado neste arquivo
            try:
                proximo_num = int(destino.stem.rsplit("-", 1)[-1]) + 1
            except ValueError:
                proximo_num = idx + 1

            log("INFO", f"[{idx}/{len(grupos)}] Criando: {destino.name}")
            try:
                inicio = time.perf_counter()
                bytes_origem = criar_zip_lote(grupo, pasta_tmp, destino, senha)
                duracao = time.perf_counter() - inicio
                tam_zip = destino.stat().st_size
                if tam_zip > max_bytes:
                    log(
                        "AVISO",
                        f"{destino.name} ficou com {fmt_bytes(tam_zip)} "
                        f"(acima do limite de {fmt_bytes(max_bytes)})",
                    )
                log(
                    "OK",
                    f"Criado: {destino.name} "
                    f"({fmt_bytes(tam_zip)}, origem: {fmt_bytes(bytes_origem)}, "
                    f"{len(grupo)} arquivo(s), {duracao:.1f}s)",
                )
                criados += 1
            except Exception as exc:
                print(flush=True)
                log("ERRO", f"Falha ao criar {destino.name}: {exc}")
                if destino.exists():
                    destino.unlink()

        log_linha()
        log("INFO", f"Concluído: {criados} ZIP(s) criado(s) a partir de {arquivo.name}")
        log_linha()

    except Exception as exc:
        log("ERRO", f"Falha ao dividir: {exc}")
    finally:
        if pasta_tmp.exists():
            log("INFO", "Removendo pasta temporária…")
            shutil.rmtree(pasta_tmp, ignore_errors=True)
            log("OK", "Temporários removidos.")


# ---------------------------------------------------------------------------
# Menu principal
# ---------------------------------------------------------------------------


def main() -> None:
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    log("INFO", "Ferramentas ZIP iniciadas")

    acoes = {
        "1": opcao_adivinhar,
        "2": opcao_extrair,
        "3": opcao_criar,
        "4": opcao_renumerar,
        "5": opcao_dividir,
    }

    while True:
        escolha = pedir_opcao()

        if escolha == "0":
            log("INFO", "Encerrando. Até logo!")
            break

        acao = acoes.get(escolha)
        if acao is None:
            log("AVISO", "Opção inválida. Escolha de 0 a 5.")
            continue

        try:
            acao()
        except KeyboardInterrupt:
            print()
            log("AVISO", "Operação interrompida pelo usuário.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        log("INFO", "Encerrando.")
        sys.exit(0)
