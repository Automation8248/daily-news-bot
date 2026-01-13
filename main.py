import os
import time
import random
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# --- 1. CONFIGURATION ---
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")
BLOGGER_ID = os.getenv("BLOGGER_BLOG_ID")
HF_TOKEN = os.getenv("HF_TOKEN")

# FIX: Using Standard Inference URL for a reliable model (Zephyr)
API_URL = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

def get_blogger_service():
    creds = Credentials(
        None,
        refresh_token=REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )
    return build('blogger', 'v3', credentials=creds)

def get_trending_topic():
    topics = [
        "Artificial Intelligence in 2026", "SpaceX Starship Updates", 
        "Future of Electric Cars", "Save Tigers Campaign", 
        "New VR Tech Gadgets", "Ocean Cleanup Success",
        "Solar Energy Breakthroughs", "Robots in Daily Life"
    ]
    return random.choice(topics)

# --- 2. AI CONTENT GENERATION (WITH RETRY) ---
def query_huggingface(prompt):
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 500, "return_full_text": False},
        "options": {"wait_for_model": True} # FIX: Tells HF to wait if model is loading
    }
    
    # Retry loop (3 koshish karega agar fail hua toh)
    for i in range(3):
        response = requests.post(API_URL, headers=HEADERS, json=payload)
        if response.status_code == 200:
            try:
                return response.json()[0]['generated_text']
            except:
                return response.text
        
        print(f"Attempt {i+1} failed: {response.text}")
        time.sleep(10) # 10 second ruk kar try karega
        
    return "Error: Could not generate content after 3 attempts."

def generate_blog_post(topic):
    prompt = f"""
    Write a 300-word engaging blog post about: '{topic}'.
    Format using HTML tags (<h2> for headings, <p> for paragraphs).
    Do NOT use <html> or <body> tags.
    Make it exciting!
    """
    return query_huggingface(prompt)

# --- 3. IMAGE & POSTING ---
def get_image_url(topic):
    safe_topic = topic.replace(" ", "%20")
    return f"https://image.pollinations.ai/prompt/cinematic%20photo%20of%20{safe_topic}%204k%20lighting?width=800&height=450&nologo=true"

def post_to_blogger():
    topic = get_trending_topic()
    print(f"Topic: {topic}")
    
    content_html = generate_blog_post(topic)
    
    # Agar content fail hua toh post mat karo
    if "Error:" in content_html:
        print("Skipping post due to AI error.")
        return

    image_url = get_image_url(topic)
    title = f"Must Read: {topic}"
    final_content = f'<a href="{image_url}"><img src="{image_url}" style="width:100%; border-radius:10px;"></a><br><br>{content_html}'
    
    service = get_blogger_service()
    body = {
        "kind": "blogger#post",
        "blog": {"id": BLOGGER_ID},
        "title": title,
        "content": final_content
    }
    
    service.posts().insert(blogId=BLOGGER_ID, body=body).execute()
    print(f"Successfully posted: {title}")

if __name__ == "__main__":
    post_to_blogger()
