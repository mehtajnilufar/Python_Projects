from flask import Flask, request, jsonify
import sqlite3
import string, random, datetime
from user_agents import parse
from openai import OpenAI

app = Flask(__name__)

# DB setup
conn = sqlite3.connect('urls.db', check_same_thread=False)
cur = conn.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS urls(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_url TEXT,
    short_code TEXT,
    clicks INTEGER,
    last_clicked TEXT,
    last_ip TEXT,
    last_browser TEXT
)""")

client = OpenAI(api_key="YOUR_OPENAI_API_KEY")

def generate_ai_keyword(url):
    prompt = f"Generate a short, creative keyword for this link: {url}"
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=8
    )
    return response.choices[0].message.content.strip().replace(" ", "-")

def generate_random_code():
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))

@app.route('/shorten', methods=['POST'])
def shorten():
    data = request.get_json()
    url = data.get('url')
    use_ai = data.get('use_ai', False)

    if use_ai:
        code = generate_ai_keyword(url)
    else:
        code = generate_random_code()

    cur.execute(
        "INSERT INTO urls (original_url, short_code, clicks, last_clicked, last_ip, last_browser) VALUES (?, ?, ?, ?, ?, ?)",
        (url, code, 0, None, None, None)
    )
    conn.commit()

    return jsonify({"short_url": f"http://localhost:5000/{code}"})

@app.route('/<code>', methods=['GET'])
def redirect_to(code):
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    browser = parse(user_agent).browser.family

    cur.execute("SELECT original_url, clicks FROM urls WHERE short_code=?", (code,))
    result = cur.fetchone()

    if not result:
        return jsonify({"error": "URL not found"}), 404

    original_url, clicks = result

    cur.execute("UPDATE urls SET clicks=?, last_clicked=?, last_ip=?, last_browser=? WHERE short_code=?",
                (clicks+1, str(datetime.datetime.now()), ip, browser, code))
    conn.commit()

    return jsonify({"redirect_to": original_url})

@app.route('/analytics/<code>', methods=['GET'])
def analytics(code):
    cur.execute("SELECT clicks, last_clicked, last_ip, last_browser FROM urls WHERE short_code=?", (code,))
    result = cur.fetchone()

    if not result:
        return jsonify({"error": "No analytics found"}), 404

    return jsonify({
        "total_clicks": result[0],
        "last_clicked": result[1],
        "last_ip": result[2],
        "last_browser": result[3]
    })

if __name__ == '__main__':
    app.run(debug=True)
