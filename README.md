# Monitor de ofertas — Shopping do Inter

Checa o Shopping do Inter a cada 20 minutos e avisa no Telegram quando aparece
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

- Produto novo com valor “Sai por” (já com cashback) até o limite → aviso.
- Produto que já existia e caiu 5% ou mais → aviso.
- A mesma oferta não é repetida a cada rodada (o `estado.json` guarda o último preço).

Para parar: aba **Actions** → workflow → menu “…” → *Disable workflow*.
