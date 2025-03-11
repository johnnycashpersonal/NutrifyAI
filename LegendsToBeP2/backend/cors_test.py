from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # <-- the simplest usage

@app.route("/test", methods=["GET", "POST", "OPTIONS"])
def test():
    return jsonify({"message": "CORS test endpoint"}), 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)
