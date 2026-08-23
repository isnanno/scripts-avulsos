# ferramentas-zip

Menu interativo em Python para ZIP/RAR: adivinhar senha (CPU ou GPU), extrair, criar com AES, renumerar arquivos e dividir ZIP grande em partes.

## O que faz

| # | Opção | Descrição |
|---|--------|-----------|
| 1 | **Adivinhar Senha** | Força bruta numérica em `.zip` ou `.rar` (CPU ou GPU) |
| 2 | **Extrair Arquivos** | Extrai `.zip`, `.rar`, `.7z` e outros de uma pasta |
| 3 | **Criar Vários Zips** | Zipa cada subpasta com a mesma senha (AES-256) |
| 4 | **Renumerar Arquivos** | Em cada subpasta, renomeia para `1`, `2`, `3`… |
| 5 | **Dividir ZIP** | Extrai e recria vários ZIPs até um tamanho máximo em GB |

## Requisitos básicos (sempre)

- **Windows** (recomendado; também roda em outros SO)
- **Python 3** — [https://www.python.org/downloads/](https://www.python.org/downloads/)  
  Na instalação, marque **"Add python.exe to PATH"**
- Na primeira execução o script instala sozinho: `pyzipper`, `rarfile`, `py7zr`

### Para RAR na CPU (opção 1 → CPU, ou opção 2)

Instale **um** destes (o script detecta sozinho):

| Programa | Link |
|----------|------|
| **7-Zip** | [https://www.7-zip.org/](https://www.7-zip.org/) |
| **WinRAR** | [https://www.win-rar.com/](https://www.win-rar.com/) |

---

## GPU — o que baixar (opção 1 → GPU)

A GPU **não** é obrigatória. Sem ela, use CPU.  
Com GPU (ex.: RTX 4090), senhas de 6–8 dígitos caem em segundos/minutos em vez de horas.

### Resumo rápido

| Arquivo | Ferramenta na GPU | O que instalar |
|---------|-------------------|----------------|
| **`.zip`** (AES) | **Hashcat** | Hashcat + driver da placa |
| **`.rar`** | **John the Ripper** (OpenCL) | John (inclui `john.exe` + `rar2john.exe`) + driver da placa |

> **Por quê John no RAR?** Em várias VMs com driver NVIDIA recente, o Hashcat 7.x quebra com erro de PTX/CUDA (`Unsupported .version 9.3`). O John com OpenCL funciona estável no RAR. O script escolhe isso automaticamente.

---

### 1) Driver da placa de vídeo

| Placa | Link |
|-------|------|
| **NVIDIA** | [https://www.nvidia.com/Download/index.aspx](https://www.nvidia.com/Download/index.aspx) |
| **AMD** | [https://www.amd.com/en/support](https://www.amd.com/en/support) |

Confira se a GPU aparece:

```powershell
nvidia-smi
```

---

### 2) Hashcat (obrigatório para ZIP na GPU)

1. Baixe a versão **Windows** (binários):  
   **[https://hashcat.net/hashcat/](https://hashcat.net/hashcat/)**  
   (ou releases: [https://github.com/hashcat/hashcat/releases](https://github.com/hashcat/hashcat/releases))
2. Extraia, por exemplo em: `C:\hashcat-7.1.2\`
3. Confirme que existe: `C:\hashcat-7.1.2\hashcat.exe`

O script procura sozinho em `C:\hashcat*` e no PATH. Se não achar, pede o caminho do `.exe`.

---

### 3) John the Ripper jumbo (obrigatório para RAR na GPU)

Precisa do pacote **jumbo** com `rar2john.exe` e `john.exe`.

1. Baixe o build **Windows 64-bit** nas releases oficiais:  
   **[https://github.com/openwall/john-packages/releases](https://github.com/openwall/john-packages/releases)**  
   Procure algo como `john-*-win64` / `Windows` (arquivo `.7z` ou `.zip`).
2. Extraia, por exemplo em: `C:\john\`
3. Confirme que existem:
   ```
   C:\john\run\john.exe
   C:\john\run\rar2john.exe
   ```

Página do projeto (referência): [https://www.openwall.com/john/](https://www.openwall.com/john/)

Teste rápido:

```powershell
C:\john\run\rar2john.exe "C:\caminho\arquivo.rar"
C:\john\run\john.exe --list=opencl-devices
```

Se listar sua RTX/AMD, a GPU está ok para o John.

---

### Pasta sugerida no disco

```
C:\
├── hashcat-7.1.2\
│   └── hashcat.exe          ← ZIP + GPU
└── john\
    └── run\
        ├── john.exe         ← RAR + GPU
        └── rar2john.exe     ← extrai hash do RAR
```

---

## Como usar

```powershell
python zip.py
```

Menu: `1`–`5`, ou `0` para sair.

### Opção 1 — Adivinhar senha (CPU ou GPU)

1. Informe o caminho do `.zip` ou `.rar`
2. Informe quantos dígitos tem a senha (ex.: `6`)
3. Escolha:
   - `1` = CPU  
   - `2` = GPU  

| Tipo | O que o script usa na GPU |
|------|---------------------------|
| ZIP AES | Hashcat (modo `13600`) |
| RAR5 | John `RAR5-opencl` + `rar2john` |
| RAR3 | John `rar-opencl` + `rar2john` |

**Dica de teste:** use um arquivo pequeno. ZIP gigante pode falhar no Hashcat (`Token length exception`).

### Opção 5 — Dividir ZIP

Ex.: `backup.zip` com limite `2` GB gera:

```
backup-1.zip
backup-2.zip
backup-3.zip
…
```

na mesma pasta. A pasta temporária é apagada no final.

---

## Observações

- Senhas nas opções 2, 3 e 5 aparecem como `********`
- Opção 5 precisa de espaço em disco ≈ ZIP + conteúdo extraído
- Se um arquivo sozinho for maior que o limite em GB, ele vai sozinho (pode passar do limite)
- Se a GPU falhar, o script oferece tentar CPU

## Erros comuns

| Erro | O que fazer |
|------|-------------|
| Hashcat / PTX `Unsupported .version` | No RAR o script já usa John. No ZIP: atualize o driver NVIDIA ou use CPU |
| `rar2john` / John não encontrado | Extraia o John em `C:\john\run\` (links acima) |
| RAR na CPU sem 7-Zip/WinRAR | Instale [7-Zip](https://www.7-zip.org/) ou [WinRAR](https://www.win-rar.com/) |
| `Token length exception` | Use um ZIP de teste menor |

Logs: `INFO`, `OK`, `AVISO`, `ERRO` com horário. `Ctrl+C` cancela.

## Licença

Uso livre. Adapte como quiser.
