import feedparser
import os
import requests
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
USER_ID = os.getenv("LINE_USER_ID")

RSS_FEEDS = [
    "https://hnrss.org/frontpage",
    "https://www.reddit.com/r/MachineLearning/.rss",
    "https://rsshub.app/twitter/user/karpathy",
    "https://rsshub.app/twitter/user/sama"
]

def fetch_articles():
    articles = []
    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:
            articles.append({
                "title": entry.title,
                "summary": entry.get("summary", ""),
                "link": entry.link
            })
    return articles

def select_top_articles(articles):
    text = "\n\n".join(
        [f"{i}. {a['title']}\n{a['summary']}" for i, a in enumerate(articles)]
    )

    prompt = f"""
以下のニュースから社会的インパクトが最も大きい上位3つを選べ。

評価基準：
- 技術的ブレークスルー
- 社会への影響
- 将来性

出力形式：
番号のみ（例: 1,4,7）

ニュース：
{text}
"""

    res = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    indices = res.choices[0].message.content.strip()
    indices = [int(i) for i in indices.replace(" ", "").split(",")]

    return [articles[i] for i in indices if i < len(articles)]

def summarize(articles):
    text = "\n\n".join(
        [f"{a['title']}\n{a['summary']}" for a in articles]
    )

    prompt = f"""
あなたはAI研究者。

以下のニュースを統合して、
エンジニア向けに深くまとめよ。

条件：
- 表面的な説明は禁止
- 技術の本質
- なぜ重要か
- 今後の影響

ニュース：
{text}
"""

    res = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return res.choices[0].message.content

def send_line(text):
    url = "https://api.line.me/v2/bot/message/push"

    headers = {
        "Authorization": f"Bearer {LINE_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "to": USER_ID,
        "messages": [{"type": "text", "text": text}]
    }

    requests.post(url, headers=headers, json=data)

def main():
    articles = fetch_articles()

    if not articles:
        send_line("ニュース取得に失敗しました")
        return

    top_articles = select_top_articles(articles)
    summary = summarize(top_articles)

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    message = f"""🧠 AI Deep News

{now}

{summary}
"""

    send_line(message)

if __name__ == "__main__":
    main()
