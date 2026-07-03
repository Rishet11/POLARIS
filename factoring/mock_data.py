"""
POLARIS Factoring Mock Data
Deliberately messy bank feed: short-pays, combined remittances, partial
payments, reused PO references, and unreferenced wires — so the cash
application engine has real exceptions to route, not just clean matches.

Dates are generated relative to today so aging buckets stay correct.
"""

from typing import Dict, List, Tuple

from .models import BankPayment, Debtor, Invoice, days_ago, days_ahead


def get_debtors() -> Dict[str, Debtor]:
    debtors = [
        Debtor("D001", "Meridian Freight Lines", "ap@meridianfreight.com", 30, 0),
        Debtor("D002", "Atlas Building Supply", "payables@atlasbuild.com", 45, 1),
        Debtor("D003", "Lakeshore Staffing Group", "finance@lakeshorestaffing.com", 30, 0),
        Debtor("D004", "Ironwood Manufacturing", "ap@ironwoodmfg.com", 60, 2),
        Debtor("D005", "Bluepeak Logistics", "accounts@bluepeaklogistics.com", 30, 0),
    ]
    return {d.debtor_id: d for d in debtors}


def get_invoices() -> List[Invoice]:
    return [
        # Clean matches
        Invoice("INV-1001", "D001", 12450.00, days_ago(35), days_ago(5), "INV-1001"),
        Invoice("INV-1002", "D001", 10000.00, days_ago(42), days_ago(12), "INV-1002"),
        Invoice("INV-1003", "D003", 8730.50, days_ago(20), days_ahead(10), "INV-1003"),
        Invoice("INV-1004", "D005", 5275.25, days_ago(26), days_ahead(4), "INV-1004"),
        # Atlas AP run pays these three in one wire
        Invoice("INV-1005", "D002", 7200.00, days_ago(85), days_ago(40), "INV-1005"),
        Invoice("INV-1006", "D002", 9405.75, days_ago(80), days_ago(35), "INV-1006"),
        Invoice("INV-1009", "D002", 6500.00, days_ago(92), days_ago(47), "INV-1009"),
        Invoice("INV-1007", "D004", 21600.00, days_ago(68), days_ago(8), "INV-1007"),
        Invoice("INV-1008", "D003", 17940.00, days_ago(15), days_ahead(15), "INV-1008"),
        Invoice("INV-1010", "D005", 8800.00, days_ago(50), days_ago(20), "INV-1010"),
        # Client reused PO-7788 on two invoices — reference is ambiguous
        Invoice("INV-1011", "D004", 15300.00, days_ago(155), days_ago(95), "PO-7788"),
        Invoice("INV-1012", "D004", 11750.00, days_ago(125), days_ago(65), "PO-7788"),
        # Same face amount from two different debtors — amount alone can't decide
        Invoice("INV-1013", "D001", 4150.00, days_ago(33), days_ago(3), "INV-1013"),
        Invoice("INV-1014", "D003", 4150.00, days_ago(10), days_ahead(20), "INV-1014"),
    ]


def get_bank_feed() -> List[BankPayment]:
    return [
        BankPayment("P001", days_ago(2), 12450.00, "MERIDIAN FREIGHT LINES",
                    "INV-1001 MERIDIAN FREIGHT"),
        BankPayment("P002", days_ago(2), 8730.50, "LAKESHORE STAFFING",
                    "PAYMENT INV-1003"),
        BankPayment("P003", days_ago(1), 21600.00, "IRONWOOD MFG",
                    "INV-1007"),
        # Garbled ACH memo, but the amount is unique across open invoices
        BankPayment("P004", days_ago(1), 5275.25, "BLUEPEAK LOGISTICS LLC",
                    "ACH PMT 88-3321"),
        # No reference at all; amount uniquely identifies the invoice
        BankPayment("P005", days_ago(1), 17940.00, "LAKESHORE STAFFING", ""),
        # Short-pay: debtor deducted a wire fee
        BankPayment("P006", days_ago(1), 9850.00, "MERIDIAN FREIGHT LINES",
                    "INV-1002 LESS WIRE FEE"),
        # One wire covering three invoices from the same debtor
        BankPayment("P007", days_ago(0), 23105.75, "ATLAS BUILDING SUPPLY",
                    "AP RUN JUNE"),
        # Partial payment (50%) with a clear reference
        BankPayment("P008", days_ago(0), 4400.00, "BLUEPEAK LOGISTICS LLC",
                    "INV-1010 PARTIAL"),
        # Reused PO reference matches two invoices; amount matches neither
        BankPayment("P009", days_ago(0), 13000.00, "IRONWOOD MFG", "PO-7788"),
        # Unreferenced wire; two open invoices share this exact amount
        BankPayment("P010", days_ago(0), 4150.00, "INCOMING WIRE HSBC NY", ""),
    ]


def get_back_office_dataset() -> Tuple[Dict[str, Debtor], List[Invoice], List[BankPayment]]:
    """Full demo dataset: debtors, invoices, and the incoming bank feed."""
    return get_debtors(), get_invoices(), get_bank_feed()
