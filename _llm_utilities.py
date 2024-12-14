def image_to_url(image):
    """
    Convert an image to a URL.
    """
    if isinstance(image, str) and (image.startswith("data:image") or image.startswith("http")):
        return image

    import base64
    import io
    from PIL import Image

    if isinstance(image, str):
        return image

    if isinstance(image, bytes):
        image = Image.open(io.BytesIO(image))

    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str


def prompt_azure(message: str, model="gpt-4o", image=None):
    """A prompt helper function that sends a message to Azure's OpenAI Service
    and returns only the text response.
    """
    import os

    token = os.environ["GH_MODELS_API_KEY"]
    endpoint = "https://models.inference.ai.azure.com"
    model = model.replace("github_models:", "")

    from azure.ai.inference import ChatCompletionsClient
    from azure.ai.inference.models import SystemMessage, UserMessage
    from azure.core.credentials import AzureKeyCredential

    client = ChatCompletionsClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(token),
    )

    if isinstance(message, str):
        message = [UserMessage(content=message)]
    if image is not None:
        image_url = image_to_url(image)
        message = [UserMessage(
                content=[
                    TextContentItem(text=message),
                    ImageContentItem(image_url={"url": "data:image/png;base64," + image_url}),
                ],
            )]


    response = client.complete(
        messages=message,
        temperature=1.0,
        top_p=1.0,
        max_tokens=4096,
        model=model
    )

    return response.choices[0].message.content