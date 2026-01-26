import os
import random
import time
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from openai import OpenAI

# --- 1. CONFIGURATION ---
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")
BLOGGER_ID = os.getenv("BLOGGER_BLOG_ID")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") 

def get_blogger_service():
    creds = Credentials(
        None,
        refresh_token=REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )
    return build('blogger', 'v3', credentials=creds)

# --- SEO STRATEGY TOPICS ---
def get_trending_topic():
    topics = [
        "Artificial Intelligence Latest News", "Generative AI Updates", 
        "AI Models GPT Gemini Claude", "Machine Learning Breakthroughs", 
        "Deep Learning Innovations", "AI Automation in Industries", 
        "Google AI & Technology News", "OpenAI Latest Updates", 
        "Microsoft AI & Tech News", "Meta AI Developments", 
        "Future Technology Trends", "Emerging Technologies", 
        "Cyber Security Threats & Fixes", "Cloud Computing News", 
        "New AI Tools Launch", "Free AI Tools News", 
        "AI Trends 2026", "Technology Trends 2026", 
        "Global Technology News", "India AI & Tech News"
    ]
    return random.choice(topics)

# --- SMART LABELS ---
def get_smart_labels(topic):
    topic_lower = topic.lower()
    selected_labels = []
    
    if any(x in topic_lower for x in ["ai", "gpt", "gemini", "learning"]):
        selected_labels.extend(["AI News", "AI Updates"])
    else:
        selected_labels.extend(["Technology News", "Tech Updates"])

    if "2026" in topic_lower: selected_labels.append("Future Tech")
    if "google" in topic_lower: selected_labels.append("Google News")
    elif "openai" in topic_lower: selected_labels.append("OpenAI News")
    
    unique_labels = list(set(selected_labels))
    if len(unique_labels) < 2: unique_labels.append("Latest Tech")
    return unique_labels[:5]

# --- 2. AI CONTENT GENERATION ---
def generate_blog_post(topic):
    print(f"Generating optimized content for: {topic} using DeepSeek R1...")
    
    client = OpenAI(
        base_url="https://models.inference.ai.azure.com",
        api_key=GITHUB_TOKEN,
    )
    
    prompt = f"""
    You are a professional tech journalist. Write a blog post about: '{topic}'.
    
    STRICT OUTPUT FORMAT (Do not include any introductory text):
    Title: [Insert Title Here]
    |||
    Description: [Insert 140 char meta description]
    |||
    [Start Body Content Here with HTML <h3> for headings. Do NOT use Markdown symbols like ##]
    
    Make the content engaging, human-like, and SEO optimized. Include a FAQ section.
    """
    
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant that strictly follows formatting instructions."},
                {"role": "user", "content": prompt}
            ],
            model="DeepSeek-R1",
            temperature=0.7,
            max_tokens=4000,
        )

        content = response.choices[0].message.content
        
        # Remove <think> blocks if present
        if "</think>" in content:
            content = content.split("</think>")[-1].strip()

        content = content.replace("#", "") # Remove accidental markdown
        return content

    except Exception as e:
        print(f"DeepSeek generation failed. Error: {e}")
        return None

# --- 3. POSTING LOGIC ---
def get_image_urls(topic):
    safe_topic = topic.replace(" ", "%20")
    seed = random.randint(1, 10000)
    img_prompts = [
        f"futuristic%20concept%20of%20{safe_topic}", 
        f"technology%20illustration%20{safe_topic}", 
        f"modern%20tech%20background%20{safe_topic}"
    ]
    image_urls = []
    for i, prompt in enumerate(img_prompts):
        url = f"https://image.pollinations.ai/prompt/{prompt}?width=1024&height=576&nologo=true&seed={seed + i}&enhance=true"
        image_urls.append(url)
    return image_urls

def post_to_blogger():
    topic = get_trending_topic()
    full_response = generate_blog_post(topic)
    
    if not full_response:
        print("Error: No response from AI.")
        return

    # --- UPDATED PARSING LOGIC (FAIL-SAFE) ---
    print("DEBUG: Processing AI Response...")
    
    if "|||" in full_response:
        parts = full_response.split("|||")
        raw_title = parts[0].replace("Title:", "").strip()
        meta_description = parts[1].replace("Description:", "").strip() if len(parts) > 1 else ""
        content_html = parts[2].strip() if len(parts) > 2 else parts[1]
    else:
        # Fallback agar AI ne format follow nahi kiya
        print("Warning: AI missed '|||' format. Using fallback mode.")
        lines = full_response.strip().split('\n')
        # Pehli non-empty line ko title maan lete hain
        raw_title = lines[0].replace("Title:", "").strip() if lines else topic
        meta_description = f"Latest updates on {topic}."
        # Baaki sab content
        content_html = "\n".join(lines[1:])

    # Title Cleanup
    final_title = raw_title[:60].strip()
    
    # Internal/External Links
    content_html = content_html.replace("[INTERNAL_LINK]", f'<a href="https://{os.getenv("BLOG_URL", "technovexa.blogspot.com")}">read more</a>')
    
    # Images Add Karna
    images = get_image_urls(topic)
    img_style = 'style="width:100%; border-radius:10px; margin: 20px 0;"'
    for i, img in enumerate(images):
        if i == 0: # Add first image at top
            content_html = f'<img src="{img}" {img_style}><br>{content_html}'
        else: # Add others inside text (simple append for fallback)
            content_html += f'<br><img src="{img}" {img_style}>'

    final_body = f"""
    <div style="font-family: Verdana, sans-serif; font-size: 16px; color: #333;">
        {content_html}
        <p><i>Article generated by Technovexa AI</i></p>
    </div>
    """

    service = get_blogger_service()
    post_body = {
        "title": final_title, 
        "content": final_body, 
        "labels": get_smart_labels(topic),
        "searchDescription": meta_description
    }
    
    try:
        service.posts().insert(blogId=BLOGGER_ID, body=post_body).execute()
        print(f"SUCCESS: Posted '{final_title}'")
    except Exception as e:
        print(f"Error posting to Blogger: {e}")

if __name__ == "__main__":
    post_to_blogger()
