var SERVER_IP = '10.101.133.225';  // IP twojego backendu Flask
var API_URL = 'http://' + SERVER_IP + ':5000/api/links';

var linksContainer = document.getElementById('links');
var iframe = document.getElementById('viewer');

var currentTvId = null;
var tvIds = [];
let refreshCounter = 0;

function arraysEqual(a, b) {
  return a.length === b.length && a.every((val, i) => val === b[i]);
}

function fetchWithRetry(url, options = {}, retries = 3, delay = 1000) {
  return fetch(url, options).catch(err => {
    if (retries <= 1) {
      throw err;
    } else {
      return new Promise(resolve => setTimeout(resolve, delay)).then(() => {
        return fetchWithRetry(url, options, retries - 1, delay);
      });
    }
  });
}

function fetchLinks(forceUpdate = false, forceReloadIframe = false) {
  fetchWithRetry(API_URL)
    .then(response => {
      if (!response.ok) {
        throw new Error(response.statusText);
      } else {
        return response.json();
      }
    })
    .then(links => {
      const newTvIds = Object.keys(links);
      const tvListChanged = !arraysEqual(tvIds, newTvIds);

      if (forceUpdate || tvListChanged) {
        displayLinks(links);
        if (!newTvIds.includes(currentTvId) && newTvIds.length > 0) {
          loadTv(newTvIds[0]);
        } else {
          if (forceReloadIframe && currentTvId) {
            loadTv(currentTvId);
          }
        }
        console.log('🔁 Lista TV zaktualizowana');
      } else {
        if (forceReloadIframe && currentTvId) {
          loadTv(currentTvId);
        }
        console.log('✅ Lista TV bez zmian');
      }
    })
    .catch(err => {
      console.error('❌ Błąd połączenia z serwerem:', err.message);
      linksContainer.textContent = 'Błąd pobierania linków: ' + err.message;
      tvIds = [];
      currentTvId = null;
      iframe.src = '';
    });
}

function displayLinks(links) {
  linksContainer.innerHTML = '';

  var headerDiv = document.createElement('div');
  headerDiv.style.display = 'flex';
  headerDiv.style.alignItems = 'center';
  headerDiv.style.marginBottom = '5px';

  var logo = document.createElement('img');
  logo.src = 'icon.png';
  logo.alt = 'SpreadDisplay logo';
  logo.style.width = '50px';
  logo.style.height = '50px';
  logo.style.marginRight = '8px';

  var title = document.createElement('span');
  title.textContent = 'SpreadDisplay';
  title.style.fontWeight = 'bold';
  title.style.fontSize = '1.2em';
  title.style.color = '#00b2a5';

  headerDiv.appendChild(logo);
  headerDiv.appendChild(title);
  linksContainer.appendChild(headerDiv);

  tvIds = Object.keys(links);
  tvIds.forEach(tvId => {
    var btn = document.createElement('button');
    btn.textContent = tvId;
    btn.onclick = function () {
      loadTv(tvId);
    };
    btn.classList.toggle('active', tvId === currentTvId);
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

window.onload = function () {
  iframe.src = '';
  currentTvId = null;
  tvIds = [];
  fetchLinks(true);
};

window.addEventListener('keydown', function (e) {
  if (!tvIds.length) {
    return;
  }
  let currentIndex = tvIds.indexOf(currentTvId);
  if (e.key === 'ArrowRight') {
    currentIndex = (currentIndex + 1) % tvIds.length;
    loadTv(tvIds[currentIndex]);
  } else if (e.key === 'ArrowLeft') {
    currentIndex = (currentIndex - 1 + tvIds.length) % tvIds.length;
    loadTv(tvIds[currentIndex]);
  }
});

const REFRESH_INTERVAL_MS = 30000;

setInterval(function () {
  if (currentTvId) {
    iframe.style.transition = 'opacity 1s ease';
    iframe.style.opacity = '0';

    setTimeout(function () {
      const tempIframe = document.createElement('iframe');
      tempIframe.style.display = 'none';
      tempIframe.src = 'http://' + SERVER_IP + ':5000/proxy/' + currentTvId;

      tempIframe.onload = function () {
        iframe.src = tempIframe.src;
        setTimeout(function () {
          iframe.style.opacity = '1';
        }, 100);
        console.log('🔄 Auto odświeżenie iframe: ' + currentTvId);
        tempIframe.remove();
      };

      document.body.appendChild(tempIframe);
    }, 500);
  }
}, REFRESH_INTERVAL_MS);

const LINKS_CHECK_INTERVAL_MS = 30000;

setInterval(function () {
  refreshCounter++;
  const forceReloadIframe = refreshCounter % 3 === 0;
  fetchLinks(false, forceReloadIframe);
}, LINKS_CHECK_INTERVAL_MS);
