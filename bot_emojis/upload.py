import base64
import requests
import os

from dotenv import load_dotenv

load_dotenv()
APP_ID = os.getenv("APP_ID")
TOKEN = os.getenv("TOKEN")
EMOJI_DIRECTIORY = 'bot_emojis\\data'

def upload_emoji(image_path: str):
    with open(image_path, "rb") as f:
        base64_data = base64.b64encode(f.read()).decode("ascii")

    image_data_uri = f"data:image/png;base64,{base64_data}"
    name = os.path.splitext(os.path.basename(image_path))[0]
    if name.startswith("icon_"):
        name = name[5:]
        
    url = f"https://discord.com/api/applications/{APP_ID}/emojis"
    headers = {
        "Authorization": f"Bot {TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "name": name,
        "image": image_data_uri
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()

def get_emoji_list():
    url = f"https://discord.com/api/applications/{APP_ID}/emojis"
    headers = {
        "Authorization": f"Bot {TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    emoji_list = get_emoji_list()

    existing_emojis = {emoji['name'] for emoji in emoji_list['items']}
    new_emojis = []
    
    # Don't async since it is easier to avoid rate limits this way
    for filename in os.listdir(EMOJI_DIRECTIORY):
        if filename.endswith(".png"):
            emoji_name = os.path.splitext(filename)[0]
            if emoji_name.startswith("icon_"):
                emoji_name = emoji_name[5:]
            if emoji_name not in existing_emojis:
                emoji = upload_emoji(os.path.join(EMOJI_DIRECTIORY, filename))
                new_emojis.append(emoji)
                print(f"Uploaded emoji: {emoji['name']} ({emoji['id']})")
                
    print(f"Uploaded {len(new_emojis)} new emojis.")
