# Berp Sistemas — loader (spinner de carregamento)

Só o globo de pastilhas da logo, animado em loop infinito e sem emenda. Fundo transparente, canvas quadrado 512×512.

| Estilo | Movimento | Ciclo |
|---|---|---|
| **spin** | O globo gira enquanto uma onda de brilho percorre as pastilhas. | 2 s por volta |
| **pulse** | O globo fica parado e a onda passa pelas pastilhas em círculo, acendendo e apagando. | 1,5 s |
| **build** | As pastilhas se encaixam uma a uma, da esquerda para a direita, até montar o globo; depois saem na mesma ordem e o ciclo recomeça. | 2,6 s |
| **twinkle** | O globo fica completo e cada pastilha pulsa sozinha (encolhe, apaga e volta), cada uma num momento diferente. | 1,6 s |
| **breathe** | A bola "respira": as pastilhas se juntam até formar uma esfera compacta e depois se espalham com as frestas bem abertas antes de voltar ao normal. | 2 s |
| **whirl** | A bola compacta, gira rápido (duas voltas), vai expandindo enquanto desacelera, para exatamente no formato original e logo compacta de novo. | 2,5 s |

| spin | pulse | build |
|---|---|---|
| ![spin](preview/berp_loader_spin.gif) | ![pulse](preview/berp_loader_pulse.gif) | ![build](preview/berp_loader_build.gif) |

| twinkle | breathe | whirl |
|---|---|---|
| ![twinkle](preview/berp_loader_twinkle.gif) | ![breathe](preview/berp_loader_breathe.gif) | ![whirl](preview/berp_loader_whirl.gif) |

## Arquivos

| Arquivo | Uso |
|---|---|
| `berp_loader_<estilo>.json` | **Lottie** (60 fps). Android, iOS, Flutter, React Native, Web. |
| `berp_loader_<estilo>.svg` | SVG com animação CSS, sem dependências (web). Com `prefers-reduced-motion`, o movimento fica mais lento (e o spin para de girar). |
| `android/drawable/avd_berp_loader_<estilo>.xml` | Animated Vector Drawable nativo, sem biblioteca, 64dp. spin e pulse: Android 5+. Os demais usam keyframes: Android 6+ nativo; abaixo disso, carregue com `AnimatedVectorDrawableCompat.create(context, R.drawable.avd_berp_loader_build)`. |
| `preview/` | GIF e MP4 de cada estilo. |
| `tools/loader.py`, `tools/loader_tiles.py` | Geram tudo de novo: o primeiro faz spin e pulse, o segundo build, twinkle, breathe e whirl (ambos usam `../berp-splash/tools/pieces.json`). |

## Como usar

### Android — nativo, sem dependências

Copie o XML para `res/drawable/`:

```xml
<ImageView
    android:id="@+id/loader"
    android:layout_width="64dp"
    android:layout_height="64dp"
    android:src="@drawable/avd_berp_loader_spin" />
```

```kotlin
(loader.drawable as Animatable).start()   // roda até chamar stop()
```

Troque `spin` pelo nome do estilo que quiser (`pulse`, `build`, `twinkle`, `breathe`, `whirl`) em todos os exemplos. No spin e no pulse, as pastilhas entram na onda uma a uma na primeira volta; depois o ciclo fica contínuo.

### Android — Lottie

```xml
<com.airbnb.lottie.LottieAnimationView
    android:layout_width="64dp"
    android:layout_height="64dp"
    app:lottie_rawRes="@raw/berp_loader_spin"
    app:lottie_autoPlay="true"
    app:lottie_loop="true" />
```

### iOS (lottie-ios)

```swift
let loader = LottieAnimationView(name: "berp_loader_spin")
loader.loopMode = .loop
loader.play()
```

### Flutter (`lottie`)

```dart
SizedBox(width: 64, height: 64, child: Lottie.asset('assets/berp_loader_spin.json'))
```

### React Native (`lottie-react-native`)

```jsx
<LottieView source={require('./berp_loader_spin.json')} autoPlay loop style={{ width: 64, height: 64 }} />
```

### Web

```html
<img src="berp_loader_spin.svg" alt="Carregando" width="64" height="64">
```

## Ajustar

Em `tools/loader.py`, `VARIANTS` define o ciclo (`period`, em quadros a 60 fps), se gira (`rotate`) e a intensidade da onda: escala mínima (`smin`) e opacidade mínima (`omin`) das pastilhas apagadas.

Em `tools/loader_tiles.py`, `VARIANTS` traz a linha do tempo de cada pastilha (quadros, valores e easing; `spread` é o quanto as pastilhas se afastam do centro e `spin` é o giro da bola inteira), e `SHIFTS` define quando cada pastilha começa: no build segue a varredura da esquerda para a direita, no twinkle é sorteado, e no breathe e no whirl as pastilhas de fora andam um pouco depois das de dentro.

```bash
python3 tools/loader.py out ../berp-splash/tools/pieces.json
python3 tools/loader_tiles.py out ../berp-splash/tools/pieces.json
```
