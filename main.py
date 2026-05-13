import os
import requests
import feedparser
from difflib import SequenceMatcher
from newspaper import Article
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# --- 1. CONFIGURATION ---
# Blogger & Google Config
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")
BLOGGER_ID = os.getenv("BLOGGER_BLOG_ID")

# Telegram Notification Config (Sirf simple token aur chat id)
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

# --- 3. FETCH ORIGINAL ARTICLE & IMAGE ---
def fetch_and_extract_news(service):
    try:
        posts = service.posts().list(blogId=BLOGGER_ID, maxResults=20, fetchBodies=False).execute()
        existing_titles = [p['title'] for p in posts.get('items', [])]
    except Exception:
        existing_titles = []

    try:
        rss_url = "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?ceid=US:en&hl=en-US&gl=US"
        entries = feedparser.parse(rss_url).entries[:15]
        
        for entry in entries:
            # Duplicate check
            if not any(is_similar(entry.title, old) for old in existing_titles):
                news_url = entry.link
                
                try:
                    # Original Article download aur parse karna
                    article = Article(news_url)
                    article.download()
                    article.parse()
                    
                    # Ensure karte hain ki article mein image ho aur text decent size ka ho
                    if article.top_image and len(article.text) > 400:
                        return {
                            "title": article.title if article.title else entry.title,
                            "content": article.text,
                            "image_url": article.top_image,
                            "source_url": news_url
                        }
                except Exception as e:
                    print(f"Extraction failed for {news_url}: {e}")
                    continue
    except Exception as e:
        print(f"RSS Fetch failed: {e}")

    return None

# --- 4. POST CONSTRUCTION & PUBLISH ---
def post_to_blogger():
    service = get_blogger_service()
    article_data = fetch_and_extract_news(service)
    
    if not article_data:
        print("No suitable new article found today.")
        return

    final_title = article_data['title'][:70].strip()
    meta_description = final_title[:150]
    img_style = 'style="max-width:100%; height:auto; border-radius:8px; margin: 25px 0; display:block;"'
    
    # Text format ko HTML paragraphs mein convert karna
    formatted_content = article_data['content'].replace('\n\n', '</p><p>').replace('\n', '<br>')

    # HTML Structure jisme last mein CREDIT diya gaya hai
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
        # Blogger par insert karna
        service.posts().insert(blogId=BLOGGER_ID, body={
            "title": final_title,
            "content": final_content,
            "labels": get_smart_labels(final_title),
            "searchDescription": meta_description
        }, isDraft=False).execute()
        
        print(f"✅ SUCCESS: Posted '{final_title}'")
        
        # Telegram par simple success notification bhejna
        if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
            msg = f"Successfully posted to Blogger!\n\nTitle: {final_title}"
            telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            requests.post(telegram_url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
            
    except Exception as e:
        print(f"❌ Blogger Error: {e}")

if __name__ == "__main__":
    post_to_blogger()
