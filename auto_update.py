"""
AI活用ログ 自動更新スクリプト
-----------------------------------
1. カテゴリごとに設定したRSS/ニュース検索フィードから新着記事を取得
2. フィードの概要文を整形して「簡易要約」として使用（無料・APIキー不要）
3. articles.json に重複なく追記
4. Gitリポジトリであれば自動で commit & push

必要なパッケージ: feedparser （setup.bat で自動インストールされます）
"""
import json
import os
import re
import sys
import hashlib
import subprocess
from datetime import datetime, timedelta
from urllib.parse import quote

try:
    import feedparser
except ImportError:
    print("feedparser がインストールされていません。先に setup.bat を実行してください。")
    sys.exit(1)

# ============================================================
# 設定
# ============================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ARTICLES_PATH = os.path.join(SCRIPT_DIR, "articles.json")


def google_news_search(query):
    """Googleニュースの検索結果をRSSとして取得するURLを作る（リンクはGoogle経由になります）"""
    return f"https://news.google.com/rss/search?q={quote(query)}&hl=ja&gl=JP&ceid=JP:ja"


# カテゴリごとの取得元。直接サイトのRSSがある場合はそちらを優先し、
# Googleニュース検索フィードを補助として使っています。
# サイトのRSS URLは変更されることがあるので、取得が止まったらここを見直してください。
FEEDS = {
    "AI": [
        "https://rss.itmedia.co.jp/rss/2.0/aiplus.xml",
        google_news_search("生成AI"),
    ],
    "副業": [
        google_news_search("副業 AI活用"),
    ],
    "株": [
        google_news_search("株式投資"),
    ],
    "整理術": [
        "https://www.lifehacker.jp/feed/index.xml",
        google_news_search("整理術"),
    ],
}

MAX_PER_FEED = 3        # 1フィードから取得する最大件数
MAX_AGE_DAYS = 3        # これより古い記事は無視
MAX_NEW_PER_RUN = 12     # 1回の実行で追加する記事数の上限
MAX_EXCERPT_LEN = 120    # 要約の最大文字数

# 自動取得記事のデフォルト値（難易度・収益性は自動判定していません）
DEFAULT_DIFFICULTY = 1
DEFAULT_PROFIT = 1
DEFAULT_TIME = "3分で読了"


# ============================================================
# ユーティリティ
# ============================================================
def strip_html(text):
    text = re.sub(r"<[^>]+>", "", text or "")
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&quot;", '"')
    return re.sub(r"\s+", " ", text).strip()


def make_excerpt(entry):
    """フィードの概要文を整形して『簡易要約』として使う（AI要約ではなく機械的な整形・短縮）"""
    raw = getattr(entry, "summary", "") or getattr(entry, "description", "") or getattr(entry, "title", "")
    text = strip_html(raw)
    if len(text) > MAX_EXCERPT_LEN:
        text = text[:MAX_EXCERPT_LEN].rstrip() + "…"
    return text


def make_id(url):
    return hashlib.md5(url.encode("utf-8")).hexdigest()[:10]


def parse_date(entry):
    for key in ("published_parsed", "updated_parsed"):
        t = getattr(entry, key, None)
        if t:
            try:
                return datetime(*t[:6])
            except Exception:
                pass
    return datetime.now()


def load_articles():
    if not os.path.exists(ARTICLES_PATH):
        return []
    try:
        with open(ARTICLES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"[警告] articles.json の読み込みに失敗しました: {e}")
        print("ファイルが壊れている可能性があります。手動で確認してください。")
        sys.exit(1)


def save_articles(articles):
    with open(ARTICLES_PATH, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)


# ============================================================
# 記事取得
# ============================================================
def fetch_new_articles(existing_urls):
    cutoff = datetime.now() - timedelta(days=MAX_AGE_DAYS)
    new_articles = []

    for category, feed_urls in FEEDS.items():
        for feed_url in feed_urls:
            try:
                parsed = feedparser.parse(feed_url)
            except Exception as e:
                print(f"  [警告] フィード取得エラー（{category}）: {e}")
                continue

            if parsed.bozo and not parsed.entries:
                print(f"  [警告] フィードを解析できませんでした（{category}）: {feed_url}")
                continue

            count = 0
            for entry in parsed.entries:
                if count >= MAX_PER_FEED:
                    break
                url = getattr(entry, "link", "")
                title = strip_html(getattr(entry, "title", ""))
                if not url or not title or url in existing_urls:
                    continue

                pub_date = parse_date(entry)
                if pub_date < cutoff:
                    continue

                article = {
                    "id": make_id(url),
                    "date": pub_date.strftime("%Y-%m-%d"),
                    "category": category,
                    "title": title,
                    "excerpt": make_excerpt(entry),
                    "difficulty": DEFAULT_DIFFICULTY,
                    "profit": DEFAULT_PROFIT,
                    "time": DEFAULT_TIME,
                    "views": 0,
                    "url": url,
                }
                new_articles.append(article)
                existing_urls.add(url)
                count += 1

    return new_articles[:MAX_NEW_PER_RUN]


# ============================================================
# Git連携
# ============================================================
def run_git(args):
    return subprocess.run(["git"] + args, cwd=SCRIPT_DIR, capture_output=True, text=True)


def push_to_github(added_count):
    if not os.path.isdir(os.path.join(SCRIPT_DIR, ".git")):
        print("\n[GitHub] このフォルダはまだGitリポジトリではありません。初回のみ以下を実行してください:")
        print("  git init")
        print("  git add .")
        print('  git commit -m "first commit"')
        print("  git branch -M main")
        print("  git remote add origin <あなたのGitHubリポジトリのURL>")
        print("  git push -u origin main")
        print("次回の実行から自動でcommit・pushされるようになります。")
        return

    run_git(["add", "articles.json"])
    diff = run_git(["diff", "--cached", "--quiet"])
    if diff.returncode == 0:
        print("[GitHub] 変更なし。コミットは行いません。")
        return

    date_str = datetime.now().strftime("%Y-%m-%d")
    commit = run_git(["commit", "-m", f"記事を自動追加 ({added_count}件) {date_str}"])
    if commit.returncode != 0:
        print("[GitHub] コミットに失敗しました:")
        print(commit.stderr.strip())
        return

    push = run_git(["push"])
    if push.returncode != 0:
        print("[GitHub] プッシュに失敗しました（ログイン設定や接続をご確認ください）:")
        print(push.stderr.strip())
        return

    print(f"[GitHub] 反映しました（{added_count}件追加, {date_str}）")


# ============================================================
# メイン処理
# ============================================================
def main():
    print("=" * 50)
    print(f"AI活用ログ 自動更新  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)

    articles = load_articles()
    existing_urls = {a.get("url") for a in articles if a.get("url")}

    print("記事を取得しています...")
    new_articles = fetch_new_articles(existing_urls)

    if not new_articles:
        print("新しい記事はありませんでした。")
        return

    articles = new_articles + articles
    save_articles(articles)

    print(f"\n{len(new_articles)} 件の記事を追加しました:")
    for a in new_articles:
        print(f"  [{a['category']}] {a['title']}")

    try:
        push_to_github(len(new_articles))
    except FileNotFoundError:
        print("\n[GitHub] git コマンドが見つかりません。Git for Windows をインストールしてください。")
        print("https://gitforwindows.org/")
    except Exception as e:
        print(f"\n[GitHub] 予期しないエラー: {e}")

    print("\n完了しました。")


if __name__ == "__main__":
    main()
