import os
import requests
import feedparser
import urllib.parse
from difflib import SequenceMatcher
from newspaper import Article, Config
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# --- 1. CONFIGURATION (100% FREE) ---
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")
BLOGGER_ID = os.getenv("BLOGGER_BLOG_ID")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- 2. PREMIUM TARGET SITES ---
TARGET_SITES = [
    "techcrunch.com", "theverge.com", "wired.com", "arstechnica.com", "venturebeat.com",
    "technologyreview.com", "openai.com", "ai.googleblog.com", "deepmind.com", "towardsdatascience.com",
    "freecodecamp.org", "smashingmagazine.com", "css-tricks.com", "hashnode.com", "dev.to",
    "infoworld.com", "zdnet.com", "krebsonsecurity.com", "thehackernews.com", "blog.cloudflare.com"
]

Existing_Labels_DB = [
    "AI Models", "AI News", "AI Updates", "Cloud Computing", "Digital Innovation", 
    "Global Tech News", "Google News", "India Tech News", "OpenAI News", 
    "Smart Technology", "Software Updates", "Tech Updates", "Technology News"
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
    if "global" in topic_lower or "world" in topic_lower: temp_labels.add("Global Tech News")
    final_labels = [lbl for lbl in temp_labels if lbl in Existing_Labels_DB]
    return final_labels[:4] if final_labels else ["Technology News"]

# --- 3. FETCH EXCLUSIVELY FROM PREMIUM SITES (NO REWRITE) ---
def fetch_and_extract_news(service):
    try:
        posts = service.posts().list(blogId=BLOGGER_ID, maxResults=30, fetchBodies=False).execute()
        existing_titles = [p['title'] for p in posts.get('items', [])]
    except Exception:
        existing_titles = []

    user_agent_config = Config()
    user_agent_config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    user_agent_config.request_timeout = 15

    # Target sites ko 5-5 ke groups me baatna taaki URL lamba na ho
    site_chunks = [TARGET_SITES[i:i + 5] for i in range(0, len(TARGET_SITES), 5)]
    
    for chunk in site_chunks:
        query = " OR ".join([f"site:{site}" for site in chunk])
        safe_query = urllib.parse.quote(query)
        
        feed_url = f"https://news.google.com/rss/search?q={safe_query}+when:14d&hl=en-US&gl=US&ceid=US:en"
        print(f"Checking premium sites for original content...")

        try:
            entries = feedparser.parse(feed_url).entries
            for entry in entries:
                if not any(is_similar(entry.title, old) for old in existing_titles):
                    news_url = entry.link
                    
                    try:
                        article = Article(news_url, config=user_agent_config)
                        article.download()
                        article.parse()
                        
                        if len(article.text) > 200:
                            final_title = article.title if article.title else entry.title
                            
                            # FREE AI IMAGE GENERATION (Agar original image nahi hai)
                            image_url = article.top_image
                            if not image_url:
                                print(f"No image found! Generating Free AI image for: {final_title[:50]}...")
                                safe_img_prompt = urllib.parse.quote(f"hyper realistic technology illustration about {final_title[:100]}")
                                image_url = f"https://image.pollinations.ai/prompt/{safe_img_prompt}?width=1024&height=576&nologo=true&enhance=true"

                            print(f"✅ Picked Article: {final_title}")

                            return {
                                "title": final_title,
                                "content": article.text, # Original content return kar rahe hain
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
        print("CRITICAL: Failed to find any suitable tech blog from the 20 websites.")
        return

    final_title = article_data['title'][:70].strip()
    meta_description = final_title[:150]
    img_style = 'style="max-width:100%; height:auto; border-radius:8px; margin: 25px 0; display:block;"'

    # Content Formatting: Original text ko cleanly HTML paragraphs me convert karna
    formatted_content = article_data['content'].replace('\n\n', '</p><p>').replace('\n', '<br>')

    # HTML Layout with ORIGINAL Content and Source Credit
    final_content = f"""
    <div style="font-family: Arial; font-size: 16px; line-height: 1.6;">
        <h1 style="text-align:center;">{final_title}</h1>
        <img src="{article_data['image_url']}" alt="Technology Blog Image" {img_style}>
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
        
        print(f"✅ SUCCESS: Posted original article '{final_title}' to Blogger.")
        
        if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
            msg = f"✅ New Post on Technovexa!\n\nTitle: {final_title}"
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                          json={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
            
    except Exception as e:
        print(f"❌ Blogger Post Error: {e}")

if __name__ == "__main__":
    post_to_blogger()
