# Invoice AI Extractor

An AI-powered invoice processing application that extracts structured information from invoice images, validates financial calculations, and exports the results to JSON and CSV.

## Features

- Upload invoice images in PNG, JPG, and JPEG formats.
- Extract invoice information using Google's Gemini AI.
- Identify invoice number, date, supplier, line items, subtotal, VAT, and grand total.
- Validate line-item calculations and invoice totals.
- Detect non-invoice documents.
- Report missing invoice information.
- Display extracted invoice data in an interactive Streamlit interface.
- Download complete invoice data as JSON and CSV.
- Handle extraction errors with user-friendly messages.

## Technology Stack

- **Python** — application logic
- **Google Gemini API** — AI-based invoice extraction
- **Pydantic** — structured data validation
- **Streamlit** — web interface
- **Pandas / Python CSV** — data handling and export

## Project Structure

```text
invoice-ai-extractor/
├── app/
│   ├── __init__.py
│   ├── extractor.py
│   ├── schemas.py
│   ├── validator.py
│   └── ui.py
├── invoices/
│   └── sample_invoice.png
├── output/
├── .env.example
├── .gitignore
├── main.py
├── requirements.txt
└── README.md
```

## Application Workflow

1. User uploads an invoice image.
2. The application sends the image to Gemini for extraction.
3. Gemini returns structured invoice information.
4. Pydantic validates the extracted data structure.
5. The validation module checks line-item calculations, subtotal, VAT, and grand total.
6. Streamlit displays the extracted information and validation results.
7. User downloads the extracted data in JSON or CSV format.

## Installation and Setup

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd invoice-ai-extractor
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
```

Activate it on macOS or Linux:

```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
python3 -m pip install -r requirements.txt
```

### 4. Configure the API key

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Use your own Gemini API key. Never commit your `.env` file.

### 5. Run the application

```bash
python3 -m streamlit run app/ui.py
```

The application will open in your browser, usually at:

```text
http://localhost:8501
```

## Validation

The application performs checks such as:

- Quantity × unit price against line-item total.
- Sum of line items against invoice subtotal.
- Subtotal + VAT against grand total.
- Missing critical invoice information.

Validation results are displayed to the user so extracted information can be reviewed.

## Limitations

- Extraction accuracy depends on image quality and invoice layout.
- AI-generated values should be reviewed before accounting use.
- Financial validation currently uses basic calculation rules and may require adjustments for discounts, rounding, or other invoice-specific charges.
- The application is a prototype and is not yet integrated with an accounting or ERP system.

## Future Improvements

- Support PDF invoices.
- Add invoice history and database storage.
- Improve extraction accuracy for different invoice formats.
- Add batch invoice processing.
- Integrate with accounting systems.

## Author

Prabesh Thapa.
