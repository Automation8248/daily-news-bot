import os
import random
import time
import feedparser
import re
from difflib import SequenceMatcher  # NEW: Similarity check karne ke liye
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from openai import OpenAI

# --- 1. CONFIGURATION ---
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")
BLOGGER_ID = os.getenv("BLOGGER_BLOG_ID")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
BLOG_URL = os.getenv("BLOG_URL", "technovexa.blogspot.com")

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

# --- NEW FUNCTION: CHECK SIMILARITY ---
def is_similar(a, b):
    """Checks if two titles are too similar (more than 60% match)"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() > 0.6

# --- 2. TOPIC STRATEGY (UPDATED WITH HISTORY CHECK) ---
def get_unique_trending_topic(service):
    # Step 1: Fetch existing post titles from Blogger (History)
    try:
        print("Checking blog history to avoid duplicates...")
        posts = service.posts().list(blogId=BLOGGER_ID, maxResults=20, fetchBodies=False).execute()
        existing_titles = [p['title'] for p in posts.get('items', [])]
    except Exception as e:
        print(f"⚠️ Could not fetch history: {e}")
        existing_titles = []

    # Step 2: Fetch Live Trending News
    try:
        print("Fetching live trending tech news from USA...")
        rss_url = "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?ceid=US:en&hl=en-US&gl=US"
        feed = feedparser.parse(rss_url)
        
        if feed.entries:
            # Check top 10 entries instead of just random choice
            candidates = feed.entries[:10]
            random.shuffle(candidates) # Shuffle to keep it random but checked

            for entry in candidates:
                title = entry.title
                
                # Check 1: Is this title in history?
                is_duplicate = False
                for old_title in existing_titles:
                    if is_similar(title, old_title):
                        print(f"⏭️ Skipping Duplicate Topic: {title}")
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    print(f"✅ Fresh Topic Selected: {title}")
                    return title

            print("⚠️ All trending topics seem to be duplicates or covered.")
            
    except Exception as e:
        print(f"Live news failed ({e}). Using fallback.")

    # Step 3: Fallback Topics (Only if live fails)
    # Ensure fallback isn't a duplicate either
    fallbacks = ["Future of AI 2026", "Google DeepMind Latest", "OpenAI Sora Updates", "Apple Vision Pro News"]
    for ft in fallbacks:
        is_dup = False
        for old_title in existing_titles:
             if is_similar(ft, old_title):
                 is_dup = True
                 break
        if not is_dup:
            return ft
            
    return fallbacks[0] # Last resort

# --- 3. SMART LABEL REUSING SYSTEM ---
def get_smart_labels(topic):
    topic_lower = topic.lower()
    final_labels = set()
    
    if any(k in topic_lower for k in ["tech", "gadget", "device", "future"]):
        final_labels.add("Technology News")
        final_labels.add("Tech Updates")
        
    if any(k in topic_lower for k in ["ai ", "artificial intelligence", "ml", "deep learning"]):
        final_labels.add("AI News")
        final_labels.add("AI Updates")
    if any(k in topic_lower for k in ["gpt", "gemini", "claude", "llama", "model"]):
        final_labels.add("AI Models")

    if "google" in topic_lower or "alphabet" in topic_lower:
        final_labels.add("Google News")
    if "openai" in topic_lower or "chatgpt" in topic_lower:
        final_labels.add("OpenAI News")
    if "microsoft" in topic_lower or "azure" in topic_lower:
         final_labels.add("Software Updates")
         final_labels.add("Cloud Computing")

    if "india" in topic_lower:
        final_labels.add("India Tech News")
    else:
         if random.random() > 0.7:
             final_labels.add("Global Tech News")

    if not final_labels:
        final_labels.add("Technology News")

    return list(final_labels)[:4]

# --- 4. AI CONTENT GENERATION ---
def generate_blog_content(topic):
    print(f"Generating 900-1200 word content for: {topic}...")
    
    client = OpenAI(
        base_url="https://models.inference.ai.azure.com",
        api_key=GITHUB_TOKEN,
    )
    
    prompt = f"""
    You are a senior tech journalist targeting a US audience. Write a deep-dive blog post about: '{topic}'.
    
    CRITICAL CONSTRAINTS:
    1.  **Word Count:** The post MUST be between 900 and 1200 words long.
    2.  **Formatting Forbidden:** DO NOT use asterisks (*) or hashtags (#) anywhere in the Title or Body. They break the blog formatting.
    3.  **Tone:** Human-like, engaging, simple English. Avoid repetitive AI jargon.
    
    STRUCTURE INSTRUCTIONS (Use '|||' separator):
    1. **Title:** Catchy hook title (max 70 chars). NO * or #.
    2. **Intro:** A single, powerful introductory paragraph.
    3. **Body:** Long, detailed content using <h3> and <p> tags.
       - Naturally insert text "[INTERNAL_LINK]" once in a relevant sentence.
       - Include a detailed FAQ section at the end.
    4. **Meta:** A 150-character SEO description.

    OUTPUT FORMAT:
    Title: [Insert Title]
    |||
    [Intro Paragraph HTML]
    |||
    [Rest of Detailed Body HTML]
    |||
    Description: [Meta Description]
    """
    
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a professional writer that strictly follows length and formatting constraints."},
                {"role": "user", "content": prompt}
            ],
            model="DeepSeek-R1",
            temperature=0.7,
            max_tokens=6000,
        )

        content = response.choices[0].message.content
        if "</think>" in content:
            content = content.split("</think>")[-1].strip()
            
        content = content.replace("*", "").replace("#", "")
        return content

    except Exception as e:
        print(f"AI Generation failed. Error: {e}")
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
    # Service pehle initialize kiya taaki history check kar sakein
    service = get_blogger_service()
    
    # Updated: Pass service to check history
    topic = get_unique_trending_topic(service)
    
    # Generate Content
    full_response = generate_blog_content(topic)
    
    if not full_response: return

    # Parsing Logic
    if "|||" in full_response:
        parts = full_response.split("|||")
        raw_title = parts[0].replace("Title:", "").strip()
        intro_html = parts[1].strip()
        body_html = parts[2].strip()
        meta_description = parts[3].replace("Description:", "").strip() if len(parts) > 3 else ""
    else:
        print("Fallback parsing used.")
        lines = full_response.strip().split('\n')
        raw_title = lines[0].replace("Title:", "").strip()
        intro_html = "<p>" + lines[1] + "</p>" if len(lines) > 1 else ""
        body_html = "\n".join(lines[2:])
        meta_description = raw_title

    # Final Assembly
    final_title = raw_title[:70].strip().replace("*", "").replace("#", "")
    images = get_image_urls(topic)
    img_style = 'style="width:100%; border-radius:8px; margin: 25px 0; display:block; box-shadow: 0 2px 5px rgba(0,0,0,0.1);"'
    
    read_more = f'<a href="https://{BLOG_URL}" style="color:#007bff; text-decoration:none; font-weight:bold;">Explore more tech insights here.</a>'
    body_html = body_html.replace("[INTERNAL_LINK]", read_more)

    paras = body_html.split("</p>")
    if len(paras) > 4:
        mid = len(paras) // 2
        paras.insert(mid, f'<br><img src="{images[1]}" alt="Details about {topic}" {img_style}><br>')
        body_html = "</p>".join(paras)
    else:
        body_html += f'<br><img src="{images[1]}" alt="Detailed view" {img_style}>'

    final_content = f"""
    <div style="font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 17px; line-height: 1.7; color: #222;">
        <h1 style="text-align:center; color:#111;">{final_title}</h1>
        {intro_html}
        <img src="{images[0]}" alt="{topic} Main Image" {img_style}>
        {body_html}
        <p style="font-size:14px; color:#666; text-align:center; margin-top:30px;"><i>Note: This content is AI-assisted, curated by human editors for accuracy.</i></p>
    </div>
    """

    selected_labels = get_smart_labels(topic)
    print(f"Labels selected: {selected_labels}")

    post_body = {
        "title": final_title,
        "content": final_content,
        "labels": selected_labels,
        "searchDescription": meta_description
    }
    
    print("Pausing for safety...")
    time.sleep(random.randint(5, 10))

    try:
        service.posts().insert(blogId=BLOGGER_ID, body=post_body, isDraft=False).execute()
        print(f"✅ SUCCESS: Posted '{final_title}'")
    except Exception as e:
        print(f"❌ Error posting to Blogger: {e}")

if __name__ == "__main__":
    post_to_blogger()
