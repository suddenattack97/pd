from flask import Flask, render_template, jsonify, Response
from flask import request, redirect, url_for, session
from datetime import datetime
import sqlite3
import json
import time
import requests
import logging

app = Flask(__name__)

# 상단에 추가
app.logger.disabled = True
log = logging.getLogger('werkzeug')
log.disabled = True

def log_client_ip(response):
    client_ip = request.remote_addr
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{current_time} - Client IP: {client_ip}")
    return response

# 요청 완료 후 실행되도록 함수 등록
app.after_request(log_client_ip)


DATABASE = 'danggn.db'


# 상단에 추가
app.secret_key = 'minsu'


# 기존 index() 함수 대신 아래의 인증 관련 함수 추가
@app.route('/', methods=['GET', 'POST'])
def auth():
    if request.method == 'POST':
        password = request.form['password']
        if password == app.secret_key:
            session['authenticated'] = True
            return redirect(url_for('index'))
        else:
            return render_template('invalid_password.html'), 401

    if 'authenticated' in session:
        return redirect(url_for('index'))
    return render_template('auth.html')

@app.route('/invalidate_session', methods=['POST'])
def invalidate_session():
    session.clear()
    return '', 204

@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    return redirect(url_for('auth'))

# index() 함수에 로그인 상태 확인 추가
@app.route('/main')
def index():
    if 'authenticated' not in session:
        return redirect(url_for('auth'))
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
        'x-user-agent' : 'TowneersApp/23.2.2/230202 iOS/16.2.0/1953.3 iPhone14,2',
        'accept' : '*/*',
        'x-country-code' : 'KR',
        'x-karrot-api-content-sha256' : '47DEQpj8HBSa+/TImW+5JCeuQeRkm5NMpJWZG3hSuFU=',
        'x-karrot-api-signature-v1' : 'c8455d1f9261ec307a93e2e467c9234ba9ad6388285352c316638763b9f627f2',
        'accept-language' : 'ko-KR',
        'x-karrot-api-timestamp' : '1680497117015',
        'accept-encoding' : 'br;q=1.0, gzip;q=0.9, deflate;q=0.8',
        'user-agent' : 'Karrot/23.2.2 (com.towneers.www; build:0; iOS 16.2.0) Alamofire/5.6.1',
        'X-Auth-Token' : '79771223201a41e4fbffde341db55f48',
        'Cookie' : '_hoian-webapp_session=kYFv3tqPpqth0Pv%2FlWOaHLZK8QHgZhCkzHkazhOl2sbVng%2BGLjDP04G1Ug85ujNwx0YlHczC0i%2BryzC8S2pfUWkxj9t%2B7vEm%2F17HbNhqXxt6wgVQmNxu3u4c8LXS32l7WQ0ScYkdFc%2FeH3cnAuJE8g3UL5BNZPnOSSvau0cCccxsHyVzu0MTN5CEmLq0%2FQYMr2TV9Nh0VUiz%2BYh2ROlMOM7RQwHJ--%2BSohH2xPwOfCWUPq--iXId19Ku%2F8TIRv0s79p0hA%3D%3D'
        }
    response = requests.get(url=response_url, headers=response_headers)
    res_json = json.loads(response.text)

    # 원하는 결과를 JSON 형식으로 반환합니다.
    return jsonify(res_json)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6700)