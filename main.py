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

# --- 3. STRICT TECH & USA FILTER LOGIC ---
def is_tech_related(text, title):
    # Yeh check karta hai ki article properly tech se related hai ya nahi
    tech_keywords = [
        "technology", "tech", "software", "hardware", "smartphone", "apple", 
        "google", "microsoft", "cybersecurity", "ai", "artificial intelligence", 
        "gadget", "robotics", "app", "startup", "silicon valley", "crypto"
    ]
    
    content_lower = text.lower() + " " + title.lower()
    # Agar inme se kam se kam 2 tech words article mein hain, tabhi usko tech article manenge
    match_count = sum(1 for word in tech_keywords if word in content_lower)
    return match_count >= 2

# --- 4. STRICTLY FETCH FROM GOOGLE RSS ONLY ---
def fetch_and_extract_news(service):
    try:
        posts = service.posts().list(blogId=BLOGGER_ID, maxResults=20, fetchBodies=False).execute()
        existing_titles = [p['title'] for p in posts.get('items', [])]
    except Exception:
        existing_titles = []

    # gl=US aur hl=en-US specifically USA audience ko target karte hain
    google_rss_feeds = [
        "https://news.google.com/rss/search?q=technology+OR+tech+OR+AI+when:24h&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=technology+OR+tech+OR+AI+when:5d&hl=en-US&gl=US&ceid=US:en"
    ]

    for feed_url in google_rss_feeds:
        timeframe = "24 Hours" if "when:24h" in feed_url else "5 Days"
        print(f"Searching USA tech news strictly from Google RSS (Last {timeframe})...")
        
        try:
            entries = feedparser.parse(feed_url).entries[:15]
            for entry in entries:
                if not any(is_similar(entry.title, old) for old in existing_titles):
                    news_url = entry.link
                    
                    try:
                        article = Article(news_url)
                        article.download()
                        article.parse()
                        
                        # Check: Image ho, Content bada ho, aur purely TECH related ho
                        if article.top_image and len(article.text) > 400 and is_tech_related(article.text, article.title):
                            print(f"Found USA Tech article: {article.title}")
                            return {
                                "title": article.title if article.title else entry.title,
                                "content": article.text,
                                "image_url": article.top_image,
                                "source_url": news_url
                            }
                        else:
                            print(f"Skipped: Not enough tech content or missing image -> {entry.title}")
                    except Exception as e:
                        continue
        except Exception as e:
            print(f"Google RSS Fetch failed for {timeframe}: {e}")

    return None

# --- 5. POST CONSTRUCTION & PUBLISH ---
def post_to_blogger():
    service = get_blogger_service()
    article_data = fetch_and_extract_news(service)
    
    if not article_data:
        print("No suitable new USA tech article found in Google RSS today.")
        return

    final_title = article_data['title'][:70].strip()
    meta_description = final_title[:150]
    img_style = 'style="max-width:100%; height:auto; border-radius:8px; margin: 25px 0; display:block;"'
    
    formatted_content = article_data['content'].replace('\n\n', '</p><p>').replace('\n', '<br>')

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
        
        if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
            msg = f"Successfully posted USA Tech News to Blogger!\n\nTitle: {final_title}"
            telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            requests.post(telegram_url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
            
    except Exception as e:
        print(f"❌ Blogger Error: {e}")

if __name__ == "__main__":
    post_to_blogger()
