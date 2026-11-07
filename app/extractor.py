
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

import pymupdf
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


def get_document_images(file_path: Path) -> list[dict]:
    """
    Convert an uploaded PDF or image into a list of
    base64-encoded images for Gemini.
    """

    images = []

    # Handle PDF files
    if file_path.suffix.lower() == ".pdf":

        pdf_document = pymupdf.open(file_path)

        try:
            for page_number, page in enumerate(pdf_document):

                pix = page.get_pixmap(
                    matrix=pymupdf.Matrix(2, 2),
                    alpha=False
                )

                image_bytes = pix.tobytes("png")

                image_base64 = base64.b64encode(
                    image_bytes
                ).decode("utf-8")

                images.append({
                    "type": "image",
                    "data": image_base64,
                    "mime_type": "image/png"
                })

                print(
                    f"Converted PDF page {page_number + 1}"
                )

        finally:
            pdf_document.close()

    # Handle JPG, JPEG and PNG files
    elif file_path.suffix.lower() in [".jpg", ".jpeg", ".png"]:

        mime_type, _ = mimetypes.guess_type(str(file_path))

        if not mime_type or not mime_type.startswith("image/"):
            raise ValueError("Unsupported image format.")

        image_bytes = file_path.read_bytes()

        image_base64 = base64.b64encode(
            image_bytes
        ).decode("utf-8")

        images.append({
            "type": "image",
            "data": image_base64,
            "mime_type": mime_type
        })

    else:
        raise ValueError(
            "Unsupported file format. Upload PDF, JPG, JPEG or PNG."
        )

    if not images:
        raise ValueError("No pages or images found in the document.")

    return images


def extract_invoice(image_path: str) -> InvoiceData:
    """
    Extract structured invoice information using Gemini.
    Supports PDF and image files.
    """

    image_file = Path(image_path)

    if not image_file.exists():
        raise FileNotFoundError(
            f"Invoice file not found: {image_path}"
        )

    try:

        # Convert document into Gemini-compatible images
        document_images = get_document_images(image_file)

        # Extraction instructions
        prompt = """
        You are an expert invoice data extraction assistant.

        Carefully examine ALL provided pages of the invoice.

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
        - Examine all pages before extracting information.
        - Treat multiple pages as parts of the same invoice
          when they belong to the same document.
        - Extract information only from the invoice.
        - Never invent missing information.
        - Use null for missing optional fields.
        - Extract all invoice items across all pages.
        - Do not duplicate items appearing on multiple pages.
        - Preserve the original item descriptions.
        - Convert dates to YYYY-MM-DD when possible.
        - Return numeric values for quantities and prices.
        - Distinguish unit price from line-item total.
        """

        # Available models
        models = [
            "gemini-3.6-flash"
        ]

        interaction = None
        last_error = None

        # Try each model
        for model in models:

            try:
                print(f"Trying model: {model}")

                # Combine prompt and all document pages
                gemini_input = [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]

                gemini_input.extend(document_images)

                interaction = client.interactions.create(
                    model=model,
                    input=gemini_input,
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
                "The uploaded document does not appear to be a valid invoice."
            )

        return invoice

    except Exception as error:
        raise RuntimeError(
            f"Invoice extraction failed: {error}"
        ) from error
