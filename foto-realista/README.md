# foto-realista

Deixa fotos com aparência mais natural — como se tivessem sido tiradas no celular e reenviadas. Útil quando uma imagem gerada por IA fica “boa demais” e você quer algo mais crível.

## O que faz

- Compressão JPEG (artefatos de celular)
- Ruído de sensor (grain / chroma leve, adaptado a cenas escuras)
- Leve desfoque, redimensionamento e tilt mínimo
- Cast de white balance, bloom sutil, lift de pretos
- Subsample de cor estilo 4:2:0 e vignette bem leve

## Requisitos

- **Windows**
- **Python 3** instalado ([python.org](https://python.org)) — marque *“Add Python to PATH”* na instalação (o `.bat` também tenta achar o Python sozinho)
- Dependências instaladas automaticamente na primeira execução: `Pillow`, `numpy`

## Como usar

### Arrastar no Explorer (recomendado)

Arraste a foto em cima do `foto_realista.bat`. Ele processa e fecha sozinho.

### Duplo clique

1. Dê duplo clique no `foto_realista.bat`
2. Arraste a imagem para a janela preta do CMD
3. Pressione Enter

## Nomes dos arquivos

| Situação | Resultado |
|----------|-----------|
| Você usa `foto.jpeg` | `foto.jpeg` → versão processada · `foto (Original).jpeg` → backup da original |
| Você usa `foto (Original).jpeg` | Original fica intacta · gera/atualiza `foto.jpeg` |

A versão processada sempre fica com o nome “limpo”; a original ganha `(Original)` no nome.

## Prompt no Flow / Nano (edição)

Por enquanto, use este prompt na edição (não diga “WhatsApp” — o modelo literaliza e inventa UI/horário):

```
Edição leve. Mesma pessoa, mesma pose, mesma mão, mesmo ângulo — não mude nada do conteúdo. Só piora a qualidade: foto de celular antigo no escuro, um pouco tremida, foco errado, pele sem filtro (poros/imperfeições), cores meio lavadas. Sem texto, sem ícones, sem relógio.
```

Se ainda mudar a pose:

```
Não redesenhe. Não mude pose. Apenas degrade a qualidade da imagem original.
```

Fluxo sugerido: editar no Flow com o prompt acima → depois passar o resultado no `foto_realista.bat`.

## Erros

Se algo der errado (Python não instalado, arquivo não encontrado), aparece um aviso. Em caso de sucesso, o script fecha sem dialog.
