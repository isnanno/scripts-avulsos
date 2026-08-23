# ferramentas-zip

Menu interativo em Python para trabalhar com ZIPs: testar senha numérica (CPU ou GPU), extrair, criar com AES, renumerar arquivos e dividir um ZIP grande em várias partes.

## O que faz

1. **Adivinhar Senha** — força bruta numérica em **ZIP ou RAR**
   - **CPU** — Python + 7-Zip/WinRAR (sempre funciona, mais lento)
   - **GPU** — Hashcat + placa de vídeo (muito mais rápido)
     - ZIP AES → Hashcat `-m 13600`
     - RAR5 → `-m 13000` (precisa [rar2john](https://www.openwall.com/john/) / John the Ripper)
     - RAR3 → `-m 12500` / `23800`
2. **Extrair Arquivos** — extrai `.zip`, `.rar`, `.7z` e outros de uma pasta (com ou sem senha)
3. **Criar Vários Zips** — zipa cada subpasta com a mesma senha (AES-256)
4. **Renumerar Arquivos** — em cada subpasta, renomeia arquivos para `1`, `2`, `3`… (mantém a extensão)
5. **Dividir ZIP** — extrai um ZIP, divide o conteúdo em várias partes até um tamanho máximo em GB e recria com a mesma senha

## Requisitos

- **Windows** (também funciona em outros sistemas, com pequenas diferenças no teclado da senha)
- **Python 3** instalado ([python.org](https://python.org)) — marque *"Add Python to PATH"* na instalação
- Dependências instaladas automaticamente na primeira execução: `pyzipper`, `rarfile`, `py7zr`
- Para `.rar`: **WinRAR** ou **7-Zip** instalado ajuda (o script detecta sozinho)
- Para **GPU** (opção 1): [Hashcat](https://hashcat.net/hashcat/) + driver NVIDIA/AMD
- Para **GPU com RAR**: também o [John the Ripper](https://www.openwall.com/john/) (`rar2john.exe`)
- Para **CPU com RAR**: 7-Zip ou WinRAR (o script detecta sozinho)

## Como usar

1. Abra o terminal na pasta deste script
2. Rode:

```powershell
python zip.py
```

3. Escolha a opção no menu (`1` a `5`, ou `0` para sair)

### Exemplos rápidos

| Opção | O que informar |
|-------|----------------|
| 1 | Caminho do `.zip`/`.rar` + quantos dígitos + **CPU ou GPU** |
| 2 | Pasta com arquivos compactados + se têm senha |
| 3 | Pasta com subpastas + senha (aparece `*`; pede confirmação) |
| 4 | Pasta com subpastas (cada uma é numerada do zero) |
| 5 | Um `.zip` + senha (se tiver) + tamanho máximo em GB (ex.: `2`) |

### Opção 1 com GPU

1. Escolha `1` → informe o ZIP → digitos (ex.: `6` ou `8`)
2. Escolha `2` (GPU)
3. Se o Hashcat não estiver no PATH, cole o caminho do `hashcat.exe`
4. O script extrai o hash AES e roda o Hashcat com máscara numérica (`?d?d?d…`)

Dica: para testar GPU, crie um ZIP pequeno na opção 3 com senha tipo `123456` — ZIPs enormes podem estourar o limite de tamanho do hash no Hashcat.

### Opção 5 — saída

Se o arquivo for `backup.zip` e o limite for 2 GB, gera:

```
backup-1.zip
backup-2.zip
backup-3.zip
…
```

na mesma pasta do original. A pasta temporária de extração é apagada no final.

## Observações

- Senhas digitadas nas opções 2, 3 e 5 aparecem como `********` (não ficam em branco)
- Espaço em disco: na opção 5, conte com espaço ≈ tamanho do ZIP + conteúdo extraído
- Se um único arquivo for maior que o limite em GB, ele vai sozinho em um ZIP (pode passar do limite)
- GPU usa Hashcat modo `13600` (WinZip AES) — o mesmo formato da opção 3 deste script

## Erros

Se faltar Python, dependência, Hashcat ou a senha estiver errada, o script mostra um log com horário (`INFO`, `OK`, `AVISO`, `ERRO`). Use `Ctrl+C` para cancelar uma operação em andamento.
