import os
import random
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# --- 1. SETUP & AUTHENTICATION ---
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")
BLOGGER_ID = os.getenv("BLOGGER_BLOG_ID")
HF_TOKEN = os.getenv("HF_TOKEN") # Hugging Face Token

# Hugging Face API URL (Mistral 7B Model - Fast & Free)
# Updated URL (Router wala)
API_URL = "https://router.huggingface.co/mistralai/Mistral-7B-Instruct-v0.3"
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

# --- 2. GET NEWS TOPIC ---
def get_trending_topic():
    topics = [
        "Artificial Intelligence Breakthroughs", "Space Exploration 2025", 
        "Future of Electric Vehicles", "Wildlife Conservation Efforts", 
        "New Smartphone Technologies", "Green Energy Innovations",
        "Robotics in Daily Life", "Ocean Cleaning Projects"
    ]
    return random.choice(topics)

# --- 3. GENERATE CONTENT (USING HUGGING FACE) ---
def query_huggingface(prompt):
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 600, "return_full_text": False}
    }
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    
    # Error handling
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return "Content generation failed."
        
    return response.json()[0]['generated_text']

def generate_blog_post(topic):
    prompt = f"""
    Write a professional and engaging blog post about: {topic}.
    Format the output in HTML (use <h2> for headings, <p> for paragraphs).
    Do NOT use <html> or <body> tags.
    Keep it interesting and under 400 words.
    """
    return query_huggingface(prompt)

# --- 4. GENERATE IMAGE ---
def get_image_url(topic):
    safe_topic = topic.replace(" ", "%20")
    # Pollinations AI (Free)
    return f"https://image.pollinations.ai/prompt/cinematic%20photo%20of%20{safe_topic}%204k%20lighting?width=800&height=450&nologo=true"

# --- 5. POST TO BLOGGER ---
def post_to_blogger():
    topic = get_trending_topic()
    print(f"Topic: {topic}")
    
    content_html = generate_blog_post(topic)
    image_url = get_image_url(topic)
    
    # Create Title
    title = f"Latest Update: {topic}" 
    
    # Combine Image + Text
    final_content = f'<a href="{image_url}"><img src="{image_url}" style="width:100%; border-radius:10px;"></a><br><br>{content_html}'
    
    service = get_blogger_service()
    body = {
        "kind": "blogger#post",
        "blog": {"id": BLOGGER_ID},
        "title": title,
        "content": final_content
    }
    
    try:
        service.posts().insert(blogId=BLOGGER_ID, body=body).execute()
        print(f"Successfully posted: {title}")
    except Exception as e:
        print(f"Failed to post: {e}")

if __name__ == "__main__":
    post_to_blogger()
