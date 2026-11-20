"""Monitora o Shopping do Inter e avisa no Telegram quando aparece oferta
de Galaxy S25 Ultra ou Galaxy A57.

Variáveis de ambiente (secrets no GitHub):
  TELEGRAM_TOKEN    token do bot (do @BotFather)            - obrigatório
  TELEGRAM_CHAT_ID  seu chat id (opcional: se faltar, o script descobre
                    sozinho a partir da última mensagem enviada ao bot)
Ajustes opcionais (variáveis do repositório):
  LIMITE_S25ULTRA   padrão 4000   (valor "Sai por", já com cashback)
  LIMITE_A57        padrão 1800
  INCLUIR_USADOS    "1" para incluir usados/recondicionados (padrão: não)
  QUEDA_MINIMA      padrão 0.05   (avisa também quando o preço cai 5%+)
"""
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

API = "https://marketplace-api.web.bancointer.com.br/site/affiliate/inter/v1/search/products"
SITE = "https://shopping.inter.co"
BUSCAS = ["galaxy s25 ultra", "s25 ultra", "galaxy a57", "a57"]
PAGINAS = 10  # 36 produtos por página
ESTADO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "estado.json")

MODELOS = {
    "S25 Ultra": (re.compile(r"s\s?25\s*ultra", re.I), float(os.getenv("LIMITE_S25ULTRA") or 4000)),
    "A57": (re.compile(r"\ba\s?57\b", re.I), float(os.getenv("LIMITE_A57") or 1800)),
}
ACESSORIO = re.compile(
    r"capa|case|pel[ií]cula|vidro|caneta|carregador|cabo|fonte|suporte|"
    r"lente|protetor|adesivo|skin|bateria externa|power ?bank|anel|pulseira|"
    r"carteira|clear|tpu|silicone|kit pel", re.I)
CELULAR = re.compile(r"celular|smartphone|galaxy|combo|\d+\s?gb", re.I)
USADO = re.compile(r"usado|seminovo|recondicionado|vitrine|refurb|excelente -|muito bom -|bom -", re.I)
INCLUIR_USADOS = os.getenv("INCLUIR_USADOS") == "1"
QUEDA_MINIMA = float(os.getenv("QUEDA_MINIMA") or 0.05)
TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()


