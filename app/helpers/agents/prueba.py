from google import genai
from google.genai import types
import pathlib
import asyncio
import os

API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

filepath = pathlib.Path('app/helpers/agents/parametrosINTEXT.PDF')

async def summary():
    prompt = "Summarize this document"
    response = await client.aio.models.generate_content(
    model="gemini-2.5-flash",
    contents=[
        types.Part.from_bytes(
            data=filepath.read_bytes(),
            mime_type='application/pdf',
        ),
        prompt])

    return response.text

async def main():
    try:
        summary_text = await summary()
        print("Summary of the document:")
        print(summary_text)
    except FileNotFoundError:
        print(f"Error: The file '{filepath}' was not found. Please check the file path.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main()) # Run the main async function