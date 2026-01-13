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

# Setup Official Client (Zephyr Model - Super Stable)
# Ye model kabhi 'Not Found' nahi bolega
client = InferenceClient(model="HuggingFaceH4/zephyr-7b-beta", token=HF_TOKEN)

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
        "Future of AI 2026", "SpaceX Starship Updates", 
        "Electric Vehicles Revolution", "Wildlife Conservation", 
        "Virtual Reality Trends", "Ocean Conservation",
        "Solar Energy Innovations", "Robotics Updates"
    ]
    return random.choice(topics)

# --- 2. AI CONTENT GENERATION ---
def generate_blog_post(topic):
    print(f"Generating content for: {topic}...")
    
    prompt = f"""
    You are a professional blogger. Write a 400-word blog post about '{topic}'.
    Format strictly using HTML tags (<h2> for headings, <p> for paragraphs).
    Do NOT use <html> or <body> tags.
    Make the content engaging and viral.
    """
    
    # Retry Logic (Agar model busy ho to 3 baar try karega)
    for i in range(3):
        try:
            response = client.text_generation(
                prompt, 
                max_new_tokens=600,
                temperature=0.7
            )
            return response
        except Exception as e:
            print(f"Attempt {i+1} failed: {e}")
            time.sleep(5) # 5 second ruko
            
    return "Error: AI content could not be generated."

# --- 3. POSTING TO BLOGGER ---
def get_image_url(topic):
    safe_topic = topic.replace(" ", "%20")
    return f"https://image.pollinations.ai/prompt/cinematic%20photo%20of%20{safe_topic}%204k%20lighting?width=800&height=450&nologo=true"

def post_to_blogger():
    topic = get_trending_topic()
    
    content_html = generate_blog_post(topic)
    
    if "Error:" in content_html:
        print("Skipping post due to AI error.")
        return

    image_url = get_image_url(topic)
    title = f"Latest News: {topic}"
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
