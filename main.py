import os
import random
import time
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from gradio_client import Client

# --- 1. CONFIGURATION ---
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")
BLOGGER_ID = os.getenv("BLOGGER_BLOG_ID")

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
        "AI Technology 2026", "SpaceX Future Missions", 
        "Electric Cars Updates", "Wildlife Conservation", 
        "Virtual Reality Gadgets", "Ocean Cleanup News",
        "Solar Energy Trends", "Robotics Innovations"
    ]
    return random.choice(topics)

# --- 2. AI CONTENT (FIXED API NAME) ---
def generate_blog_post(topic):
    print(f"Connecting to MiniMax AI for topic: {topic}...")
    
    try:
        client = Client("ramuenugurthi/MiniMaxAI-MiniMax-M2")
        
        prompt = f"""
        Write a 300-word engaging blog post about: '{topic}'.
        Format using HTML tags (<h2> for headings, <p> for paragraphs).
        Do NOT use <html> or <body> tags.
        """
        
        # CHANGE: '/chat' ko hatakar '/predict' kiya hai
        result = client.predict(
            prompt, 
            api_name="/predict"
        )
        
        # Result tuple ho sakta hai, isliye string mein convert kar rahe hain
        return str(result)
        
    except Exception as e:
        print(f"AI Generation Failed: {e}")
        # Fallback: Agar ye fail ho to user ko error dikhaye
        return "Error: Could not generate content."

# --- 3. POSTING ---
def get_image_url(topic):
    safe_topic = topic.replace(" ", "%20")
    return f"https://image.pollinations.ai/prompt/cinematic%20photo%20of%20{safe_topic}%204k%20lighting?width=800&height=450&nologo=true"

def post_to_blogger():
    topic = get_trending_topic()
    
    content_html = generate_blog_post(topic)
    
    # Agar content "Error" se shuru ho raha hai to post mat karo
    if content_html.startswith("Error"):
        print("Skipping post due to AI error.")
        return

    image_url = get_image_url(topic)
    title = f"Latest Update: {topic}"
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
