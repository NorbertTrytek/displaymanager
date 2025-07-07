var SERVER_IP = '10.101.133.192';  // IP twojego backendu Flask
var API_URL = 'http://' + SERVER_IP + ':5000/api/links';

var linksContainer = document.getElementById('links');
var iframe = document.getElementById('viewer');

var currentTvId = null;
var tvIds = [];

function fetchLinks() {
  fetch(API_URL)
    .then(response => {
      if (!response.ok) throw new Error(response.statusText);
      return response.json();
    })
    .then(links => {
      displayLinks(links);
      if (tvIds.length > 0) {
        loadTv(tvIds[0]);
      } else {
        linksContainer.textContent = 'Brak dostępnych linków.';
      }
    })
    .catch(err => {
      linksContainer.textContent = 'Błąd pobierania linków: ' + err.message;
    });
}

function displayLinks(links) {
  linksContainer.innerHTML = '';
  tvIds = Object.keys(links);
  tvIds.forEach(tvId => {
    var btn = document.createElement('button');
    btn.textContent = tvId;
    btn.onclick = () => loadTv(tvId);
    linksContainer.appendChild(btn);
  });
}

function loadTv(tvId) {
  currentTvId = tvId;
  Array.from(linksContainer.children).forEach(btn => {
    btn.classList.toggle('active', btn.textContent === tvId);
  });
  iframe.src = 'http://' + SERVER_IP + ':5000/proxy/' + tvId;
  console.log('Ładowanie: ' + tvId);
}

window.onload = fetchLinks;

// Sterowanie pilotem: lewo/prawo zmienia TV
window.addEventListener('keydown', function(e) {
  if (!tvIds.length) return;

  let currentIndex = tvIds.indexOf(currentTvId);
  if (e.key === 'ArrowRight') {
    currentIndex = (currentIndex + 1) % tvIds.length;
    loadTv(tvIds[currentIndex]);
  } else if (e.key === 'ArrowLeft') {
    currentIndex = (currentIndex - 1 + tvIds.length) % tvIds.length;
    loadTv(tvIds[currentIndex]);
  }
});

//Auto odświeżanie iframe co 10 sekund
const REFRESH_INTERVAL_MS = 10000;

setInterval(() => {
  if (iframe.src && currentTvId) {
    iframe.src = iframe.src;
    console.log('Auto odświeżanie: ' + currentTvId);
  }
}, REFRESH_INTERVAL_MS);
