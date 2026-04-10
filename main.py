import os
import random
import time
import feedparser
import re
import asyncio  # NEW: Telegram ke liye zaroori
from telethon import TelegramClient, events # NEW: Telegram automation ke liye
from difflib import SequenceMatcher
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# --- 1. CONFIGURATION ---
# Blogger & Google Config
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")
BLOGGER_ID = os.getenv("BLOGGER_BLOG_ID")
BLOG_URL = os.getenv("BLOG_URL", "technovexa.blogspot.com")

# Telegram Config (Aapne jo API ID/Hash nikali wo yahan use hogi)
API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
BOT_USERNAME = "@chatgpt_gidbot"

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
        None,
        refresh_token=REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )
    return build('blogger', 'v3', credentials=creds, static_discovery=False)

def is_similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() > 0.6

# --- 2. TOPIC STRATEGY ---
def get_unique_trending_topic(service):
    try:
        print("Checking blog history to avoid duplicates...")
        posts = service.posts().list(blogId=BLOGGER_ID, maxResults=20, fetchBodies=False).execute()
        existing_titles = [p['title'] for p in posts.get('items', [])]
    except Exception as e:
        print(f"⚠️ Could not fetch history: {e}")
        existing_titles = []

    try:
        print("Fetching live trending tech news...")
        rss_url = "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?ceid=US:en&hl=en-US&gl=US"
        feed = feedparser.parse(rss_url)
        
        if feed.entries:
            candidates = feed.entries[:10]
            random.shuffle(candidates)
            for entry in candidates:
                title = entry.title
                is_duplicate = False
                for old_title in existing_titles:
                    if is_similar(title, old_title):
                        is_duplicate = True
                        break
                if not is_duplicate:
                    return title
    except Exception as e:
        print(f"Live news failed ({e}).")

    return "Future of AI 2026"

# --- 3. SMART LABEL REUSING SYSTEM ---
def get_smart_labels(topic):
    topic_lower = topic.lower()
    final_labels = set()
    if any(k in topic_lower for k in ["tech", "gadget", "device"]): final_labels.add("Technology News")
    if "ai" in topic_lower: final_labels.add("AI News")
    if "google" in topic_lower: final_labels.add("Google News")
    if not final_labels: final_labels.add("Technology News")
    return list(final_labels)[:4]

# --- 4. NEW: TELEGRAM AI CONTENT GENERATION ---
async def generate_content_via_telegram(topic):
    print(f"Requesting content from Telegram Bot for: {topic}...")
    
    # Telethon Session setup
    client = TelegramClient('session_name', API_ID, API_HASH)
    await client.start()

    prompt = f"""
    Write a deep-dive blog post about: '{topic}'.
    1. Word Count: 900-1200 words.
    2. No asterisks (*) or hashtags (#).
    3. Use '|||' separator for Title, Intro, Body, and Meta Description.
    Format: Title: [Title] ||| [Intro HTML] ||| [Detailed Body HTML] ||| Description: [Meta]
    """

    try:
        # Send message to bot
        await client.send_message(BOT_USERNAME, prompt)
        
        # Wait for reply (max 120 seconds)
        print("Waiting for bot response...")
        await asyncio.sleep(15) # Bot ko sochne ka time dena
        
        async for message in client.iter_messages(BOT_USERNAME, limit=1):
            content = message.text
            content = content.replace("*", "").replace("#", "")
            await client.disconnect()
            return content

    except Exception as e:
        print(f"Telegram Generation failed: {e}")
        await client.disconnect()
        return None

# --- 5. IMAGE GENERATION ---
def get_image_urls(topic):
    safe_topic = topic.replace(" ", "%20")
    seed = random.randint(1, 99999)
    url1 = f"https://image.pollinations.ai/prompt/hyper-realistic%20concept%20photo%20of%20{safe_topic}?width=1024&height=576&nologo=true&seed={seed}&enhance=true"
    url2 = f"https://image.pollinations.ai/prompt/detailed%20diagrammatic%20tech%20illustration%20related%20to%20{safe_topic}?width=1024&height=576&nologo=true&seed={seed+100}&enhance=true"
    return [url1, url2]

# --- 6. POST CONSTRUCTION ---
def post_to_blogger():
    service = get_blogger_service()
    topic = get_unique_trending_topic(service)
    
    # Run Async Telegram function inside Sync script
    full_response = asyncio.run(generate_content_via_telegram(topic))
    
    if not full_response: return

    # Parsing Logic (Same as your original code)
    if "|||" in full_response:
        parts = full_response.split("|||")
        raw_title = parts[0].replace("Title:", "").strip()
        intro_html = parts[1].strip()
        body_html = parts[2].strip()
        meta_description = parts[3].replace("Description:", "").strip() if len(parts) > 3 else ""
    else:
        raw_title = topic
        intro_html = "<p>Introduction to " + topic + "</p>"
        body_html = full_response
        meta_description = topic

    final_title = raw_title[:70].strip()
    images = get_image_urls(topic)
    img_style = 'style="width:100%; border-radius:8px; margin: 25px 0;"'
    
    read_more = f'<a href="https://{BLOG_URL}" style="color:#007bff; font-weight:bold;">Explore more tech insights here.</a>'
    body_html = body_html.replace("[INTERNAL_LINK]", read_more)

    final_content = f"""
    <div style="font-family: Arial; font-size: 17px;">
        <h1 style="text-align:center;">{final_title}</h1>
        {intro_html}
        <img src="{images[0]}" alt="Main Image" {img_style}>
        {body_html}
        <br><img src="{images[1]}" alt="Secondary Image" {img_style}>
    </div>
    """

    post_body = {
        "title": final_title,
        "content": final_content,
        "labels": get_smart_labels(topic),
        "searchDescription": meta_description
    }
    
    try:
        service.posts().insert(blogId=BLOGGER_ID, body=post_body, isDraft=False).execute()
        print(f"✅ SUCCESS: Posted '{final_title}'")
    except Exception as e:
        print(f"❌ Blogger Error: {e}")

if __name__ == "__main__":
    post_to_blogger()
