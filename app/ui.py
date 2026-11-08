import pymupdf
from PIL import Image
from io import BytesIO
import json
import csv
import io
from pathlib import Path

import streamlit as st

from app.extractor import extract_invoice
from app.validator import validate_invoice


st.set_page_config(
    page_title="Invoice AI Extractor",
    page_icon="🧾",
    layout="wide"
)

st.title("🧾 Invoice AI Extractor")
st.write(
    "Upload an invoice image or PDF to extract structured information "
    "and validate its financial calculations."
)

uploaded_file = st.file_uploader(
    "Upload an invoice",
    type=["pdf", "png", "jpg", "jpeg"]
)

if uploaded_file is not None:

    # Preview uploaded PDF
    if uploaded_file.type == "application/pdf":

        pdf_document = pymupdf.open(
            stream=uploaded_file.getvalue(),
            filetype="pdf"
        )

        first_page = pdf_document.load_page(0)

        pix = first_page.get_pixmap(
            matrix=pymupdf.Matrix(2, 2)
        )

        image = Image.open(
            BytesIO(pix.tobytes("png"))
        )

        st.image(
            image,
            caption="PDF Preview - Page 1",
            use_container_width="stretch"
        )

        if len(pdf_document) > 1:
            st.info(
                f"This PDF contains {len(pdf_document)} pages. "
                "The extractor will process all pages."
            )

        pdf_document.close()

    # Preview uploaded image
    else:
        st.image(
            uploaded_file,
            caption="Uploaded Invoice",
            use_container_width="stretch"
        )

    if st.button("Extract Invoice Data", type="primary"):

        try:
            with st.spinner("Analyzing invoice with AI..."):

                # Preserve the original file extension
                file_extension = Path(uploaded_file.name).suffix.lower()

                temporary_file = Path(
                    f"uploaded_invoice{file_extension}"
                )

                # Save uploaded file temporarily
                temporary_file.write_bytes(
                    uploaded_file.getvalue()
                )

                # Extract and validate invoice
                invoice = extract_invoice(
                    str(temporary_file)
                )

                validation = validate_invoice(invoice)

            st.success(
                "Invoice extraction completed. "
                "Review the validation results below."
            )

            result = invoice.model_dump()
            result["validation"] = validation

            st.subheader("Extracted Invoice Information")

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Invoice Number",
                invoice.invoice_number or "N/A"
            )

            col2.metric(
                "Supplier",
                invoice.supplier_name or "N/A"
            )

            col3.metric(
                "Total Amount",
                (
                    f"{invoice.total_amount:,.2f}"
                    if invoice.total_amount is not None
                    else "N/A"
                )
            )

            st.subheader("Invoice Items")

            items = [
                item.model_dump()
                for item in invoice.items
            ]

            if items:
                st.dataframe(
                    items,
                    use_container_width="stretch",
                    hide_index=True
                )
            else:
                st.info("No invoice items were extracted.")

            st.subheader("Financial Validation")

            if validation["is_valid"]:
                st.success(
                    "All critical validation checks passed."
                )
            else:
                st.warning(
                    "Invoice validation failed."
                )

            # Display missing fields
            if validation["missing_fields"]:
                st.warning(
                    "Some invoice information is missing:"
                )

                for field in validation["missing_fields"]:
                    st.write(f"- {field}")

            # Display financial validation errors
            if validation["errors"]:
                st.subheader("Validation Errors")

                for error in validation["errors"]:
                    st.error(error)

            # Display complete JSON output
            with st.expander("View Complete JSON Output"):
                st.json(result)

            # Download JSON
            st.download_button(
                label="Download Extracted JSON",
                data=json.dumps(result, indent=4),
                file_name="extracted_invoice.json",
                mime="application/json"
            )

            # Download CSV
            if invoice.items:

                csv_buffer = io.StringIO()

                csv_writer = csv.DictWriter(
                    csv_buffer,
                    fieldnames=[
                        "description",
                        "quantity",
                        "unit",
                        "unit_price",
                        "total"
                    ]
                )

                csv_writer.writeheader()

                for item in invoice.items:
                    csv_writer.writerow(
                        item.model_dump()
                    )

                st.download_button(
                    label="Download Invoice Items CSV",
                    data=csv_buffer.getvalue(),
                    file_name="invoice_items.csv",
                    mime="text/csv"
                )

        except Exception as error:
            st.error(
                f"Invoice processing failed: {error}"
            )
