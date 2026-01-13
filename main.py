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
    
    # Backup Models List
    models_to_try = [
        "mistralai/Mistral-7B-Instruct-v0.3",
        "microsoft/Phi-3.5-mini-instruct",
        "Qwen/Qwen2.5-72B-Instruct"
    ]
    
    # Prompt mein hum AI ko bol rahe hain ki structure kaisa rakhna hai
    prompt = f"""
    You are a professional blogger. Write a detailed blog post about '{topic}'.
    
    Follow this structure STRICTLY:
    1. Start with one engaging Intro Paragraph (<p style="font-family: Georgia, serif; font-size: 18px;">).
    2. Write '[IMG1]' exactly here.
    3. Then write 8 to 9 distinct Subheadings using <h3> tags.
    4. Under each subheading, write a detailed paragraph using <p style="font-family: Verdana, sans-serif;"> tags.
    5. Insert '[IMG2]' somewhere in the middle (after 3rd subheading).
    6. Insert '[IMG3]' near the end (after 7th subheading).
    
    DO NOT output the Main Title (H1). Start directly with the intro paragraph.
    """
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant that writes HTML formatted blog posts."},
        {"role": "user", "content": prompt}
    ]
    
    for model in models_to_try:
        print(f"Trying model: {model}...")
        try:
            client = InferenceClient(model=model, token=HF_TOKEN)
            response = client.chat_completion(
                messages, 
                max_tokens=1500, # Word count badha diya hai
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Model {model} failed: {e}")
            time.sleep(2)
            
    return "Error: All AI models failed."

# --- 3. IMAGES & POSTING ---
def get_image_urls(topic):
    # 3 Alag-alag images generate karenge
    safe_topic = topic.replace(" ", "%20")
    base_url = "https://image.pollinations.ai/prompt"
    
    img1 = f"{base_url}/cinematic%20photo%20of%20{safe_topic}%20overview%204k?width=800&height=450&nologo=true&seed={random.randint(1,1000)}"
    img2 = f"{base_url}/detailed%20closeup%20of%20{safe_topic}%20technology?width=800&height=450&nologo=true&seed={random.randint(1,1000)}"
    img3 = f"{base_url}/futuristic%20view%20of%20{safe_topic}?width=800&height=450&nologo=true&seed={random.randint(1,1000)}"
    
    return [img1, img2, img3]

def post_to_blogger():
    topic = get_trending_topic()
    
    # 1. Content Generate karo
    content_html = generate_blog_post(topic)
    
    if "Error:" in content_html:
        print("Skipping post due to AI error.")
        return

    # 2. Images Generate karo
    images = get_image_urls(topic)
    
    # 3. Content mein Images fit karo (Replace placeholders)
    # Image style add kiya hai taaki wo center aur sundar dikhe
    img_style = 'style="width:100%; border-radius:10px; margin: 20px 0;"'
    
    content_html = content_html.replace('[IMG1]', f'<img src="{images[0]}" {img_style}><br>')
    content_html = content_html.replace('[IMG2]', f'<img src="{images[1]}" {img_style}><br>')
    content_html = content_html.replace('[IMG3]', f'<img src="{images[2]}" {img_style}><br>')
    
    # 4. Final HTML Structure Assemble karo
    # Sabse upar Heading (H1), fir AI ka content (jisme Intro > Img > Subheadings hain)
    final_body = f"""
    <h1 style="text-align: center; color: #333;">{topic}</h1>
    <hr>
    {content_html}
    """
    
    # 5. Title (Sirf Topic ka naam, koi "Latest News" nahi)
    clean_title = topic
    
    service = get_blogger_service()
    body = {
        "kind": "blogger#post",
        "blog": {"id": BLOGGER_ID},
        "title": clean_title,
        "content": final_body
    }
    
    service.posts().insert(blogId=BLOGGER_ID, body=body).execute()
    print(f"Successfully posted: {clean_title}")

if __name__ == "__main__":
    post_to_blogger()