def get_json(url, data=None):
    req = urllib.request.Request(url, data=data, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36",
        "Accept": "application/json",
        "Origin": SITE,
        "Referer": SITE + "/",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def buscar(termo):
    vistos = []
    for pag in range(PAGINAS):
        q = urllib.parse.urlencode({"lang": "pt-BR", "searchText": termo,
                                    "offset": pag * 36, "limit": 36})
        try:
            j = get_json(f"{API}?{q}")
        except Exception as e:  # noqa: BLE001
            print(f"[aviso] falha na busca '{termo}' pág {pag}: {e}")
            break
        prods = j.get("products") or []
        vistos += prods
        if len(prods) < 36 or (j.get("pagination") or {}).get("isLastPage"):
            break
        time.sleep(0.5)
    return vistos


def classificar(p):
    nome = p.get("name") or ""
    if ACESSORIO.search(nome) and not re.search(r"combo|\+ ?galaxy", nome, re.I):
        return None
    if not CELULAR.search(nome):
        return None
    if USADO.search(nome) and not INCLUIR_USADOS:
        return None
    for modelo, (rx, _) in MODELOS.items():
        if rx.search(nome):
            return modelo
    return None


def preco(p):
    v = p.get("fullLiquidPriceValue") or p.get("priceValue")
    return float(v) if v is not None else None


def brl(v):
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def telegram(metodo, **params):
    url = f"https://api.telegram.org/bot{TOKEN}/{metodo}"
    data = urllib.parse.urlencode(params).encode()
    return get_json(url, data=data)


def descobrir_chat():
    r = telegram("getUpdates")
    for u in reversed(r.get("result", [])):
        msg = u.get("message") or u.get("channel_post") or {}
        if msg.get("chat", {}).get("id"):
            return str(msg["chat"]["id"])
    return ""


def enviar(texto):
    for i in range(0, len(texto), 3800):
        telegram("sendMessage", chat_id=CHAT_ID, text=texto[i:i + 3800],
                 parse_mode="HTML", disable_web_page_preview="true")


def main():
    global CHAT_ID
    if not TOKEN:
        sys.exit("Falta o secret TELEGRAM_TOKEN.")
    estado = {}
    if os.path.exists(ESTADO):
        with open(ESTADO, encoding="utf-8") as f:
            estado = json.load(f)
    chat_salvo = str(estado.pop("_chat_id", "") or "")
    if not CHAT_ID:
        CHAT_ID = chat_salvo or descobrir_chat()
        if not CHAT_ID:
            sys.exit("Mande qualquer mensagem para o seu bot no Telegram e rode de novo.")
        print("Chat id encontrado.")
    primeira_vez = not estado

    achados = {}
    for termo in BUSCAS:
        for p in buscar(termo):
            modelo = classificar(p)
            v = preco(p)
            if modelo and v and p.get("id"):
                achados[p["id"]] = (modelo, v, p)
    print(f"{len(achados)} aparelhos encontrados")

    alertas = []
    novo_estado = {}
    for pid, (modelo, v, p) in achados.items():
        limite = MODELOS[modelo][1]
        antes = estado.get(pid)
        novo_estado[pid] = v
        abaixo = v <= limite
        caiu = antes is not None and v <= antes * (1 - QUEDA_MINIMA)
        ja_avisado_abaixo = antes is not None and antes <= limite and v >= antes
        if (abaixo and not ja_avisado_abaixo) or caiu:
            motivo = "abaixo do seu limite" if abaixo else f"caiu de {brl(antes)}"
            alertas.append((v, modelo, p, motivo))

    if primeira_vez:
        linhas = ["✅ <b>Bot ligado!</b> Vou checar o Shopping do Inter a cada 20 minutos.",
                  f"Limites: S25 Ultra até {brl(MODELOS['S25 Ultra'][1])} · A57 até {brl(MODELOS['A57'][1])} (valor “Sai por”).",
                  "", "Mais baratos agora:"]
        for modelo in MODELOS:
            lista = sorted(((v, p) for _, (m, v, p) in achados.items() if m == modelo), key=lambda x: x[0])
            if lista:
                v, p = lista[0]
                linhas.append(f"• {modelo}: {brl(v)} — {p.get('sellerName', '')}\n  {SITE}/{p.get('slug', '')}")
        enviar("\n".join(linhas))

    if alertas:
        alertas.sort(key=lambda a: a[0])
        linhas = ["🔥 <b>Oferta no Shopping do Inter</b>"]
        for v, modelo, p, motivo in alertas[:15]:
            nome = html.escape((p.get("name") or "")[:110])
            linhas.append(
                f"\n<b>{nome}</b>\n{html.escape(p.get('sellerName', ''))} · {p.get('price', '')}"
                f" · cashback {p.get('fullCashback', '-')}\n"
                f"Sai por <b>{brl(v)}</b> ({motivo})\n{SITE}/{p.get('slug', '')}")
        enviar("\n".join(linhas))
        print(f"{len(alertas)} alerta(s) enviado(s)")

    # guarda também itens que sumiram nesta rodada, para não re-avisar se voltarem iguais
    for pid, v in estado.items():
        novo_estado.setdefault(pid, v)
    if not os.getenv("TELEGRAM_CHAT_ID", "").strip():
        novo_estado["_chat_id"] = CHAT_ID
    with open(ESTADO, "w", encoding="utf-8") as f:
        json.dump(novo_estado, f, ensure_ascii=False, indent=0, sort_keys=True)


if __name__ == "__main__":
    main()
