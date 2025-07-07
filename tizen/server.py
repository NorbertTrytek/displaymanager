from flask import Flask, request, Response
import requests

app = Flask(__name__)

@app.route('/proxy')
def proxy():
    target_url = request.args.get('url')
    if not target_url:
        return "Brak parametru url", 400

    try:
        # Pobierz zawartość strony
        resp = requests.get(target_url, timeout=10)

        # Zwróć odpowiedź, przekazując nagłówki content-type itp.
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items()
                   if name.lower() not in excluded_headers]

        return Response(resp.content, resp.status_code, headers)
    except Exception as e:
        return f"Błąd proxy: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)