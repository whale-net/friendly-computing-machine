from temporalio import activity
import google.generativeai as genai


@activity.defn
async def generate_gemini_response(
    prompt_text: str,
) -> str:
    """
    Generate a response using the Gemini AI model.
    """
    model = genai.GenerativeModel()
    response = await model.generate_content_async(prompt_text)
    return response.text
