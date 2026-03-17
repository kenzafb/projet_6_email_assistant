var file = [];
var statutActuel = {actif: true, stats: {simples: 0, ignores: 0}};

async function rafraichir() {
  try {
    var r1 = await fetch('/api/file');
    var r2 = await fetch('/api/statut');
    file = await r1.json();
    statutActuel = await r2.json();
    afficher();
    mettreAJourStatut();
  } catch(e) {
    document.getElementById('statusText').textContent = 'Erreur de connexion...';
  }
}

function mettreAJourStatut() {
  var dot = document.getElementById('statusDot');
  var txt = document.getElementById('statusText');
  var btn = document.getElementById('btnPause');
  var s = statutActuel;

  if (s.actif) {
    btn.textContent = '⏸ Pause';
    var msg = '● Surveillance active';
    if (s.derniere_verification) { msg += ' — Dernière vérif : ' + s.derniere_verification; }
    if (s.prochaine_verification) { msg += ' — Prochaine : ' + s.prochaine_verification; }
    txt.textContent = msg;
  } else {
    btn.textContent = '▶ Reprendre';
    txt.textContent = '⏸ Surveillance en pause';
  }

  if (s.stats) {
    document.getElementById('countSimples').textContent = s.stats.simples;
    document.getElementById('countIgnores').textContent = s.stats.ignores;
  } else {
    document.getElementById('countSimples').textContent = 0;
    document.getElementById('countIgnores').textContent = 0;
  }
}

function afficher() {
  var contenu = document.getElementById('contenu');
  var enAttente = file.filter(function(e) { return e.statut === 'en_attente'; });
  document.getElementById('countAttente').textContent = enAttente.length;

  if (enAttente.length === 0) {
    var icone, message;
    if (!statutActuel.actif) {
      icone = '⏸️';
      message = 'Surveillance en pause.<br>Aucun nouvel email ne sera traité jusqu\'à la reprise.';
    } else {
      icone = '✉️';
      message = 'Aucun email en attente de validation.<br>La surveillance tourne en arrière-plan.';
    }
    contenu.innerHTML = '<div class="empty"><div class="icon">' + icone + '</div><p>' + message + '</p></div>';
    return;
  }

  var cardsDiv = contenu.querySelector('.cards');
  if (!cardsDiv) {
    contenu.innerHTML = '<div class="cards"></div>';
    cardsDiv = contenu.querySelector('.cards');
  }

  enAttente.forEach(function(email) {
    if (!document.getElementById('card-' + email.email_id)) {
      var div = document.createElement('div');
      div.innerHTML = construireCard(email);
      cardsDiv.appendChild(div.firstElementChild);
    }
  });

  var cards = cardsDiv.querySelectorAll('.card');
  cards.forEach(function(cardEl) {
    var id = cardEl.id.replace('card-', '');
    var existe = enAttente.find(function(e) { return e.email_id === id; });
    if (!existe) { cardEl.remove(); }
  });
}

function construireCard(email) {
  var html = '<div class="card" id="card-' + email.email_id + '">';
  html += '<div class="card-header">';
  html += '<div class="card-meta">';
  html += '<span class="card-from">De : ' + email.destinataire + '</span>';
  html += '<span class="card-subject">' + email.sujet + '</span>';
  html += '</div><span class="badge">⚠ Complexe</span></div>';
  html += '<div class="card-body">';
  html += '<div><div class="section-label">Email original</div>';
  html += '<div class="original-text">' + (email.corps_original || '(vide)') + '</div></div>';
  html += '<div><div class="section-label">Réponse proposée — modifiable</div>';
  html += '<textarea class="reponse-textarea" id="rep-' + email.email_id + '">' + email.reponse_proposee + '</textarea></div>';
  html += '</div><div class="card-footer">';
  html += '<button class="btn btn-rejeter" onclick="rejeter(\'' + email.email_id + '\')">❌ Rejeter</button>';
  html += '<button class="btn btn-envoyer" onclick="envoyer(\'' + email.email_id + '\')">✅ Envoyer</button>';
  html += '</div></div>';
  return html;
}

function togglePause() {
  fetch('/api/pause', {method: 'POST'}).then(function() { rafraichir(); });
}

async function envoyer(id) {
  var reponse = document.getElementById('rep-' + id).value;
  var btnE = document.querySelector('#card-' + id + ' .btn-envoyer');
  var btnR = document.querySelector('#card-' + id + ' .btn-rejeter');
  btnE.disabled = true; btnR.disabled = true;
  btnE.textContent = 'Envoi...';

  var res = await fetch('/api/envoyer', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({email_id: id, reponse: reponse})
  });
  var data = await res.json();

  if (data.succes) {
    supprimerCard(id);
    toast('✅ Réponse envoyée !', 'succes');
    if (statutActuel.stats) { statutActuel.stats.simples++; }
    mettreAJourStatut();
  } else {
    toast('❌ Erreur : ' + (data.erreur || 'inconnue'), 'erreur');
    btnE.disabled = false; btnR.disabled = false;
    btnE.textContent = '✅ Envoyer';
  }
}

async function rejeter(id) {
  await fetch('/api/rejeter', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({email_id: id})
  });
  supprimerCard(id);
  toast('🗑️ Email rejeté', 'succes');
}

function supprimerCard(id) {
  file = file.filter(function(e) { return e.email_id !== id; });
  var c = document.getElementById('card-' + id);
  if (c) {
    c.style.opacity = '0';
    c.style.transform = 'translateX(20px)';
    c.style.transition = 'all 0.3s ease';
    setTimeout(function() { afficher(); }, 300);
  }
}

function toast(msg, type) {
  var t = document.createElement('div');
  t.className = 'toast ' + type;
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(function() { t.remove(); }, 3000);
}

rafraichir();
setInterval(rafraichir, 10000);
