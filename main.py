import os
import random
import requests
import google.generativeai as genai
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime

# --- 1. SETUP & AUTHENTICATION ---
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")
BLOGGER_ID = os.getenv("BLOGGER_BLOG_ID")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def get_blogger_service():
    creds = Credentials(
        None,
        refresh_token=REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )
    return build('blogger', 'v3', credentials=creds)

# --- 2. GET NEWS TOPIC ---
def get_trending_topic():
    # Aaj ki date ke hisaab se topic vary karega
    topics = [
        "Artificial Intelligence Breakthroughs", "Space Exploration Updates", 
        "Electric Vehicles Future", "Wildlife Conservation", 
        "Latest Smartphone Technology", "Green Energy Innovations"
    ]
    return random.choice(topics)

# --- 3. GENERATE CONTENT (GEMINI) ---
def generate_content(topic):
    prompt = f"""
    Write a viral blog post about '{topic}'.
    - Format strictly in HTML (use <h2>, <p>, <ul>).
    - Do NOT use <html>, <head>, or <body> tags.
    - Include interesting facts.
    - Length: Approx 400 words.
    """
    response = model.generate_content(prompt)
    return response.text

# --- 4. GENERATE IMAGE ---
def get_image_url(topic):
    safe_topic = topic.replace(" ", "%20")
    # Pollinations AI se High Quality Image
    return f"https://image.pollinations.ai/prompt/cinematic%20photo%20of%20{safe_topic}%204k%20lighting?width=800&height=450&nologo=true"

# --- 5. POST TO BLOGGER ---
def post_to_blogger():
    topic = get_trending_topic()
    print(f"Topic: {topic}")
    
    content_html = generate_content(topic)
    image_url = get_image_url(topic)
    
    # Title generate karein
    title = model.generate_content(f"Write a short clickbait title for: {topic}").text.strip()
    
    # Image ko HTML mein sabse upar lagayein
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
