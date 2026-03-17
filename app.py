from flask import Flask, render_template_string, request, jsonify
from connexion import connecter_gmail
from envoi import charger_file_attente, sauvegarder_file_attente, envoyer_reponse
from surveillant import demarrer_surveillance, etat, lock, log
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
demarrer_surveillance()

HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Email AI Assistant</title>
  <link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet"/>
  <style>
    :root { --bg:#f5f0e8;--surface:#fffdf7;--border:#d4c9b0;--accent:#2d5016;--accent2:#c84b2f;--text:#1a1a14;--text-muted:#7a7060;--radius:4px; }
    *{box-sizing:border-box;margin:0;padding:0}
    body{background:var(--bg);color:var(--text);font-family:'DM Mono',monospace;min-height:100vh;padding:40px 20px}
    body::before{content:'';position:fixed;inset:0;pointer-events:none;z-index:0;opacity:.5;background:url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none'%3E%3Cg fill='%23c4b89a' fill-opacity='0.15'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")}
    .container{position:relative;z-index:1;max-width:960px;margin:0 auto}
    header{display:flex;align-items:flex-end;justify-content:space-between;margin-bottom:24px;padding-bottom:20px;border-bottom:2px solid var(--text);flex-wrap:wrap;gap:16px}
    .logo h1{font-family:'Instrument Serif',serif;font-size:2.2rem;font-weight:400;letter-spacing:-.02em;line-height:1}
    .logo h1 em{font-style:italic;color:var(--accent2)}
    .logo p{font-size:.7rem;color:var(--text-muted);margin-top:4px;letter-spacing:.1em;text-transform:uppercase}
    .stats{display:flex;gap:24px;align-items:center}
    .stat{text-align:right}
    .stat .number{font-family:'Instrument Serif',serif;font-size:2rem;line-height:1}
    .stat .label{font-size:.65rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:.08em}
    .stat.attente .number{color:var(--accent2)}
    .stat.simples .number{color:var(--accent)}
    .stat.ignores .number{color:var(--text-muted)}
    .status-bar{display:flex;align-items:center;gap:12px;padding:10px 16px;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);margin-bottom:24px;font-size:.75rem;flex-wrap:wrap}
    .status-dot{width:8px;height:8px;border-radius:50%;background:var(--accent);box-shadow:0 0 8px var(--accent);animation:pulse 2s infinite;flex-shrink:0}
    .status-dot.pause{background:var(--accent2);box-shadow:0 0 8px var(--accent2);animation:none}
    @keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
    .status-text{flex:1;color:var(--text-muted)}
    .btn-pause{padding:6px 14px;border-radius:var(--radius);font-family:'DM Mono',monospace;font-size:.72rem;cursor:pointer;border:1px solid var(--border);background:transparent;color:var(--text);transition:all .15s}
    .btn-pause:hover{border-color:var(--accent2);color:var(--accent2)}
    .section-title{font-family:'Instrument Serif',serif;font-size:1.1rem;font-weight:400;margin-bottom:16px;color:var(--text-muted)}
    .empty{text-align:center;padding:60px 20px;border:1px dashed var(--border);border-radius:var(--radius)}
    .empty .icon{font-size:2.5rem;margin-bottom:12px}
    .empty p{color:var(--text-muted);font-size:.82rem;line-height:1.6}
    .cards{display:flex;flex-direction:column;gap:20px}
    .card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;box-shadow:4px 4px 0 var(--border);animation:slideIn .3s ease}
    @keyframes slideIn{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
    .card-header{padding:14px 20px;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center;background:var(--bg)}
    .card-meta{display:flex;flex-direction:column;gap:3px}
    .card-from{font-size:.72rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:.06em}
    .card-subject{font-family:'Instrument Serif',serif;font-size:1.15rem;font-weight:400}
    .badge{font-size:.65rem;padding:4px 10px;border-radius:20px;background:#fde8e3;color:var(--accent2);border:1px solid #f5c4b8;text-transform:uppercase;letter-spacing:.08em;white-space:nowrap}
    .card-body{padding:20px;display:grid;grid-template-columns:1fr 1fr;gap:20px}
    @media(max-width:600px){.card-body{grid-template-columns:1fr}}
    .section-label{font-size:.65rem;text-transform:uppercase;letter-spacing:.1em;color:var(--text-muted);margin-bottom:8px}
    .original-text{background:var(--bg);border:1px solid var(--border);border-radius:var(--radius);padding:12px;font-size:.78rem;line-height:1.6;color:var(--text-muted);min-height:120px;max-height:200px;overflow-y:auto;white-space:pre-wrap}
    .reponse-textarea{width:100%;min-height:120px;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:12px;font-family:'DM Mono',monospace;font-size:.78rem;line-height:1.6;color:var(--text);resize:vertical;outline:none;transition:border-color .2s}
    .reponse-textarea:focus{border-color:var(--accent)}
    .card-footer{padding:14px 20px;border-top:1px solid var(--border);display:flex;gap:10px;justify-content:flex-end}
    .btn{padding:8px 18px;border-radius:var(--radius);font-family:'DM Mono',monospace;font-size:.76rem;cursor:pointer;border:1px solid;transition:all .15s;letter-spacing:.04em}
    .btn-envoyer{background:var(--accent);color:white;border-color:var(--accent)}
    .btn-envoyer:hover{background:#1e3a0f}
    .btn-rejeter{background:transparent;color:var(--accent2);border-color:var(--accent2)}
    .btn-rejeter:hover{background:#fde8e3}
    .btn:disabled{opacity:.4;cursor:not-allowed}
    .toast{position:fixed;bottom:24px;right:24px;padding:12px 20px;border-radius:var(--radius);font-size:.78rem;font-family:'DM Mono',monospace;z-index:100;animation:toastIn .3s ease;border:1px solid}
    .toast.succes{background:#e8f3e0;color:var(--accent);border-color:#b8d9a0}
    .toast.erreur{background:#fde8e3;color:var(--accent2);border-color:#f5c4b8}
    @keyframes toastIn{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
  </style>
</head>
<body>
<div class="container">
  <header>
    <div class="logo">
      <h1>Email <em>AI</em> Assistant</h1>
      <p>Surveillance &amp; validation en temps r&eacute;el</p>
    </div>
    <div class="stats">
      <div class="stat attente"><div class="number" id="countAttente">0</div><div class="label">En attente</div></div>
      <div class="stat simples"><div class="number" id="countSimples">0</div><div class="label">Envoy&eacute;s</div></div>
      <div class="stat ignores"><div class="number" id="countIgnores">0</div><div class="label">Ignor&eacute;s</div></div>
    </div>
  </header>
  <div class="status-bar">
    <div class="status-dot" id="statusDot"></div>
    <span class="status-text" id="statusText">Chargement...</span>
    <button class="btn-pause" id="btnPause" onclick="togglePause()">Pause</button>
  </div>
  <div class="section-title">File d'attente &mdash; validation requise</div>
  <div id="contenu"></div>
</div>
<script src="/static/app.js"></script>
</body>
</html>"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/api/file")
def api_file():
    return jsonify(charger_file_attente())

@app.route("/api/statut")
def api_statut():
    with lock:
        return jsonify(etat)

@app.route("/api/pause", methods=["POST"])
def api_pause():
    with lock:
        etat["actif"] = not etat["actif"]
        log.info("Surveillance " + ("reprise" if etat["actif"] else "mise en pause") + " par l'utilisateur")
    return jsonify({"actif": etat["actif"]})

@app.route("/api/envoyer", methods=["POST"])
def api_envoyer():
    data = request.get_json()
    email_id = data.get("email_id")
    reponse = data.get("reponse", "")
    file = charger_file_attente()
    email = next((e for e in file if e["email_id"] == email_id), None)
    if not email:
        return jsonify({"succes": False, "erreur": "Email introuvable"})
    try:
        service = connecter_gmail()
        succes = envoyer_reponse(service, email["destinataire"], email["sujet"], reponse)
        if succes:
            email["statut"] = "approuve"
            sauvegarder_file_attente(file)
            log.info("APPROUVE | " + email["sujet"] + " -> " + email["destinataire"])
            with lock:
                etat["stats"]["simples"] += 1
            return jsonify({"succes": True})
        return jsonify({"succes": False, "erreur": "Echec envoi"})
    except Exception as e:
        return jsonify({"succes": False, "erreur": str(e)})

@app.route("/api/rejeter", methods=["POST"])
def api_rejeter():
    data = request.get_json()
    email_id = data.get("email_id")
    file = charger_file_attente()
    for email in file:
        if email["email_id"] == email_id:
            email["statut"] = "rejete"
            log.info("REJETE | " + email["sujet"])
            break
    sauvegarder_file_attente(file)
    return jsonify({"succes": True})

if __name__ == "__main__":
    print("\n🚀 Email AI Assistant démarré")
    print("   Interface : http://localhost:5001")
    print("   Logs      : logs/activity.log\n")
    app.run(debug=False, port=5001)
