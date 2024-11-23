import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/debug_env", methods=["GET"])
def debug_env():
    return jsonify({
        "TELEGRAM_TOKEN": os.getenv("TELEGRAM_TOKEN"),
        "WEBHOOK_URL": os.getenv("WEBHOOK_URL"),
        "STRAVA_CLIENT_ID": os.getenv("STRAVA_CLIENT_ID"),
        "STRAVA_CLIENT_SECRET": os.getenv("STRAVA_CLIENT_SECRET"),
        "PORT": os.getenv("PORT")
    })

if __name__ == "__main__":
    PORT = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=PORT)
