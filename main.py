import os
import requests
import feedparser
import urllib.parse
from difflib import SequenceMatcher
from newspaper import Article, Config
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

# --- 3. FETCH ANY TECH NEWS & AI IMAGE GENERATION ---
def fetch_and_extract_news(service):
    try:
        posts = service.posts().list(blogId=BLOGGER_ID, maxResults=30, fetchBodies=False).execute()
        existing_titles = [p['title'] for p in posts.get('items', [])]
    except Exception:
        existing_titles = []

    # Config taaki block na ho
    user_agent_config = Config()
    user_agent_config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    user_agent_config.request_timeout = 15

    # Broad RSS Feeds (USA targetted) - Koi strict trending time limit nahi
    google_rss_feeds = [
        "https://news.google.com/rss/search?q=technology+OR+AI+when:24h&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=gadget+OR+software&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=technology+OR+tech+OR+AI&hl=en-US&gl=US&ceid=US:en" # Pure fallback (Koi bhi tech news)
    ]

    for feed_url in google_rss_feeds:
        print(f"Checking feed: {feed_url.split('?')[0]} ...")
        
        try:
            entries = feedparser.parse(feed_url).entries
            for entry in entries:
                if not any(is_similar(entry.title, old) for old in existing_titles):
                    news_url = entry.link
                    
                    try:
                        article = Article(news_url, config=user_agent_config)
                        article.download()
                        article.parse()
                        
                        # LOGIC UPDATE: Ab image hona zaroori nahi, bas content length acchi honi chahiye
                        if len(article.text) > 300:
                            final_title = article.title if article.title else entry.title
                            
                            # AI IMAGE GENERATION FALLBACK
                            image_url = article.top_image
                            if not image_url:
                                print(f"No image found in article! Generating AI image for: {final_title}")
                                # URL safe prompt banana
                                safe_prompt = urllib.parse.quote(f"hyper realistic technology news illustration about {final_title}")
                                # Pollinations AI API
                                image_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1024&height=576&nologo=true&enhance=true"
                            else:
                                print("Original image found.")

                            print(f"Selected Article: {final_title}")
                            return {
                                "title": final_title,
                                "content": article.text,
                                "image_url": image_url,
                                "source_url": news_url
                            }
                    except Exception as e:
                        pass
        except Exception as e:
            pass

    return None

# --- 4. POST CONSTRUCTION & PUBLISH ---
def post_to_blogger():
    service = get_blogger_service()
    article_data = fetch_and_extract_news(service)
    
    if not article_data:
        print("CRITICAL: Failed to find any suitable article today.")
        if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                          json={"chat_id": TELEGRAM_CHAT_ID, "text": "⚠️ Technovexa Bot Failed: No article found today!"})
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
            msg = f"✅ Successfully posted to Technovexa!\n\nTitle: {final_title}"
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                          json={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
            
    except Exception as e:
        print(f"❌ Blogger Error: {e}")

if __name__ == "__main__":
    post_to_blogger()
