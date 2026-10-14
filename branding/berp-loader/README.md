# Berp Sistemas — loader (spinner de carregamento)

Só o globo de pastilhas da logo, animado em loop infinito e sem emenda. Fundo transparente, canvas quadrado 512×512.

| Estilo | Movimento | Ciclo |
|---|---|---|
| **spin** | O globo gira enquanto uma onda de brilho percorre as pastilhas. | 2 s por volta |
| **pulse** | O globo fica parado e a onda passa pelas pastilhas em círculo, acendendo e apagando. | 1,5 s |

| spin | pulse |
|---|---|
| ![spin](preview/berp_loader_spin.gif) | ![pulse](preview/berp_loader_pulse.gif) |

## Arquivos

| Arquivo | Uso |
|---|---|
| `berp_loader_spin.json`, `berp_loader_pulse.json` | **Lottie** (60 fps). Android, iOS, Flutter, React Native, Web. |
| `berp_loader_spin.svg`, `berp_loader_pulse.svg` | SVG com animação CSS, sem dependências (web). Com `prefers-reduced-motion`, para de girar e pulsa mais devagar. |
| `android/drawable/avd_berp_loader_*.xml` | Animated Vector Drawable nativo (API 21+), sem biblioteca. Tamanho padrão de 64dp. |
| `preview/` | GIF e MP4 de cada estilo. |
| `tools/loader.py` | Gera tudo de novo (usa `../berp-splash/tools/pieces.json`). |

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

Na primeira volta, as pastilhas entram na onda uma a uma; depois o ciclo fica contínuo.

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

```bash
python3 tools/loader.py out ../berp-splash/tools/pieces.json
```
