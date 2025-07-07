from flask import Flask, request, jsonify, render_template_string, Response
import json
import os
import requests

app = Flask(__name__)

LINKS_FILE = 'tv_links.json'

if not os.path.exists(LINKS_FILE):
    default_links = {
        "tv1": "https://www.youtube.com",
        "tv2": "https://www.facebook.com",
        "tv3": "https://www.twitter.com",
        "tv4": "https://www.instagram.com",
        "tv5": "https://www.reddit.com",
        "tv6": "https://www.netflix.com"
    }
    with open(LINKS_FILE, 'w') as f:
        json.dump(default_links, f, indent=2)

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
    links = load_links()
    target_url = links.get(tv_id)
    if not target_url:
        return f"TV id '{tv_id}' not found", 404

    try:
        resp = requests.get(target_url, timeout=10)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        return f"Error fetching {target_url}: {e}", 500

    excluded_headers = [
        'content-encoding',
        'content-length',
        'transfer-encoding',
        'connection',
        'x-frame-options',
        'content-security-policy'
    ]

    headers = [(name, value) for (name, value) in resp.headers.items()
               if name.lower() not in excluded_headers]

    return Response(resp.content, resp.status_code, headers)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)