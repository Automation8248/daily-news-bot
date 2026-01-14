import os
import random
import time
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from huggingface_hub import InferenceClient

# --- 1. CONFIGURATION ---
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")
BLOGGER_ID = os.getenv("BLOGGER_BLOG_ID")
HF_TOKEN = os.getenv("HF_TOKEN")

def get_blogger_service():
    creds = Credentials(
        None,
        refresh_token=REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )
    return build('blogger', 'v3', credentials=creds)

# --- SEO STRATEGY TOPICS (AI, TECH, EVERGREEN) ---
def get_trending_topic():
    # 60% AI, 30% Technology, 10% Evergreen Analysis
    topics = [
        # --- CORE AI TOPICS (High Value) ---
        "Artificial Intelligence Latest News", "Generative AI Updates", 
        "AI Models GPT Gemini Claude", "Machine Learning Breakthroughs", 
        "Deep Learning Innovations", "AI Automation in Industries", 
        "AI Ethics & Regulations", "AI Policy & Government Rules", 
        "AI in Real Life Applications", "Future of Artificial Intelligence",
        
        # --- BIG TECH (High Search) ---
        "Google AI & Technology News", "OpenAI Latest Updates", 
        "Microsoft AI & Tech News", "Meta AI Developments", 
        "Apple Technology News", "Startup & Funding News",
        
        # --- TECHNOLOGY NEWS (Evergreen) ---
        "Future Technology Trends", "Emerging Technologies", 
        "Software & App Updates", "Cyber Security Threats & Fixes", 
        "Cloud Computing News", "Internet & Digital Technology", 
        "Smart Technology & IoT", "Data Privacy & Security", 
        "Open Source Technology News",
        
        # --- AI TOOLS (Trending) ---
        "New AI Tools Launch", "Free AI Tools News", 
        "AI Software Updates", "Productivity AI Tools", 
        "Automation Tools News", "SaaS Platform Updates",
        
        # --- TRENDS & REGIONS ---
        "AI Trends 2026", "Technology Trends 2026", 
        "How AI is Changing Technology", "AI Impact on Jobs", 
        "Global Technology News", "US Technology News", 
        "India AI & Tech News", "Asia Technology Trends",
        
        # AI NEWS & UPDATES (60%)
        "Artificial Intelligence Latest News", "Generative AI Updates", 
        "AI Models GPT Gemini Claude", "Machine Learning Breakthroughs", 
        "Deep Learning Innovations", "AI Automation in Industries", 
        "AI Ethics & Regulations", "AI Policy & Government Rules", 
        "AI in Real Life Applications", "Future of Artificial Intelligence",
        "OpenAI Latest Updates", "Google AI & Technology News", 
        "Microsoft AI & Tech News", "Meta AI Developments", 
        "AI Trends 2026", "New AI Tools Launch", "Free AI Tools News",
        
        # TECHNOLOGY NEWS (30%)
        "Future Technology Trends", "Emerging Technologies", 
        "Software & App Updates", "Cyber Security Threats & Fixes", 
        "Cloud Computing News", "Internet & Digital Technology", 
        "Smart Technology & IoT", "Data Privacy & Security", 
        "Open Source Technology News", "Apple Technology News",
        "Startup & Funding News", "New Product Launches",
        "Global Technology News", "US Technology News", 
        "India AI & Tech News", "Asia Technology Trends",
        
        # EVERGREEN ANALYSIS (10%)
        "How AI is Changing Technology", "AI Impact on Jobs", 
        "AI vs Human Intelligence", "Future of Automation",
        "Technology Trends 2026", "SaaS Platform Updates"
    ]
    return random.choice(topics)

