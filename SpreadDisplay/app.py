import os
import json
import threading
import time
from flask import Flask, request, jsonify, render_template, send_file, flash, redirect, url_for
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key_for_dev")

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

def is_valid_url(url):
    """Podstawowa walidacja URL"""
    return url.startswith(('http://', 'https://')) and len(url) > 10

@app.route('/')
def admin_panel():
    """Panel administracyjny z nowoczesnym interfejsem"""
    links = load_links()
    return render_template('admin.html', links=links)

@app.route('/update_links', methods=['POST'])
def update_links():
    """Aktualizacja linków z walidacją"""
    links = load_links()
    updated_count = 0
    
    for tv in links.keys():
        new_url = request.form.get(tv)
        if new_url and new_url != links[tv]:
            if is_valid_url(new_url):
                links[tv] = new_url
                updated_count += 1
            else:
                flash(f'Nieprawidłowy URL dla {tv}: {new_url}', 'error')
                return redirect(url_for('admin_panel'))
    
    save_links(links)
    
    if updated_count > 0:
        flash(f'Pomyślnie zaktualizowano {updated_count} linków!', 'success')
    else:
        flash('Nie dokonano żadnych zmian.', 'info')
    
    return redirect(url_for('admin_panel'))

@app.route('/rename_monitor', methods=['POST'])
def rename_monitor():
    """Zmiana nazwy monitora"""
    data = request.get_json()
    old_name = data.get('old_name')
    new_name = data.get('new_name')
    
    if not old_name or not new_name:
        return jsonify({'success': False, 'message': 'Brak wymaganych danych'})
    
    if old_name == new_name:
        return jsonify({'success': False, 'message': 'Nowa nazwa jest taka sama jak stara'})
    
    links = load_links()
    
    if old_name not in links:
        return jsonify({'success': False, 'message': 'Monitor o tej nazwie nie istnieje'})
    
    if new_name in links:
        return jsonify({'success': False, 'message': 'Monitor o tej nazwie już istnieje'})
    
    # Przemianuj monitor
    links[new_name] = links[old_name]
    del links[old_name]
    save_links(links)
    
    # Przemianuj plik snapshot jeśli istnieje
    old_snapshot = os.path.join(SNAPSHOT_DIR, f'{old_name}.png')
    new_snapshot = os.path.join(SNAPSHOT_DIR, f'{new_name}.png')
    
    if os.path.exists(old_snapshot):
        os.rename(old_snapshot, new_snapshot)
    
    return jsonify({'success': True, 'message': f'Monitor "{old_name}" został przemianowany na "{new_name}"'})

@app.route('/add_monitor', methods=['POST'])
def add_monitor():
    """Dodanie nowego monitora"""
    data = request.get_json()
    monitor_name = data.get('name')
    monitor_url = data.get('url', 'https://www.example.com')
    
    if not monitor_name:
        return jsonify({'success': False, 'message': 'Nazwa monitora jest wymagana'})
    
    links = load_links()
    
    if monitor_name in links:
        return jsonify({'success': False, 'message': 'Monitor o tej nazwie już istnieje'})
    
    if not is_valid_url(monitor_url):
        return jsonify({'success': False, 'message': 'Nieprawidłowy format URL'})
    
    links[monitor_name] = monitor_url
    save_links(links)
    
    return jsonify({'success': True, 'message': f'Monitor "{monitor_name}" został dodany'})

@app.route('/delete_monitor', methods=['POST'])
def delete_monitor():
    """Usunięcie monitora"""
    data = request.get_json()
    monitor_name = data.get('name')
    
    if not monitor_name:
        return jsonify({'success': False, 'message': 'Nazwa monitora jest wymagana'})
    
    links = load_links()
    
    if monitor_name not in links:
        return jsonify({'success': False, 'message': 'Monitor o tej nazwie nie istnieje'})
    
    if len(links) <= 1:
        return jsonify({'success': False, 'message': 'Nie można usunąć ostatniego monitora'})
    
    del links[monitor_name]
    save_links(links)
    
    # Usuń plik snapshot jeśli istnieje
    snapshot_path = os.path.join(SNAPSHOT_DIR, f'{monitor_name}.png')
    if os.path.exists(snapshot_path):
        os.remove(snapshot_path)
    
    return jsonify({'success': True, 'message': f'Monitor "{monitor_name}" został usunięty'})

@app.route('/reset_links', methods=['POST'])
def reset_links():
    """Resetowanie linków do wartości domyślnych"""
    default_links = {
        "tv1": "https://www.example.com",
        "tv2": "https://www.example.com", 
        "tv3": "https://www.example.com",
        "tv4": "https://www.example.com",
        "tv5": "https://www.example.com",
        "tv6": "https://www.example.com"
    }
    save_links(default_links)
    flash('Linki zostały zresetowane do wartości domyślnych!', 'warning')
    return redirect(url_for('admin_panel'))

@app.route('/api/links')
def api_links():
    """API endpoint dla linków"""
    return jsonify(load_links())

@app.route('/api/validate_url', methods=['POST'])
def validate_url():
    """API endpoint do walidacji URL"""
    data = request.get_json()
    url = data.get('url', '')
    
    if is_valid_url(url):
        return jsonify({'valid': True, 'message': 'URL jest prawidłowy'})
    else:
        return jsonify({'valid': False, 'message': 'Nieprawidłowy format URL'})

@app.route('/proxy/<tv_id>')
def proxy(tv_id):
    """Proxy dla obrazków snapshot"""
    snapshot_path = os.path.join(SNAPSHOT_DIR, f'{tv_id}.png')
    if not os.path.exists(snapshot_path):
        return f"Snapshot dla TV id '{tv_id}' nie istnieje", 404
    return send_file(snapshot_path, mimetype='image/png')

def take_snapshot(tv_id, url, driver):
    """Robienie snapshot strony"""
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
    """Worker do robienia snapshot w tle"""
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

# Main application entry point is now in main.py
