from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
app = Flask(__name__)
CORS(app)

'''
Tables for DB:
Devices
    mac_address (primary key)
    username (varchar)
    password (varchar)
    key (varchar)
Preferences
    mac_address (foreign key)
    preferences (json)
'''

@app.route('/register', methods=['POST'])
def registerDevice():
    data = request.get_json()
    mac_address = data['macAddress']
    username = data['username']
    password = data['password']
    # Check mac address has not been used yet
    # Register MAC address with username and password
    # Send key to user's ESP32 - maybe via MQTT (don't worry about this right now)
    # Return success message
    print(f"Registering device with MAC address {mac_address} for user {username}")
    return jsonify(data)


@app.route('/validateKey', methods=['POST'])
def validateKey():
    data = request.get_json()
    mac_address = data['macAddress']
    key = data['key']
    # Check key against database and return username and password if valid
    # Call function to regenerate key
    return jsonify(data)

@app.route('/regenKey', methods=['GET'])
def regenKey():
    data = request.get_json()
    mac_address = data['macAddress']
    # Regenerate key, and store in database
    return jsonify(data)

@app.route('/retrievePreferences', methods=['GET'])
def retrievePreferences():
    data = request.get_json()
    mac_address = data['macAddress']
    # Retrieve preferences from database using mac_address
    return jsonify(data)


@app.route('/updatePreferences', methods=['POST'])
def updatePreferences():
    data = request.get_json()
    mac_address = data['macAddress']
    preferences = data['preferences']
    # Add preference to database using mac_address 
    return jsonify(data)


if __name__ == '__main__':
    connection = sqlite3.connect('backend/database.db') # Connect to database
    with open('backend/schema.sql') as f: # Read schema from file and make sure tables are created
        connection.executescript(f.read())
    connection.close()
    app.run(debug=True)
    
