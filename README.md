AI Deep News Bot

概要

AI・テック分野の「ディープなニュース」を収集し、
LLMによって統合・要約してLINEに配信するボット。

単なるニュース要約ではなく、
「技術的に重要な流れ」と「今後の影響」にフォーカスする。

⸻

特徴
	•	X（Twitter）インフルエンサーを中心とした情報収集
	•	社会的インパクトに基づくTop3選定
	•	エンジニア向けの深い要約生成
	•	LINEへの自動配信

⸻

技術スタック
	•	Python
	•	OpenAI API
	•	LINE Messaging API
	•	RSS / RSSHub

セットアップ方法

1. リポジトリをクローン
git clone https://github.com/yourname/ai-deep-news-bot.git
cd ai-deep-news-bot
2. 環境変数設定
.envファイルを作成し、以下を記入
OPENAI_API_KEY=your_key
LINE_CHANNEL_ACCESS_TOKEN=your_token
LINE_USER_ID=your_user_id
3. ライブラリインストール
pip install -r requirements.txt
4. 実行
python main.py

今後の改善
	•	ユーザーごとのパーソナライズ
	•	インフルエンサーリストの拡張
	•	記事本文取得による精度向上
	•	定期実行（cron / cloud scheduler）

⸻

注意
	•	RSSHubの可用性に依存します
	•	OpenAI APIの利用料金が発生します
