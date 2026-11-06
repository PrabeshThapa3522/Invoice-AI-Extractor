
# import os
# from pathlib import Path

# from dotenv import load_dotenv
# from google import genai
# from google.genai import types
# from PIL import Image

# from app.schemas import InvoiceData


# # Load environment variables from .env
# load_dotenv()

# # Read Gemini API key
# API_KEY = os.getenv("GEMINI_API_KEY")

# if not API_KEY:
#     raise ValueError(
#         "GEMINI_API_KEY is missing. Please check your .env file."
#     )

# # Initialize Gemini client
# client = genai.Client(api_key=API_KEY)


# def extract_invoice(image_path: str) -> InvoiceData:
#     """
#     Extract invoice information from an image using Gemini AI.
#     """

#     image_file = Path(image_path)

#     # Check whether the image exists
#     if not image_file.exists():
#         raise FileNotFoundError(
#             f"Invoice image not found: {image_path}"
#         )

#     try:
#         # Open invoice image
#         with Image.open(image_file) as image:
#             image.load()

#             prompt = """
#             You are an expert invoice data extraction assistant.

#             Carefully examine the supplied invoice image.

#             Extract the following information:
#             1. Invoice number
#             2. Invoice date
#             3. Supplier name
#             4. Every invoice item:
#                - Description
#                - Quantity
#                - Unit
#                - Unit price
#                - Line-item total
#             5. Subtotal
#             6. VAT
#             7. Final total amount

#             Important instructions:
#             - Extract information only from the invoice.
#             - Do not invent missing information.
#             - Use null for missing fields.
#             - Preserve the original meaning of descriptions.
#             - Convert dates to YYYY-MM-DD when possible.
#             - Return numeric values for prices and quantities.
#             - Do not confuse unit price with line-item total.
#             - Extract every item, not just the first one.
#             """

#             # Send image and prompt to Gemini
#             response = client.models.generate_content(
#                 model="gemini-3.6-flash",
#                 contents=[prompt, image],
#                 config=types.GenerateContentConfig(
#                     response_mime_type="application/json",
#                     response_schema=InvoiceData,
#                 ),
#             )

#             if not response.text:
#                 raise ValueError(
#                     "Gemini returned an empty response."
#                 )

#             # Convert AI response into validated Pydantic data
#             invoice_data = InvoiceData.model_validate_json(
#                 response.text
#             )

#             return invoice_data

#     except Exception as error:
#         raise RuntimeError(
#             f"Invoice extraction failed: {error}"
#         ) from error


import os
import base64
import mimetypes
from pathlib import Path

from dotenv import load_dotenv
from google import genai

from app.schemas import InvoiceData


# Load environment variables
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY is missing from .env")

# Initialize Gemini client
client = genai.Client(api_key=API_KEY)


def extract_invoice(image_path: str) -> InvoiceData:
    """
    Extract structured invoice information using Gemini.
    """

    image_file = Path(image_path)

    if not image_file.exists():
        raise FileNotFoundError(
            f"Invoice image not found: {image_path}"
        )

    try:
        # Identify image format
        mime_type, _ = mimetypes.guess_type(image_file)

        if not mime_type or not mime_type.startswith("image/"):
            raise ValueError("Unsupported image format.")

        # Read and encode image
        image_bytes = image_file.read_bytes()
        image_base64 = base64.b64encode(
            image_bytes
        ).decode("utf-8")

        # Extraction instructions
        prompt = """
        You are an expert invoice data extraction assistant.

        Carefully examine the provided invoice image.

        Extract:
        1. Invoice number
        2. Invoice date
        3. Supplier name
        4. Every invoice item:
           - Description
           - Quantity
           - Unit
           - Unit price
           - Line item total
        5. Subtotal
        6. VAT
        7. Final total amount

        Important instructions:
        - Extract information only from the invoice.
        - Never invent missing information.
        - Use null for missing optional fields.
        - Extract all invoice items.
        - Preserve the original item descriptions.
        - Convert dates to YYYY-MM-DD when possible.
        - Return numeric values for quantities and prices.
        - Distinguish unit price from line-item total.
        """

        # Available models
        models = [
            # "gemini-3.8-flash",
            # "gemini-3.7-flash",
            "gemini-3.6-flash",
            # "gemini-3.5-flash"
        ]

        interaction = None
        last_error = None

        # Try each model
        for model in models:
            try:
                print(f"Trying model: {model}")

                interaction = client.interactions.create(
                    model=model,
                    input=[
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image",
                            "data": image_base64,
                            "mime_type": mime_type
                        }
                    ],
                    response_format={
                        "type": "text",
                        "mime_type": "application/json",
                        "schema": InvoiceData.model_json_schema()
                    }
                )

                if not interaction.output_text:
                    raise ValueError("Empty response from Gemini")

                print(f"Successfully processed using {model}")
                break

            except Exception as error:
                last_error = error
                interaction = None
                print(f"{model} failed: {error}")

        # Check whether all models failed
        if interaction is None or not interaction.output_text:
            raise RuntimeError(
                f"All Gemini models failed. Last error: {last_error}"
            )

        # Validate the returned JSON
        invoice = InvoiceData.model_validate_json(
            interaction.output_text
        )
        
        if not invoice.is_invoice:
            raise ValueError(
                "The uploaded document is not appear to be a validate invoice."
            )

        return invoice

    except Exception as error:
        raise RuntimeError(
            f"Invoice extraction failed: {error}"
        ) from error
