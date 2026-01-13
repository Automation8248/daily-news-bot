import os
import random
import time
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from gradio_client import Client # Aapka naya tool

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
        "Artificial Intelligence Trends 2026", "SpaceX Starship Future", 
        "Electric Vehicles Revolution", "Wildlife Conservation", 
        "Latest VR Gadgets", "Ocean Cleanup Projects",
        "Solar Energy Innovations", "Robotics in Daily Life"
    ]
    return random.choice(topics)

# --- 2. AI CONTENT (USING GRADIO CLIENT) ---
def generate_blog_post(topic):
    print(f"Connecting to MiniMax AI for topic: {topic}...")
    
    try:
        # Aapka Diya Hua Client
        client = Client("ramuenugurthi/MiniMaxAI-MiniMax-M2")
        
        prompt = f"""
        Write a 400-word engaging blog post about: '{topic}'.
        Format strictly using HTML tags (<h2> for headings, <p> for paragraphs).
        Do NOT use <html> or <body> tags.
        Add a catchy title at the start.
        """
        
        # 'predict' function call kar rahe hain. 
        # Note: Aksar chat models ka API endpoint '/chat' ya '/predict' hota hai.
        # Hum standard input bhej rahe hain.
        result = client.predict(
            prompt, 
            api_name="/chat" # Agar ye fail ho to '/predict' try karenge
        )
        
        # Result kabhi-kabhi tuple ya list mein aata hai, use string banayenge
        return str(result)
        
    except Exception as e:
        print(f"AI Generation Failed: {e}")
        return "Error: Could not generate content."

# --- 3. POSTING ---
def get_image_url(topic):
    safe_topic = topic.replace(" ", "%20")
    # Pollinations AI for Image
    return f"https://image.pollinations.ai/prompt/cinematic%20photo%20of%20{safe_topic}%204k%20lighting?width=800&height=450&nologo=true"

def post_to_blogger():
    topic = get_trending_topic()
    
    content_html = generate_blog_post(topic)
    
    # Agar error aaya to post mat karo
    if "Error:" in content_html:
        print("Skipping post due to AI error.")
        return

    image_url = get_image_url(topic)
    
    # Blog post structure
    final_content = f'<a href="{image_url}"><img src="{image_url}" style="width:100%; border-radius:10px;"></a><br><br>{content_html}'
    
    # Title nikalna (Simple tareeka)
    title = f"Latest Update: {topic}"
    
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
