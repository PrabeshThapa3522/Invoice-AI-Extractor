import json
import csv
import io
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
    "Upload an invoice image to extract structured information "
    "and validate its financial calculations."
)

uploaded_file = st.file_uploader(
    "Upload an invoice image",
    type=["png", "jpg", "jpeg"]
)

if uploaded_file is not None:
    st.image(
        uploaded_file,
        caption="Uploaded Invoice",
        width=500
    )

    if st.button("Extract Invoice Data", type="primary"):
        try:
            with st.spinner("Analyzing invoice with AI..."):
                # Save uploaded image temporarily
                with open("uploaded_invoice.png", "wb") as file:
                    file.write(uploaded_file.getvalue())

                invoice = extract_invoice("uploaded_invoice.png")
                validation = validate_invoice(invoice)

            st.success("Invoice extraction completed. Review the validation results below.")

            result = invoice.model_dump()
            result["validation"] = validation

            st.subheader("Extracted Invoice Information")

            col1, col2, col3 = st.columns(3)

            col1.metric("Invoice Number", invoice.invoice_number or "N/A")
            col2.metric("Supplier", invoice.supplier_name or "N/A")
            col3.metric("Total Amount", f"{invoice.total_amount:,.2f}")

            st.subheader("Invoice Items")

            items = [
                item.model_dump()
                for item in invoice.items
            ]

            st.dataframe(
                items,
                use_container_width=True,
                hide_index=True
            )

            st.subheader("Financial Validation")

            if validation["is_valid"]:
                st.success("All critical validation checks passed.")
            else:
                st.warning("Invoice validation failed.")
            # Display missing fields
            if validation["missing_fields"]:
                st.warning("Some invoice information is missing:")
                    
                for field in validation["missing_fields"]:
                    st.write(f"- {field}")
            # Display financial validation errors              
            if validation["errors"]:
                st.subheader("Validation Errors")
                
                for error in validation["errors"]:
                    st.error(error)

            with st.expander("View Complete JSON Output"):
                st.json(result)

            st.download_button(
                label="Download Extracted JSON",
                data=json.dumps(result, indent=4),
                file_name="extracted_invoice.json",
                mime="application/json"
            )
            csv_buffer = io.StringIO()
            if invoice.items:
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
                    csv_writer.writerow(item.model_dump())
                    
                st.download_button(
                    label="Download Invoice Items CSV",
                    data=csv_buffer.getvalue(),
                    file_name="invoice_items.csv",
                     mime="text/csv"
    )

        except Exception as error:
            st.error(f"Invoice processing failed: {error}")