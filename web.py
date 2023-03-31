from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

# SQLite3 데이터베이스 파일 경로
DATABASE = 'danggn.db'

@app.route('/')
def index():
    # 데이터베이스 연결
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()

    # 아이템 목록 가져오기
    cur.execute('SELECT * FROM item_view order by reg_date desc limit 35')
    items = cur.fetchall()

    # 데이터베이스 연결 종료
    cur.close()
    conn.close()

    # 템플릿 파일 렌더링
    return render_template('index.html', items=items)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6700)