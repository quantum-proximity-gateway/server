from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/register', methods=['POST'])
def registerDevice():
    data = request.get_json()
    print(data)
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
