# foto-realista

Deixa fotos com aparência mais natural — como se tivessem sido tiradas no celular e reenviadas no WhatsApp. Útil quando uma imagem gerada por IA fica “boa demais” e você quer algo mais crível.

## O que faz

- Compressão JPEG agressiva (artefatos de blocos)
- Ruído de sensor (grain de foto noturna com flash)
- Leve desfoque e redimensionamento
- Ajustes sutis de cor/contraste
- Vignette nas bordas

## Requisitos

- **Windows**
- **Python 3** instalado ([python.org](https://python.org)) — marque *“Add Python to PATH”* na instalação
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

## Erros

Se algo der errado (Python não instalado, arquivo não encontrado), aparece um aviso. Em caso de sucesso, o script fecha sem dialog.
