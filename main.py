import os
import random
import time
import feedparser
import re
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

# --- MASTER LABEL LIST (FROM YOUR IMAGE) ---
# Ye wo labels hain jo aapke blog par already hain.
# Code koshish karega ki inhi mein se select kare taaki naye duplicate na banein.
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
    # Increased timeout for safety
    return build('blogger', 'v3', credentials=creds, static_discovery=False)

# --- 2. TOPIC STRATEGY ---
def get_trending_topic():
    try:
        print("Fetching live trending tech news from USA...")
        # Google News Technology US Feed
        rss_url = "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?ceid=US:en&hl=en-US&gl=US"
        feed = feedparser.parse(rss_url)
        if feed.entries:
            # Pick one random topic from top 5 to ensure variety
            entry = random.choice(feed.entries[:5])
            print(f"Live Topic Selected: {entry.title}")
            return entry.title
    except Exception as e:
        print(f"Live news failed ({e}). Using fallback list.")

    # Fallback Topics
    topics = ["Future of AI 2026", "Google DeepMind Latest", "OpenAI Sora Updates", "Apple Vision Pro News"]
    return random.choice(topics)

# --- 3. SMART LABEL REUSING SYSTEM (NEW) ---
def get_smart_labels(topic):
    topic_lower = topic.lower()
    final_labels = set()
    
    # Keyword matching strategy to reuse existing labels
    
    # 1. Broad Technology Matches
    if any(k in topic_lower for k in ["tech", "gadget", "device", "future"]):
        final_labels.add("Technology News")
        final_labels.add("Tech Updates")
        
    # 2. AI Specific Matches
    if any(k in topic_lower for k in ["ai ", "artificial intelligence", "ml", "deep learning"]):
        final_labels.add("AI News")
        final_labels.add("AI Updates")
    if any(k in topic_lower for k in ["gpt", "gemini", "claude", "llama", "model"]):
        final_labels.add("AI Models")

    # 3. Company Specific Matches
    if "google" in topic_lower or "alphabet" in topic_lower:
        final_labels.add("Google News")
    if "openai" in topic_lower or "chatgpt" in topic_lower:
        final_labels.add("OpenAI News")
    if "microsoft" in topic_lower or "azure" in topic_lower:
         final_labels.add("Software Updates")
         final_labels.add("Cloud Computing")

    # 4. Regional/Specific Matches
    if "india" in topic_lower:
        final_labels.add("India Tech News")
    else:
         # Agar India specific nahi hai to Global maan lete hain
         if random.random() > 0.7: # 30% chance to add global tag
             final_labels.add("Global Tech News")

    # 5. Fallback - Agar koi bhi label match nahi hua
    if not final_labels:
        final_labels.add("Technology News")
        print("No specific match found, using generic label.")

    # Convert set back to list and limit to 4 labels max
    return list(final_labels)[:4]


# --- 4. AI CONTENT GENERATION (UPDATED PROMPT) ---
def generate_blog_content(topic):
    print(f"Generating 900-1200 word content for: {topic}...")
    
    client = OpenAI(
        base_url="https://models.inference.ai.azure.com",
        api_key=GITHUB_TOKEN,
    )
    
    # Updated Prompt with Strict Constraints
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
            max_tokens=6000, # Increased tokens for longer articles
        )

        content = response.choices[0].message.content
        if "</think>" in content:
            content = content.split("</think>")[-1].strip()
            
        # FINAL SAFETY CLEANUP: Remove any rogue * or # characters
        content = content.replace("*", "").replace("#", "")
        return content

    except Exception as e:
        print(f"AI Generation failed. Error: {e}")
        return None

# --- 5. IMAGE GENERATION ---
def get_image_urls(topic):
    safe_topic = topic.replace(" ", "%20")
    seed = random.randint(1, 99999)
    # Image 1 (Top Concept)
    url1 = f"https://image.pollinations.ai/prompt/hyper-realistic%20concept%20photo%20of%20{safe_topic}?width=1024&height=576&nologo=true&seed={seed}&enhance=true"
    # Image 2 (Middle Detail)
    url2 = f"https://image.pollinations.ai/prompt/detailed%20diagrammatic%20tech%20illustration%20related%20to%20{safe_topic}?width=1024&height=576&nologo=true&seed={seed+100}&enhance=true"
    return [url1, url2]

# --- 6. POST CONSTRUCTION ---
def post_to_blogger():
    topic = get_trending_topic()
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
    
    # Internal Link Replacement
    read_more = f'<a href="https://{BLOG_URL}" style="color:#007bff; text-decoration:none; font-weight:bold;">Explore more tech insights here.</a>'
    body_html = body_html.replace("[INTERNAL_LINK]", read_more)

    # Insert Image 2 in Middle
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

    # Get reused labels
    selected_labels = get_smart_labels(topic)
    print(f"Labels selected for this post: {selected_labels}")

    service = get_blogger_service()
    post_body = {
        "title": final_title,
        "content": final_content,
        "labels": selected_labels,
        "searchDescription": meta_description
    }
    
    # ACCOUNT SAFETY PAUSE
    print("Pausing for a few seconds before posting for safety...")
    time.sleep(random.randint(5, 10)) # Human-like pause

    try:
        service.posts().insert(blogId=BLOGGER_ID, body=post_body, isDraft=False).execute()
        print(f"✅ SUCCESS: Posted '{final_title}' (Approx words: High)")
    except Exception as e:
        print(f"❌ Error posting to Blogger: {e}")

if __name__ == "__main__":
    post_to_blogger()