# --- TECHNOVEXA SMART LABELS LOGIC ---
def get_smart_labels(topic):
    topic_lower = topic.lower()
    selected_labels = []

    # Level 1: Main Categories
    if any(x in topic_lower for x in ["ai", "gpt", "gemini", "learning", "claude", "automation"]):
        selected_labels.extend(["AI News", "AI Updates"])
    else:
        selected_labels.extend(["Technology News", "Tech Updates"])

    # Level 2 & 3: Specialized Topics
    if "generative" in topic_lower or "sora" in topic_lower: selected_labels.append("Generative AI")
    if "model" in topic_lower or "gpt" in topic_lower: selected_labels.append("AI Models")
    if "automation" in topic_lower or "robot" in topic_lower: selected_labels.append("AI Automation")
    if "security" in topic_lower or "privacy" in topic_lower: selected_labels.append("Cyber Security")
    if "cloud" in topic_lower or "saas" in topic_lower: selected_labels.append("Cloud Computing")
    if "software" in topic_lower or "app" in topic_lower: selected_labels.append("Software Updates")
    if "smart" in topic_lower or "iot" in topic_lower: selected_labels.append("Smart Technology")

    # Level 4: Company News
    if "google" in topic_lower: selected_labels.append("Google News")
    elif "openai" in topic_lower: selected_labels.append("OpenAI News")
    elif "microsoft" in topic_lower: selected_labels.append("Microsoft News")
    elif "meta" in topic_lower: selected_labels.append("Meta News")
    elif "apple" in topic_lower: selected_labels.append("Big Tech")
    elif "startup" in topic_lower: selected_labels.append("Startup News")

    # Level 5: Region & Trends
    if "2026" in topic_lower or "future" in topic_lower: selected_labels.extend(["Tech Trends", "Future Technology"])
    if "india" in topic_lower: selected_labels.append("India Tech News")
    elif "global" in topic_lower: selected_labels.append("Global Tech News")
    elif "us " in topic_lower: selected_labels.append("US Tech News")

    # Final Filter: Max 5, Min 3
    unique_labels = list(set(selected_labels))
    if len(unique_labels) < 3: unique_labels.extend(["Digital Innovation", "Tech Updates"])
    return unique_labels[:5]

# --- 2. AI CONTENT (HUMANIZED) ---
def generate_blog_post(topic):
    print(f"Generating content for: {topic}...")
    models = ["mistralai/Mistral-7B-Instruct-v0.3", "microsoft/Phi-3.5-mini-instruct", "Qwen/Qwen2.5-72B-Instruct"]
    
    prompt = f"""
    Write a humanized, senior tech journalist style blog post for category: '{topic}'.
    RULES:
    - TITLE: Direct, simple, NO colons (:), Max 55 chars.
    - TONE: Conversational, personal, engaging (Use "We", "I"). No robotic filler.
    - STRUCTURE: Title First Line -> '|||' -> Intro -> [IMG1] -> 8-9 Subheadings (<h3>) with stylish paragraphs -> [IMG2] (after 3rd H3) -> [IMG3] (near end).
    - HTML: Use <p style="font-family: Georgia, serif; font-size: 18px;"> for Intro.
    - HTML: Use <p style="font-family: Verdana, sans-serif;"> for Body paragraphs.
    """
    
    for model in models:
        try:
            client = InferenceClient(model=model, token=HF_TOKEN)
            response = client.chat_completion([{"role": "user", "content": prompt}], max_tokens=2000, temperature=0.8)
            return response.choices[0].message.content
        except Exception as e:
            print(f"Model {model} failed. Retrying...")
            time.sleep(2)
    return "Error: AI generation failed."

# --- 3. POSTING LOGIC ---
def get_image_urls(topic):
    safe_topic = topic.replace(" ", "%20").replace("&", "")
    seed = random.randint(1, 1000)
    return [
        f"https://image.pollinations.ai/prompt/futuristic%20tech%20{safe_topic}?nologo=true&seed={seed}",
        f"https://image.pollinations.ai/prompt/ai%20chip%20circuit%20{safe_topic}?nologo=true&seed={seed+1}",
        f"https://image.pollinations.ai/prompt/human%20robot%20interaction%20{safe_topic}?nologo=true&seed={seed+2}"
    ]

def post_to_blogger():
    topic = get_trending_topic()
    final_labels = get_smart_labels(topic)
    full_response = generate_blog_post(topic)
    
    if "|||" not in full_response: return

    parts = full_response.split("|||")
    raw_title = parts[0].strip().replace(":", "").replace('"', '')
    content_html = parts[1].strip()

    # Title Length Control (55 Chars)
    final_title = raw_title[:55].rsplit(' ', 1)[0] if len(raw_title) > 55 else raw_title
    
    images = get_image_urls(topic)
    img_style = 'style="width:100%; border-radius:10px; margin: 20px 0; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"'
    
    for i, img in enumerate(images):
        content_html = content_html.replace(f'[IMG{i+1}]', f'<img src="{img}" {img_style}><br>')

    final_body = f"""
    <h1 style="text-align: center; font-family: 'Helvetica Neue', sans-serif; color: #2c3e50;">{final_title}</h1>
    <hr style="border:0; height:1px; background-image: linear-gradient(to right, #ccc, #333, #ccc);">
    {content_html}
    <p style="text-align:center; font-size:12px; color:#888;"><i>Article by Technovexa AI Intelligence</i></p>
    """

    service = get_blogger_service()
    body = {"title": final_title, "content": final_body, "labels": final_labels}
    service.posts().insert(blogId=BLOGGER_ID, body=body).execute()
    print(f"Posted: {final_title} | Tags: {final_labels}")

if __name__ == "__main__":
    post_to_blogger()
