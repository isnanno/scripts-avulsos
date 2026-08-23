# scripts-avulsos

Coleção de scripts e ferramentas simples — um arquivo (ou poucos arquivos) que resolvem uma coisa específica, sem precisar de um repositório inteiro para cada um.

## O que vai aqui

- Scripts `.bat`, `.py`, `.ps1`, etc. que funcionam sozinhos
- Utilitários pessoais, automações rápidas, conversores, atalhos
- Projetos pequenos demais para merecer um repo dedicado

**Não vai aqui:** apps com frontend/backend, bibliotecas reutilizáveis, projetos com CI, testes extensos ou várias pastas interdependentes — esses merecem repositório próprio.

## Como está organizado

Cada script fica em **sua própria pasta**, na raiz do repositório:

```
scripts-avulsos/
├── README.md                 ← este arquivo (visão geral)
├── foto-realista/
│   ├── README.md             ← explica só este script
│   └── foto_realista.bat
└── outro-script/
    ├── README.md
    └── script.py
```

### Regras ao adicionar algo novo

1. **Crie uma pasta** com nome curto em kebab-case (`meu-script`, não `Meu Script`)
2. **Coloque o(s) arquivo(s)** do script dentro dela — evite soltar arquivos soltos na raiz
3. **Escreva um `README.md`** na pasta do script com:
   - O que faz (1–2 frases)
   - Requisitos (Python, Windows, etc.)
   - Como usar (passo a passo simples)
4. **Atualize a tabela abaixo** com uma linha linkando para a pasta
5. **Não commite secrets** (`.env`, tokens, credenciais)

## Scripts disponíveis

| Script | Descrição |
|--------|-----------|
| [foto-realista](foto-realista/) | Deixa fotos geradas por IA com aparência mais realista (compressão, ruído, etc.) |
| [ferramentas-zip](ferramentas-zip/) | Menu ZIP/RAR: adivinhar senha (CPU ou GPU), extrair, criar AES, renumerar e dividir por GB |

## Requisitos gerais

Dependem de cada script — veja o README da pasta correspondente.

## Licença

Uso livre. Cada script é independente; use e adapte como quiser.
