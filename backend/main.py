from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/register', methods=['POST'])
def registerDevice():
    data = request.get_json()
    mac_address = data['macAddress']
    username = data['username']
    password = data['password']
    print(f"Registering device with MAC address {mac_address} for user {username}")
    return jsonify(data)


@app.route('/validateKey', methods=['POST'])
def validateKey():
    data = request.get_json()
    mac_address = data['macAddress']
    key = data['key']
    # validate key here
    return jsonify(data)

@app.route('/regenKey', methods=['GET'])
def regenKey():
    data = request.get_json()
    mac_address = data['macAddress']
    # regen key here
    return jsonify(data)




if __name__ == '__main__':
    app.run(debug=True)
