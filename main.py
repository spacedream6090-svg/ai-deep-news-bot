import feedparser
import os
import requests
import re
import json
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
from html import unescape

load_dotenv()

# ===== 設定 =====
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
USER_ID = os.getenv("LINE_USER_ID")

client = OpenAI(api_key=OPENAI_API_KEY)

RSS_FEEDS = [
    "https://hnrss.org/frontpage",
    "https://www.reddit.com/r/MachineLearning/.rss"
]

MAX_ARTICLES_PER_FEED = 5
SEEN_FILE = "seen.json"


# ===== ユーティリティ =====
def log(msg):
    print(f"[LOG] {msg}")


def clean_html(text):
    text = re.sub(r"<.*?>", "", text)
    return unescape(text)


def load_seen():
    if not os.path.exists(SEEN_FILE):
        return set()
    with open(SEEN_FILE, "r") as f:
        return set(json.load(f))


def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)


# ===== 記事取得 =====
def fetch_articles():
    articles = []

    for url in RSS_FEEDS:
        feed = feedparser.parse(url)

        if getattr(feed, "bozo", False):
            log(f"RSS異常: {url}")

        for entry in feed.entries[:MAX_ARTICLES_PER_FEED]:
            title = clean_html(entry.get("title", "").strip())
            summary = clean_html(entry.get("summary", "").strip())
            link = entry.get("link", "").strip()

            if not title:
                continue

            articles.append({
                "title": title,
                "summary": summary[:300],
                "link": link
            })

    return articles


# ===== 重複除去 =====
def deduplicate(articles):
    seen = set()
    unique = []

    for a in articles:
        key = re.sub(r"\W+", "", a["title"].lower())

        if key not in seen:
            seen.add(key)
            unique.append(a)

    return unique


# ===== 軽量スコアリング =====
def score_articles(articles):
    keywords = ["AI", "model", "GPT", "research", "openai"]

    def score(a):
        return sum(k.lower() in a["title"].lower() for k in keywords)

    return sorted(articles, key=score, reverse=True)[:5]


# ===== LLM選定（JSON強制） =====
def select_top_articles(articles):
    text = "\n\n".join(
        [f"{i+1}. {a['title']}\n{a['summary']}" for i, a in enumerate(articles)]
    )

    prompt = f"""
次のニュースから重要度上位3件を選べ。

JSON形式で出力：
{{ "indices": [1,2,3] }}

ニュース：
{text}
"""

    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "厳密にJSONで答えよ"},
                {"role": "user", "content": prompt}
            ]
        )

        content = res.choices[0].message.content or ""
        data = json.loads(content)

        indices = data.get("indices", [])

        return [articles[i-1] for i in indices if 0 < i <= len(articles)]

    except Exception as e:
        log(f"選定失敗: {e}")
        return articles[:3]


# ===== MapReduce要約 =====
def summarize(articles):
    summaries = []

    # Map
    for a in articles:
        prompt = f"""
以下を1文で要約：
{a['title']}
{a['summary']}
"""
        try:
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            summaries.append(res.choices[0].message.content.strip())
        except:
            continue

    # Reduce
    combined = "\n".join(summaries)

    final_prompt = f"""
以下を統合して深く解説せよ：

{combined}
"""

    try:
        res = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": final_prompt}]
        )
        return res.choices[0].message.content.strip()

    except:
        return "要約失敗"


# ===== LINE送信 =====
def send_line(text):
    url = "https://api.line.me/v2/bot/message/push"

    headers = {
        "Authorization": f"Bearer {LINE_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "to": USER_ID,
        "messages": [{"type": "text", "text": text[:5000]}]
    }

    try:
        res = requests.post(url, headers=headers, json=data, timeout=10)
        log(f"LINE: {res.status_code}")
    except Exception as e:
        log(f"LINE失敗: {e}")


# ===== メイン =====
def main():
    seen_links = load_seen()

    articles = fetch_articles()
    articles = [a for a in articles if a["link"] not in seen_links]

    if not articles:
        send_line("新着ニュースなし")
        return

    articles = deduplicate(articles)
    articles = score_articles(articles)

    selected = select_top_articles(articles)

    summary = summarize(selected)

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    message = f"""🧠 AI Deep News

{now}

{summary}
"""

    send_line(message)

    for a in articles:
        seen_links.add(a["link"])

    save_seen(seen_links)


if __name__ == "__main__":
    main()
