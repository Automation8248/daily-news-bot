import os
import requests
import feedparser
from difflib import SequenceMatcher
from newspaper import Article
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# --- 1. CONFIGURATION ---
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")
BLOGGER_ID = os.getenv("BLOGGER_BLOG_ID")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- MASTER LABEL LIST ---
Existing_Labels_DB = [
    "AI Models", "AI News", "AI Updates", 
    "Cloud Computing", "Digital Innovation", 
    "Global Tech News", "Google News", "India Tech News", 
    "OpenAI News", "Smart Technology", "Software Updates", 
    "Tech Updates", "Technology News"
]

def get_blogger_service():
    creds = Credentials(
        None, refresh_token=REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID, client_secret=CLIENT_SECRET
    )
    return build('blogger', 'v3', credentials=creds, static_discovery=False)

def is_similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() > 0.6

# --- 2. SMART LABEL SYSTEM ---
def get_smart_labels(topic):
    topic_lower = topic.lower()
    temp_labels = set()
    
    if any(k in topic_lower for k in ["tech", "gadget", "device"]): temp_labels.add("Technology News")
    if any(k in topic_lower for k in ["ai", "artificial intelligence"]): temp_labels.update(["AI News", "AI Models"])
    if "google" in topic_lower: temp_labels.add("Google News")
    if "cloud" in topic_lower: temp_labels.add("Cloud Computing")
    if "software" in topic_lower or "update" in topic_lower: temp_labels.add("Software Updates")
    if "openai" in topic_lower or "chatgpt" in topic_lower: temp_labels.add("OpenAI News")
    if "india" in topic_lower: temp_labels.add("India Tech News")
    if "global" in topic_lower or "world" in topic_lower: temp_labels.add("Global Tech News")
    if "innovation" in topic_lower or "future" in topic_lower: temp_labels.add("Digital Innovation")

    final_labels = [lbl for lbl in temp_labels if lbl in Existing_Labels_DB]
    return final_labels[:4] if final_labels else ["Technology News"]

# --- 3. FETCH ORIGINAL ARTICLE & IMAGE (WITH 5-DAY FALLBACK LOGIC) ---
def fetch_and_extract_news(service):
    # Purane posts ke titles fetch karte hain duplicate rokne ke liye
    try:
        posts = service.posts().list(blogId=BLOGGER_ID, maxResults=20, fetchBodies=False).execute()
        existing_titles = [p['title'] for p in posts.get('items', [])]
    except Exception:
        existing_titles = []

    # Pehle 24h ki news check karega, agar fail hua to 5 days ki news check karega
    rss_feeds = [
        "https://news.google.com/rss/search?q=technology+when:24h&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=technology+when:5d&hl=en-US&gl=US&ceid=US:en"
    ]

    for feed_url in rss_feeds:
        timeframe = "24 Hours" if "when:24h" in feed_url else "5 Days"
        print(f"Searching trending news in the last: {timeframe}...")
        
        try:
            entries = feedparser.parse(feed_url).entries[:15]
            for entry in entries:
                # Agar title blog mein match nahi karta (Duplicate Check)
                if not any(is_similar(entry.title, old) for old in existing_titles):
                    news_url = entry.link
                    
                    try:
                        # Article scrape karna
                        article = Article(news_url)
                        article.download()
                        article.parse()
                        
                        # Valid Image aur accha content length (400 chars se jyada) check karna
                        if article.top_image and len(article.text) > 400:
                            print(f"Found suitable article: {article.title}")
                            return {
                                "title": article.title if article.title else entry.title,
                                "content": article.text,
                                "image_url": article.top_image,
                                "source_url": news_url
                            }
                    except Exception as e:
                        # Kuch websites extraction block karti hain, isliye error aane par aage badh jayega
                        continue
        except Exception as e:
            print(f"RSS Fetch failed for {timeframe}: {e}")

    return None

# --- 4. POST CONSTRUCTION & PUBLISH ---
def post_to_blogger():
    service = get_blogger_service()
    article_data = fetch_and_extract_news(service)
    
    if not article_data:
        print("No suitable article found today (checked both 24h and 5-day old news).")
        return

    final_title = article_data['title'][:70].strip()
    meta_description = final_title[:150]
    img_style = 'style="max-width:100%; height:auto; border-radius:8px; margin: 25px 0; display:block;"'
    
    # Content format karna (spaces aur lines ko theek karna)
    formatted_content = article_data['content'].replace('\n\n', '</p><p>').replace('\n', '<br>')

    # Final HTML design (Saath mein source owner ko clear credit dena)
    final_content = f"""
    <div style="font-family: Arial; font-size: 16px; line-height: 1.6;">
        <h1 style="text-align:center;">{final_title}</h1>
        <img src="{article_data['image_url']}" alt="News Image" {img_style}>
        <p>{formatted_content}</p>
        <br><hr><br>
        <p style="font-size: 14px; color: #555;">
            <em><strong>Credit:</strong> This article was originally published at <a href="{article_data['source_url']}" target="_blank" rel="nofollow">Source Link</a>. All rights reserved by the original publisher.</em>
        </p>
    </div>
    """

    try:
        service.posts().insert(blogId=BLOGGER_ID, body={
            "title": final_title,
            "content": final_content,
            "labels": get_smart_labels(final_title),
            "searchDescription": meta_description
        }, isDraft=False).execute()
        
        print(f"✅ SUCCESS: Posted '{final_title}'")
        
        # Post successful hone par direct Telegram alert bhejna
        if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
            msg = f"Successfully posted to Blogger!\n\nTitle: {final_title}"
            telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            requests.post(telegram_url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
            
    except Exception as e:
        print(f"❌ Blogger Error: {e}")

if __name__ == "__main__":
    post_to_blogger()
