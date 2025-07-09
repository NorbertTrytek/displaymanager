import os
import json
import threading
import time
from flask import Flask, request, jsonify, render_template_string, send_file
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

app = Flask(__name__)

LINKS_FILE = 'tv_links.json'
SNAPSHOT_DIR = 'snapshots'

# Tworzymy pliki/katalogi jeśli ich nie ma
if not os.path.exists(LINKS_FILE):
    default_links = {
        "tv1": "https://www.example.com",
        "tv2": "https://www.example.com",
        "tv3": "https://www.example.com",
        "tv4": "https://www.example.com",
        "tv5": "https://www.example.com",
        "tv6": "https://www.example.com"
    }
    with open(LINKS_FILE, 'w') as f:
        json.dump(default_links, f, indent=2)

if not os.path.exists(SNAPSHOT_DIR):
    os.makedirs(SNAPSHOT_DIR)

def load_links():
    with open(LINKS_FILE, 'r') as f:
        return json.load(f)

def save_links(links):
    with open(LINKS_FILE, 'w') as f:
        json.dump(links, f, indent=2)

@app.route('/')
def admin_panel():
    links = load_links()
    html = '''
    <h1>Panel admina - ustaw linki dla telewizorów</h1>
    <form method="POST" action="/update_links">
      {% for tv, url in links.items() %}
        <label>{{ tv }}:</label>
        <input type="text" name="{{ tv }}" value="{{ url }}" style="width: 400px"><br><br>
      {% endfor %}
      <button type="submit">Zapisz</button>
    </form>
    '''
    return render_template_string(html, links=links)

@app.route('/update_links', methods=['POST'])
def update_links():
    links = load_links()
    for tv in links.keys():
        new_url = request.form.get(tv)
        if new_url:
            links[tv] = new_url
    save_links(links)
    return 'Linki zostały zaktualizowane! <a href="/">Wróć do panelu admina</a>'

@app.route('/api/links')
def api_links():
    return jsonify(load_links())

@app.route('/proxy/<tv_id>')
def proxy(tv_id):
    snapshot_path = os.path.join(SNAPSHOT_DIR, f'{tv_id}.png')
    if not os.path.exists(snapshot_path):
        return f"Snapshot dla TV id '{tv_id}' nie istnieje", 404
    return send_file(snapshot_path, mimetype='image/png')

def take_snapshot(tv_id, url, driver):
    try:
        driver.get(url)
        time.sleep(5)
        driver.refresh()
        time.sleep(5)

        # Wymuś dokładnie 1920x1080 przez CDP
        driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
            "mobile": False,
            "width": 1920,
            "height": 1020,
            "deviceScaleFactor": 1,
        })
        time.sleep(3)  # chwila na przeskalowanie

        path = os.path.join(SNAPSHOT_DIR, f"{tv_id}.png")
        driver.save_screenshot(path)

        print(f"[{tv_id}] Snapshot zapisany w 1920x1080")
    except Exception as e:
        print(f"[{tv_id}] Błąd snapshotu: {e}")

def snapshot_worker():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_size(1920, 1080)

    while True:
        links = load_links()
        for tv_id, url in links.items():
            take_snapshot(tv_id, url, driver)
        time.sleep(30)  # snapshot co 30 sekund

if __name__ == '__main__':
    threading.Thread(target=snapshot_worker, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=True)