from flask import Flask, render_template, jsonify, Response
from flask import request, redirect, url_for, session, send_file
from datetime import datetime
import sqlite3
import json
import time
import requests
import logging
import qrcode
from io import BytesIO

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


@app.route('/generate_qr_code/<path:url>', methods=['GET'])
def generate_qr_code(url):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data("https://www.daangn.com/articles/"+url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/png')

@app.route('/url/<string:item_id>', methods=['POST'])
def url(item_id):
    # 여기에서 필요한 처리를 수행합니다.
    data = {
        "content": {
            "action": {
                "type": "LINK",
                "value": "https://www.daangn.com/articles/"+item_id
            },
            "description": "네이버앱에서 웹페이지를 확인하실 수 있습니다.",
            "title": "PC 웨일에서 웹페이지가 전송되었습니다."
        },
        "pushDevice": {
            "appId": "APG00012",
            "deviceType": "apns",
            "duId": "dc5b1455a1af44f20e545236b4d3cb09"
        }
    }
    response_url = "http://apis.naver.com/whale/tube_api/push?msgpad=1680593278015&md=k4kNp8QufgrL%2FOnMC5yRkT6kftk%3D"
    response_headers = {
        'x-user-agent' : 'TowneersApp/23.2.2/230202 iOS/16.2.0/1953.3 iPhone14,2',
        'accept' : '*/*',
        'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Whale/3.19.166.16 Safari/537.36',
        'Accept-Encoding' : 'gzip, deflate',
        'accept-language' : 'ko-KR',
        'Content-Type' : 'application/json',
        'Cookie' : 'NID_AUT=kCCZsVklch86Rbo3dKubNw7+YRaom9lBK6FYYdXltQcmzD1TO9J6mUBD6eHrnEGU;NID_JKL=fW2EpfuB+ei2aWvU4sQyhcdD3R1+WqQGRxBNgECLlk4=;NID_SES=AAABw7EDlSVps+1gSfC/xlq8pbny1Sno99+ZcixNzXC7dor4t7dyTjj2KiQUfAqV3BlxOlhezciESH1wgefwJC4pEGK6KC2EJlfxmV0wyWHGuA2wegC0mylVW8XdY0AUKUYt+f0IoT84pS6q2Ion0yRL2LLLG4S1DHFpa5DICmDLt/JcEdFqkWWg8ie2NcHMwmz+mW96lnxWLz2PvgYSOwOHJNGpw3RRs7KQn5RDWXl16tE+g50PocZUrDabYqugzxlYhA030eDMPQ3paVNxMF5mXaWJlHG+GDzdgTywQ7AT5MYhZirVFHTaqUCGMPJhciGhgr3SjsrdszKAGHtcn1AXRqk3oeUd3SHwFzzT0afAIdnooeZ25ELXMBvKFg0f0g2xia7MyejTCZ/NdIYH1EefRi+3fqDgWiL01y2cBt79ghdzMA0pMOqnBR0HqKQnD6xABEoXNLl8Y3HpRCCx9erkyBZLXEqz93CMGkflRDIcXeVcrA5nVxhVPBPCIZJkCXobT1Yvro69kEWQkdomFJPU0J082DbFk21NYVUEOJYjriRbGrKwek83hZ4qv9jrOtYpOFbfcjw0Q66vnoI3pxT2SsRbJXBjQqjqsLmyIWBc4NaO;'
        }
    response = requests.post(url=response_url, headers=response_headers, json=data)
    
    res_json = json.loads(response.text)
    # 원하는 결과를 JSON 형식으로 반환합니다.
    return jsonify(res_json)


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