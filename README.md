# Monitor de ofertas — Shopping do Inter

Checa o Shopping do Inter (vitrine "No Inter" e "Nos sites parceiros") e avisa no Telegram quando aparece
**Galaxy S25 Ultra** ou **Galaxy A57** (inclusive combos com Watch/Buds) abaixo do limite.

## Configurar (uma vez)

1. **Telegram:** fale com `@BotFather`, envie `/newbot`, escolha um nome e copie o token.
   Depois abra o seu bot e mande qualquer mensagem (ex.: "oi").
2. **GitHub:** em *Settings → Secrets and variables → Actions*:
   - aba **Secrets** → *New repository secret* → nome `TELEGRAM_TOKEN`, valor = o token.
   - (opcional) aba **Variables** → `LIMITE_S25ULTRA` (padrão 4000), `LIMITE_A57` (padrão 2000), `LIMITE_S25ULTRA_WATCH` (padrão 5000), `LIMITE_A57_WATCH` (padrão 2500),
     `INCLUIR_USADOS` = `1` para incluir usados.
3. Aba **Actions** → *Monitor Shopping do Inter* → **Run workflow**.
   Em segundos chega no Telegram “Bot ligado!” com os preços atuais.

## Como avisa

- **Abaixo do normal:** o robô guarda o preço de cada aparelho dia a dia. O preço normal é a mediana dos
  últimos 14 dias. Se o valor “Sai por” ficar 1% ou mais abaixo do normal, chega aviso.
- **Dentro do limite:** produto com valor “Sai por” até o limite do modelo → aviso.
- Não repete o mesmo aviso. Só avisa de novo se o preço cair ainda mais, ou se voltar ao normal e depois cair outra vez.

Para parar: aba **Actions** → workflow → menu “…” → *Disable workflow*.
