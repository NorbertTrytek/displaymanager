import threading
from app import app, snapshot_worker

if __name__ == '__main__':
    # Start the snapshot worker in a background thread
    threading.Thread(target=snapshot_worker, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=True)