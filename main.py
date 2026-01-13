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

# --- STRICT TECH & AI TOPICS ---
def get_trending_topic():
    topics = [
        "Future of Generative AI 2026", 
        "Nvidia New AI Chip Review", 
        "OpenAI Sora Video Tools", 
        "Humane AI Pin Features", 
        "Python Automation Tricks", 
        "Latest Android 16 Updates",
        "Quantum Computing Progress", 
        "Tesla Optimus Robot News"
    ]
    return random.choice(topics)

# --- 2. AI CONTENT GENERATION (HUMANIZED) ---
def generate_blog_post(topic):
    print(f"Generating humanized content for: {topic}...")
    
    models_to_try = [
        "mistralai/Mistral-7B-Instruct-v0.3",
        "microsoft/Phi-3.5-mini-instruct",
        "Qwen/Qwen2.5-72B-Instruct"
    ]
    
    # Prompt mein 'No Colons' ka strict instruction add kiya hai
    prompt = f"""
    Act as a senior Tech Journalist. Write a blog post about '{topic}'.
    
    IMPORTANT INSTRUCTIONS FOR HUMAN-LIKE WRITING:
    - Use a conversational, engaging tone (use "we", "I", rhetorical questions).
    - Avoid robotic transitions like "In conclusion", "Moreover".
    - Keep sentences varied in length to increase burstiness.
    
    STRUCTURE REQUIREMENTS:
    1. First line: Write a Simple Title (Max 55 chars). DO NOT use colons (:). Keep it direct.
    2. Second line: Write "|||" (This is a separator).
    3. Third line onwards: The HTML Body.
       - Start with a strong Intro Paragraph (<p style="font-family: Georgia, serif; font-size: 18px;">).
       - Write '[IMG1]' placeholder.
       - Add 6-8 Subheadings (<h3>) with detailed paragraphs (<p style="font-family: Verdana, sans-serif;">).
       - Insert '[IMG2]' after the 3rd subheading.
       - Insert '[IMG3]' near the end.
       - DO NOT output <html>, <head>, or <body> tags.
    """
    
    messages = [
        {"role": "system", "content": "You are a tech blogger. Never use colons in titles."},
        {"role": "user", "content": prompt}
    ]
    
    for model in models_to_try:
        try:
            client = InferenceClient(model=model, token=HF_TOKEN)
            response = client.chat_completion(messages, max_tokens=1800, temperature=0.8)
            return response.choices[0].message.content
        except Exception as e:
            print(f"Model {model} failed: {e}")
            time.sleep(2)
            
    return "Error: All AI models failed."

# --- 3. IMAGES & POSTING ---
def get_image_urls(topic):
    safe_topic = topic.replace(" ", "%20")
    base_url = "https://image.pollinations.ai/prompt"
    img1 = f"{base_url}/futuristic%20tech%20{safe_topic}%20cyberpunk?width=800&height=450&nologo=true&seed={random.randint(1,1000)}"
    img2 = f"{base_url}/detailed%20circuit%20ai%20{safe_topic}?width=800&height=450&nologo=true&seed={random.randint(1,1000)}"
    img3 = f"{base_url}/human%20using%20technology%20{safe_topic}?width=800&height=450&nologo=true&seed={random.randint(1,1000)}"
    return [img1, img2, img3]

def post_to_blogger():
    topic = get_trending_topic()
    
    full_response = generate_blog_post(topic)
    
    if "Error:" in full_response or "|||" not in full_response:
        print("Skipping due to formatting error.")
        return

    # --- SEPARATE TITLE AND BODY ---
    try:
        parts = full_response.split("|||")
        raw_title = parts[0].strip().replace('"', '').replace("Title:", "")
        content_html = parts[1].strip()
    except:
        raw_title = topic
        content_html = full_response

    # --- LOGIC: REMOVE COLONS & LIMIT LENGTH ---
    # 1. Colon (:) Hatao Logic
    final_title = raw_title.replace(":", "")  # Colon ko delete kar dega
    final_title = final_title.replace("  ", " ") # Double space ko single karega

    # 2. 55 Character Logic
    if len(final_title) > 55:
        shortened = final_title[:55]
        last_space = shortened.rfind(' ')
        if last_space != -1:
            final_title = shortened[:last_space]
        else:
            final_title = shortened

    if len(final_title) < 10:
        final_title = f"{topic} Updates"

    print(f"Original Title: {raw_title}")
    print(f"Cleaned Title (No Colon): {final_title}")

    # Images Lagana
    images = get_image_urls(topic)
    img_style = 'style="width:100%; border-radius:10px; margin: 20px 0; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"'
    
    content_html = content_html.replace('[IMG1]', f'<img src="{images[0]}" {img_style}><br>')
    content_html = content_html.replace('[IMG2]', f'<img src="{images[1]}" {img_style}><br>')
    content_html = content_html.replace('[IMG3]', f'<img src="{images[2]}" {img_style}><br>')
    
    # Blogger Body
    final_body = f"""
    <h1 style="text-align: center; font-family: 'Helvetica Neue', sans-serif; color: #2c3e50;">{final_title}</h1>
    <hr style="border: 0; height: 1px; background: #333; background-image: linear-gradient(to right, #ccc, #333, #ccc);">
    {content_html}
    <br>
    <p style="text-align:center; font-size:12px; color: #888;"><i>Generated by TechBot AI</i></p>
    """
    
    service = get_blogger_service()
    body = {
        "kind": "blogger#post",
        "blog": {"id": BLOGGER_ID},
        "title": final_title,
        "content": final_body
    }
    
    service.posts().insert(blogId=BLOGGER_ID, body=body).execute()
    print(f"Successfully posted: {final_title}")

if __name__ == "__main__":
    post_to_blogger()
