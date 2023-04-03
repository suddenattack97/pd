from flask import Flask, render_template, jsonify, Response
import sqlite3
import json
import time
import requests

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

            cur.execute('SELECT * FROM item_view order by reg_date desc limit 21')
            items = cur.fetchall()

            cur.close()
            conn.close()

            data = json.dumps({'items': items})
            yield f"data: {data}\n\n"

            time.sleep(5)

    return Response(event_stream(), content_type='text/event-stream')
    
@app.route('/mark_as_read/<int:item_id>', methods=['POST'])
def mark_as_read(item_id):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()

    cur.execute('UPDATE item_view SET read = 1 WHERE item_id = ?', (item_id,))
    conn.commit()

    cur.close()
    conn.close()

    return '', 204




@app.route('/updates/<string:item_id>', methods=['POST'])
def updates(item_id):
    # 여기에서 필요한 처리를 수행합니다.
    response_url = "https://api.kr.karrotmarket.com/webapp/api/v24/articles/"+item_id+".json?feed_visible=1&include=is_watched_by_me"
    response_headers = {
        'x-user-agent' : 'TowneersApp/23.5.1/230501 iOS/16.3.0/1953.3 iPhone15,2',
        'accept' : '*/*',
        'x-country-code' : 'KR',
        'x-karrot-api-content-sha256' : '47DEQpj8HBSa+/TImW+5JCeuQeRkm5NMpJWZG3hSuFU=',
        'x-karrot-api-signature-v1' : '39e8308e12c9f83c8878ec3e83ec1876fd82937b6c63bee89cce6fba8056b636',
        'accept-language' : 'ko-KR',
        'x-karrot-api-timestamp' : '1678329469729',
        'accept-encoding' : 'br;q=1.0, gzip;q=0.9, deflate;q=0.8',
        'user-agent' : 'Karrot/23.5.1 (com.towneers.www; build:1; iOS 16.3.0) Alamofire/5.6.1',
        'x-auth-token' : '943ce001830d26c08f8a6262393d38179bd8d5f3a93076ee24754096db15cf55',
        'cookie' : '_hoian-webapp_session=KiZUuJQ1DyqBOnhPosQ0A3cBo1sduE9maOeYBJ835yHY7xLTZXVP49g4i%2FI0Ch%2FXlEzfMBQ2X2bP8E3IkQGeRhi5OG7w2CrF7C4dkGwi7aK88V6f1OuAvNgWOup3OkkC4LlD1Lnq%2FzKbD%2BsusSQHeJ7B4FFFLF%2BOhdyrbYB%2FREPN7N2uJLRNglfHCes%2FhE6wsTSE2MCMphLymKh%2Fnm0%2BM0dtwM5P--EPbjhcBvMrCSPVIf--f5gvBpLSI3zZy0kqxsCjWQ%3D%3D'
        }
    response = requests.get(url=response_url, headers=response_headers)
    res_json = json.loads(response.text)

    # 원하는 결과를 JSON 형식으로 반환합니다.
    return jsonify(res_json)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6700)