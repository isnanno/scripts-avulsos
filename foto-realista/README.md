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

Prompt atual (melhor resultado até agora):

```
Deixe a foto com aparência de foto real e amadora de celular, tirada no escuro para enviar no WhatsApp: iluminação irregular e fraca, pouca exposição, sombras naturais, ruído/granulação de sensor, leve desfoque de movimento e pequenas imperfeições de câmera. Remova o aspecto cinematográfico e de fotografia profissional, mantendo a imagem original.
```

Se o modelo inventar interface/horário de WhatsApp, tire a menção a WhatsApp e/ou use:

```
Não redesenhe. Não mude pose. Apenas degrade a qualidade da imagem original. Sem texto, sem ícones, sem relógio.
```

Fluxo sugerido: editar no Flow com o prompt acima → depois passar o resultado no `foto_realista.bat`.

## Erros

Se algo der errado (Python não instalado, arquivo não encontrado), aparece um aviso. Em caso de sucesso, o script fecha sem dialog.
