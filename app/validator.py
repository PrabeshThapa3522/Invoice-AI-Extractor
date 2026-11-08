from decimal import Decimal, ROUND_HALF_UP

from app.schemas import InvoiceData


def to_decimal(value):
    """Convert a numeric value to Decimal."""
    if value is None:
        return None

    return Decimal(str(value))


def money(value):
    """Round a monetary value to two decimal places."""
    return value.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )


def validate_invoice(invoice: InvoiceData) -> dict:
    """
    Validate invoice item calculations, subtotal, and final total.
    """

    errors = []
    # Check for missing important invoice fields
    missing_fields = []
    
    if not invoice.supplier_name:
        missing_fields.append("Supplier Name")
    
    if invoice.total_amount is None:
        missing_fields.append("Total Amount")
        
    if not invoice.invoice_number:
        missing_fields.append("Invoice Number")
        
    if not invoice.invoice_date:
        missing_fields.append("Invoice Date")
        
    if not invoice.items:
        missing_fields.append("Invoice Items")
        
    # Critical fields determine whether the invoice is valid
    if "Supplier Name" in missing_fields:
        errors.append("Supplier name is missing.")
        
    if "Total Amount" in missing_fields:
        errors.append("Total amount is missing.")

    # Check each item's quantity multiplied by unit price
    for index, item in enumerate(invoice.items, start=1):

        expected_item_total = money(
            to_decimal(item.quantity)
            * to_decimal(item.unit_price)
        )

        actual_item_total = money(
            to_decimal(item.total)
        )

        if expected_item_total != actual_item_total:
            errors.append(
                f"Item {index}: quantity * unit price "
                f"does not match line-item total."
            )

    # Calculate sum of line-item totals
    calculated_subtotal = money(
        sum(
            (to_decimal(item.total) for item in invoice.items),
            Decimal("0.00")
        )
    )

    # Check subtotal
    if invoice.subtotal is not None:
        invoice_subtotal = money(
            to_decimal(invoice.subtotal)
        )

        if calculated_subtotal != invoice_subtotal:
            errors.append(
                "Line-item totals do not match invoice subtotal."
            )

    # Check subtotal + VAT = final total
    if (
        invoice.subtotal is not None
        and invoice.vat is not None
        and invoice.total_amount is not None
    ):
        expected_total = money(
            to_decimal(invoice.subtotal)
            + to_decimal(invoice.vat)
        )

        actual_total = money(
            to_decimal(invoice.total_amount)
        )

        if expected_total != actual_total:
            errors.append(
                "Subtotal + VAT does not match final invoice total."
            )

    return {
        "is_valid": len(errors) == 0,
        "items_match_subtotal": (
            invoice.subtotal is not None
            and calculated_subtotal == money(
                to_decimal(invoice.subtotal)
            )
        ),
        "total_matches_subtotal_and_vat": (
            invoice.subtotal is not None
            and invoice.vat is not None
            and invoice.total_amount is not None
            and money(
                to_decimal(invoice.subtotal)
                + to_decimal(invoice.vat)
            ) == money(
                to_decimal(invoice.total_amount)
            )
        ),
        "missing_fields": missing_fields,
        "errors": errors
    }
