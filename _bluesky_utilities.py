import os
from atproto import Client, client_utils, models


def pretty_print(s):
    """Helper function for debugging. It prints out atproto objects nicely."""
    indent = 0
    result = []
    opening = '([{'
    closing = ')]}'
    s = str(s).replace(", ",",")
    
    i = 0
    while i < len(s):
        char = s[i]
        
        # Handle opening brackets
        if char in opening:
            result.append(char + '\n' + '  ' * (indent + 1))
            indent += 1
            
        # Handle closing brackets
        elif char in closing:
            result.append('\n' + '  ' * (indent - 1) + char)
            indent -= 1
            
        # Handle commas
        elif char == ',':
            result.append(char + '\n' + '  ' * indent)
            
        # Handle other characters
        else:
            result.append(char)
            
        i += 1
    
    print(''.join(result))

def send_post(message, link=None, image_filename=None):
    """Send a message as a new post"""
    # Login to bluesky
    BLUESKY_HANDLE = os.environ.get("BLUESKY_USERNAME", "")
    APP_PASSWORD = os.environ.get("BLUESKY_API_KEY", "")
    
    client = Client()
    client.login(BLUESKY_HANDLE, APP_PASSWORD)
    
    text = client_utils.TextBuilder().text(message)
    if link is not None:
        text = text.link(link, link)
    
    print("tweeting:", text)

    if image_filename is not None:
        with open(image_filename, 'rb') as f:
            img_data = f.read()

        post = client.send_image(
            text=text,
            image=img_data,
            image_alt=''
        )
    else:
        post = client.send_post(text)

    id = post.uri.split("/")[-1]
    link = f"https://bsky.app/profile/{BLUESKY_HANDLE}/post/{id}"
    
    return link
