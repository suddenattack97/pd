from flask import Flask, render_template, jsonify, Response
import sqlite3
import json
import time

app = Flask(__name__)

DATABASE = 'danggn.db'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stream')
def stream():
    def event_stream():
        while True:
            conn = sqlite3.connect(DATABASE)
            cur = conn.cursor()

            cur.execute('SELECT * FROM item_view order by reg_date desc limit 35')
            items = cur.fetchall()

            cur.close()
            conn.close()

            data = json.dumps({'items': items})
            yield f"data: {data}\n\n"

            time.sleep(3)

    return Response(event_stream(), content_type='text/event-stream')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6700)