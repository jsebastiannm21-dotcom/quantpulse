# caida.py - Aviso de caída: revisa si la app publicada responde y, si no, avisa por el bot de Telegram de admin.
# Corre cada 30 minutos con GitHub Actions en el repositorio PÚBLICO «quantpulse» (ahí los minutos son gratis).
# Avisa una vez al caer, recuerda cada 6 horas si sigue caída, y avisa cuando vuelve. Solo usa la librería estándar.
# Prueba local:  python caida.py --prueba
import json
import os
import sys
import time
import urllib.parse
import urllib.request

ESTADO = "estado_caida.txt"            # Lo guarda y lo recupera el workflow (caché de GitHub Actions)
INTENTOS, ESPERA = 3, 60               # Tres intentos, un minuto entre cada uno (evita falsas alarmas)
RECORDAR = 6 * 3600


def responde(url):
    """True si el servidor de Streamlit contesta «ok» en su chequeo de salud."""
    try:
        with urllib.request.urlopen(url.rstrip("/") + "/~/+/_stcore/health", timeout=45) as r:
            return r.status == 200 and r.read(20).strip() == b"ok"
    except Exception:
        return False


def avisar(texto):
    token, chat = os.environ.get("ADMIN_TELEGRAM_TOKEN"), os.environ.get("ADMIN_TELEGRAM_CHAT_ID")
    if not (token and chat):
        print("Sin bot de admin configurado:", texto)
        return
    datos = urllib.parse.urlencode({"chat_id": chat, "text": texto}).encode()
    try:
        urllib.request.urlopen(f"https://api.telegram.org/bot{token}/sendMessage", datos, timeout=30).read()
    except Exception as error:                       # Nunca imprime el token
        print("No se pudo avisar por Telegram:", type(error).__name__)


def decidir(arriba, antes, ahora):
    """(mensaje o None, nuevo estado). antes = {'estado': 'arriba'|'caida', 'desde': t, 'aviso': t}."""
    if arriba:
        if antes.get("estado") == "caida":
            minutos = round((ahora - antes["desde"]) / 60)
            return f"🟢 QUANTPULSE TRADER volvió a responder (estuvo caída unos {minutos} minutos).", {"estado": "arriba"}
        return None, {"estado": "arriba"}
    if antes.get("estado") != "caida":
        return ("🔴 QUANTPULSE TRADER no responde. Revisa share.streamlit.io (Manage app → logs o Reboot app).",
                {"estado": "caida", "desde": ahora, "aviso": ahora})
    if ahora - antes.get("aviso", 0) >= RECORDAR:
        horas = round((ahora - antes["desde"]) / 3600, 1)
        return f"🔴 QUANTPULSE TRADER sigue sin responder (hace {horas} horas).", {**antes, "aviso": ahora}
    return None, antes


def main():
    url = os.environ["APP_URL"]
    antes = json.loads(open(ESTADO, encoding="utf-8").read()) if os.path.exists(ESTADO) else {}
    arriba = False
    for i in range(INTENTOS):
        if responde(url):
            arriba = True
            break
        if i < INTENTOS - 1:
            time.sleep(ESPERA)
    mensaje, nuevo = decidir(arriba, antes, time.time())
    if mensaje:
        avisar(mensaje)
    open(ESTADO, "w", encoding="utf-8").write(json.dumps(nuevo))
    print("La app responde." if arriba else "La app NO responde.", "Aviso enviado." if mensaje else "Sin aviso nuevo.")


if __name__ == "__main__":
    if "--prueba" in sys.argv:
        t = 1_000_000.0
        m, e = decidir(False, {}, t)
        assert m.startswith("🔴") and e["estado"] == "caida"                    # Cae: avisa una vez
        assert decidir(False, e, t + 1800) == (None, e)                         # 30 min después: no repite
        m2, e2 = decidir(False, e, t + RECORDAR)
        assert "sigue sin responder" in m2 and e2["aviso"] == t + RECORDAR      # 6 horas: recuerda
        m3, e3 = decidir(True, e2, t + RECORDAR + 600)
        assert m3.startswith("🟢") and e3 == {"estado": "arriba"}               # Vuelve: avisa
        assert decidir(True, e3, t + RECORDAR + 1200) == (None, {"estado": "arriba"})
        assert responde(os.environ.get("APP_URL", "https://example.invalid")) in (True, False)
        print("Aviso de caída: pruebas OK")
    else:
        main()
