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

# --- 2. AI CONTENT (HUMANIZED & SEO OPTIMIZED) ---
def generate_blog_post(topic):
    print(f"Generating optimized content for: {topic}...")
    models = ["mistralai/Mistral-7B-Instruct-v0.3", "microsoft/Phi-3.5-mini-instruct", "Qwen/Qwen2.5-72B-Instruct"]
    
    # Updated Prompt with SEO, FAQ, Conclusion and E-E-A-T
    prompt = f"""
    Write a humanized, senior tech journalist style blog post for category: '{topic}'.
    
    STRICT SEO & STRUCTURE RULES:
    1. FORMAT: Title ||| Search Description ||| Body
    2. NO MARKDOWN: Do NOT use '#' or '##' symbols for headings. Use HTML tags only.
    3. TITLE: Direct, simple, NO colons (:), Max 55 chars. Use searchable keywords like '{topic} Explained'.
    4. SEARCH DESCRIPTION: Write a 140-character meta description for Google search.
    5. TONE: Conversational, personal, engaging (Use "We", "I"). No robotic filler words.
    6. ZERO-CLICK FAQ: After Intro, add a 'Quick Summary FAQ' section with 2 Q&As using <div> tags.
    7. STRUCTURE: Intro -> FAQ -> [IMG1] -> 8-9 Subheadings (<h3>) -> [IMG2] -> [IMG3] -> Conclusion (Takeaways) -> Author Bio.
    8. INTERNAL/EXTERNAL: Naturally place [INTERNAL_LINK] and [EXTERNAL_LINK] in paragraphs.
    9. E-E-A-T: End with: "About Author: Senior Tech Analyst at Technovexa with 10+ years of AI expertise."
    10. HTML ONLY: Use <h3> for headings. NEVER use '#' or Markdown. 
    11. FONTS: Intro <p> in Georgia (18px), Body <p> in Verdana.
    12. IMAGE PROTECTION: ONLY write the text [IMG1], [IMG2], [IMG3]. NEVER write <img> tags, alt text, or style attributes.
    """
    
    for model in models:
        try:
            client = InferenceClient(model=model, token=HF_TOKEN)
            response = client.chat_completion([{"role": "user", "content": prompt}], max_tokens=2500, temperature=0.8)
            content = response.choices[0].message.content
            
            # Cleaning: Remove any accidental Markdown hashes
            content = content.replace("#", "")
            return content
        except Exception as e:
            print(f"Model {model} failed. Error: {e}")
            time.sleep(2)
            
    return "Error: AI generation failed."

# --- 3. POSTING LOGIC ---
# --- 5. IMAGE LOGIC (Topic Related & Reliable) ---
def get_image_urls(topic):
    # Topic ko URL friendly banaya, special characters hataye
    safe_topic = topic.replace(" ", "%20").replace("&", "").replace("/", "").replace(":", "").replace('"', '')
    seed = random.randint(1, 10000) # Seed range badhaya for more variety

    # Image prompts ko aur specific aur descriptive banaya gaya hai
    # Har image ke liye alag focus
    img_prompts = [
        f"futuristic%20concept%20of%20{safe_topic}%20high%20tech%20digital%20art", # Overall concept
        f"detailed%20illustration%20of%20AI%20innovation%20related%20to%20{safe_topic}", # Technical/Innovation
        f"people%20interacting%20with%20{safe_topic}%20in%20a%20modern%20setting", # Real-world application
    ]
    
    image_urls = []
    for i, prompt_text in enumerate(img_prompts):
        # Pollinations.ai URL parameters adjust kiye hain for better results
        url = f"https://image.pollinations.ai/prompt/{prompt_text}?width=1024&height=576&nologo=true&seed={seed + i}&enhance=true"
        image_urls.append(url)
        
    return image_urls

def post_to_blogger():
    topic = get_trending_topic()
    final_labels = get_smart_labels(topic)
    full_response = generate_blog_post(topic)
    
    # Check for 3 parts: Title ||| Meta ||| Body
    if "|||" not in full_response: return

    parts = full_response.split("|||")
    
    # Logic for Title, Meta and Body separation
    raw_title = parts[0].strip().replace(":", "").replace('"', '')
    
    # Agar 3 parts hain to meta_desc lo, varna empty string
    meta_description = parts[1].strip()[:150] if len(parts) > 2 else ""
    content_html = parts[2].strip() if len(parts) > 2 else parts[1].strip()

    # Title Length Control (55 Chars)
    final_title = raw_title[:55].rsplit(' ', 1)[0] if len(raw_title) > 55 else raw_title
    
    # SEO Linking Logic (Internal & External)
    # Note: Authority link ke liye Wikipedia ya Research site use ki hai
    content_html = content_html.replace("[INTERNAL_LINK]", f'<a href="https://{os.getenv("BLOG_URL", "technovexa.blogspot.com")}">latest AI insights</a>')
    content_html = content_html.replace("[EXTERNAL_LINK]", '<a href="https://en.wikipedia.org/wiki/Artificial_intelligence" rel="nofollow">technical authority research</a>')

    # Schema Markup (JSON-LD) for SEO
    schema_markup = f"""
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "TechArticle",
      "headline": "{final_title}",
      "description": "{meta_description}",
      "author": {{ "@type": "Organization", "name": "Technovexa AI" }}
    }}
    </script>
    """
    
    images = get_image_urls(topic)
    img_style = 'style="width:100%; border-radius:10px; margin: 20px 0; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"'
    
    for i, img in enumerate(images):
        content_html = content_html.replace(f'[IMG{i+1}]', f'<img src="{img}" {img_style}><br>')

    # Final Body with Schema + Content
    final_body = f"""
    {schema_markup}
    <h1 style="text-align: center; font-family: 'Helvetica Neue', sans-serif; color: #2c3e50;">{final_title}</h1>
    <hr style="border:0; height:1px; background-image: linear-gradient(to right, #ccc, #333, #ccc);">
    {content_html}
    <p style="text-align:center; font-size:12px; color:#888;"><i>Article by Technovexa AI Intelligence</i></p>
    """

    service = get_blogger_service()
    
    # Final Post Body with Search Description
    post_body = {
        "title": final_title, 
        "content": final_body, 
        "labels": final_labels,
        "searchDescription": meta_description  # Adds the Meta Description to Blogger
    }
    
    service.posts().insert(blogId=BLOGGER_ID, body=post_body).execute()
    print(f"Posted: {final_title} | Tags: {final_labels} | SEO Optimized: Yes")

if __name__ == "__main__":
    post_to_blogger()
