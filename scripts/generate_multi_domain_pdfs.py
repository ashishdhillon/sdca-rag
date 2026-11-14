"""Script to generate realistic, benchmark PDF documents for multi-domain evaluation:
1. SEC Form 10-K Excerpt (Financial domain)
   - Real-world multi-column financial statements (Income Statement, Balance Sheet, Debt Maturities).
2. Enterprise Master Services Agreement (Legal domain)
   - Multi-tiered hierarchical clauses (Articles, Sections, Sub-clauses, Liability Caps, Indemnity).
"""

from pathlib import Path
import pymupdf


def build_financial_10k_pdf(output_path: Path):
    doc = pymupdf.open()
    page_width = 612.0
    page_height = 792.0
    margin_x = 54.0
    margin_top = 54.0
    margin_bottom = 738.0
    content_width = page_width - 2 * margin_x

    page = doc.new_page(width=page_width, height=page_height)
    y = margin_top

    def ensure_space(needed: float):
        nonlocal page, y
        if y + needed > margin_bottom:
            page = doc.new_page(width=page_width, height=page_height)
            y = margin_top

    def draw_heading_1(text: str):
        nonlocal y
        ensure_space(34)
        rect = pymupdf.Rect(margin_x, y, margin_x + content_width, y + 26)
        page.insert_textbox(rect, text, fontsize=14, fontname="helv", fontfile=None)
        y += 30

    def draw_heading_2(text: str):
        nonlocal y
        ensure_space(28)
        rect = pymupdf.Rect(margin_x, y, margin_x + content_width, y + 22)
        page.insert_textbox(rect, text, fontsize=12.5, fontname="helv", fontfile=None)
        y += 26

    def draw_paragraph(text: str):
        nonlocal y
        # Estimate height based on character length
        lines = max(1, len(text) // 90 + 1)
        needed = lines * 14 + 10
        ensure_space(needed)
        rect = pymupdf.Rect(margin_x, y, margin_x + content_width, y + needed)
        page.insert_textbox(rect, text, fontsize=10, fontname="helv")
        y += needed + 4

    def draw_table(title: str, headers: list[str], rows: list[list[str]], col_widths: list[float]):
        nonlocal y
        row_height = 18.0
        header_height = 22.0
        table_height = header_height + len(rows) * row_height + 20.0
        ensure_space(table_height)

        # Draw Table Title
        rect_title = pymupdf.Rect(margin_x, y, margin_x + content_width, y + 18)
        page.insert_textbox(rect_title, title, fontsize=10, fontname="helv")
        y += 20

        # Draw Header Row Background
        header_rect = pymupdf.Rect(margin_x, y, margin_x + sum(col_widths), y + header_height)
        page.draw_rect(header_rect, color=(0.7, 0.7, 0.7), fill=(0.93, 0.93, 0.95))

        cur_x = margin_x
        for h, w in zip(headers, col_widths):
            h_rect = pymupdf.Rect(cur_x + 4, y + 3, cur_x + w - 4, y + header_height - 2)
            align = 2 if cur_x > margin_x + col_widths[0] else 0  # right-align numbers
            page.insert_textbox(h_rect, h, fontsize=9, fontname="helv", align=align)
            cur_x += w
        y += header_height

        # Draw Data Rows
        for r_idx, row in enumerate(rows):
            cur_x = margin_x
            row_rect = pymupdf.Rect(margin_x, y, margin_x + sum(col_widths), y + row_height)
            if r_idx % 2 == 1:
                page.draw_rect(row_rect, color=(0.9, 0.9, 0.9), fill=(0.98, 0.98, 0.98))
            page.draw_line(pymupdf.Point(margin_x, y + row_height), pymupdf.Point(margin_x + sum(col_widths), y + row_height), color=(0.85, 0.85, 0.85))

            for c_idx, (val, w) in enumerate(zip(row, col_widths)):
                val_rect = pymupdf.Rect(cur_x + 4, y + 2, cur_x + w - 4, y + row_height - 1)
                align = 2 if c_idx > 0 else 0
                page.insert_textbox(val_rect, val, fontsize=8.5, fontname="helv", align=align)
                cur_x += w
            y += row_height
        y += 14

    # Document Header
    draw_heading_1("UNITED STATES SECURITIES AND EXCHANGE COMMISSION")
    draw_heading_1("FORM 10-K - ANNUAL REPORT PURSUANT TO SECTION 13 OF THE EXCHANGE ACT")
    draw_paragraph("GLOBALTECH ENTERPRISES INC. (Exact name of registrant as specified in its charter)")
    draw_paragraph("Commission File Number 001-38492 | Fiscal Year Ended December 31, 2025 | State of Incorporation: Delaware")

    # Item 1
    draw_heading_1("ITEM 1. BUSINESS")
    draw_paragraph(
        "GlobalTech Enterprises Inc. is a leading provider of hybrid-cloud enterprise data systems, "
        "autonomous infrastructure optimization, and distributed AI application frameworks. "
        "We serve over 4,800 enterprise customers across North America, EMEA, and Asia-Pacific. "
        "Our core product lines include GlobalMesh Cloud Fabric, Apex Query Lake, and HyperGuard AI Shield."
    )
    draw_paragraph(
        "During fiscal 2025, our recurring software subscription revenues grew 28.4% year-over-year, "
        "driven by enterprise adoption of our multi-region distributed vector indexing engine. "
        "We continue to invest aggressively in research and development to expand our structural indexing capabilities."
    )

    # Item 7
    draw_heading_1("ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION")
    draw_heading_2("Executive Overview and Key Operating Metrics")
    draw_paragraph(
        "For the fiscal year ended December 31, 2025, total revenue was $1,485.6 million, an increase of 21.6% "
        "compared to $1,221.7 million in fiscal 2024 and $984.2 million in fiscal 2023. Operating margin expanded "
        "to 22.4% from 18.2% in fiscal 2024, reflecting higher gross margins from cloud infrastructure efficiencies "
        "and disciplined sales productivity. Operating cash flow reached $412.3 million."
    )
    draw_paragraph(
        "Free cash flow for fiscal 2025 was $348.9 million, compared to $265.4 million for fiscal 2024. "
        "Cash, cash equivalents, and short-term marketable securities totaled $892.4 million at year-end."
    )

    # Item 8
    draw_heading_1("ITEM 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA")
    draw_heading_2("Consolidated Statements of Operations")
    draw_paragraph("(In millions of U.S. Dollars, except per share amounts)")

    ops_headers = ["Financial Line Item", "FY 2025", "FY 2024", "FY 2023"]
    ops_widths = [264.0, 80.0, 80.0, 80.0]
    ops_rows = [
        ["Subscription Revenue", "$1,248.5", "$972.1", "$760.4"],
        ["Professional Services Revenue", "$237.1", "$249.6", "$223.8"],
        ["Total Revenues", "$1,485.6", "$1,221.7", "$984.2"],
        ["Cost of Subscription Revenue", "$249.7", "$204.1", "$167.3"],
        ["Cost of Professional Services", "$213.4", "$229.6", "$210.4"],
        ["Total Cost of Revenues", "$463.1", "$433.7", "$377.7"],
        ["Gross Profit", "$1,022.5", "$788.0", "$606.5"],
        ["Research and Development", "$356.5", "$288.9", "$231.4"],
        ["Sales and Marketing", "$218.4", "$189.3", "$162.5"],
        ["General and Administrative", "$114.8", "$87.4", "$74.2"],
        ["Total Operating Expenses", "$689.7", "$565.6", "$468.1"],
        ["Operating Income", "$332.8", "$222.4", "$138.4"],
        ["Interest and Other Expense, Net", "($14.2)", "($16.8)", "($12.1)"],
        ["Income Before Taxes", "$318.6", "$205.6", "$126.3"],
        ["Provision for Income Taxes", "$57.3", "$37.0", "$22.7"],
        ["Net Income", "$261.3", "$168.6", "$103.6"],
        ["Diluted Net Income Per Share (EPS)", "$1.82", "$1.21", "$0.76"],
    ]
    draw_table("Consolidated Statement of Operations (FY23 - FY25)", ops_headers, ops_rows, ops_widths)

    draw_heading_2("Consolidated Balance Sheets")
    draw_paragraph("(In millions of U.S. Dollars, as of December 31)")
    bs_headers = ["Balance Sheet Category", "As of Dec 31, 2025", "As of Dec 31, 2024"]
    bs_widths = [284.0, 110.0, 110.0]
    bs_rows = [
        ["Cash and Cash Equivalents", "$542.1", "$389.2"],
        ["Short-Term Marketable Securities", "$350.3", "$278.4"],
        ["Accounts Receivable, Net", "$218.6", "$176.5"],
        ["Prepaid Expenses and Other Current Assets", "$64.2", "$51.8"],
        ["Total Current Assets", "$1,175.2", "$895.9"],
        ["Property, Plant and Equipment, Net", "$342.8", "$312.4"],
        ["Operating Lease Right-of-Use Assets", "$118.4", "$124.9"],
        ["Goodwill and Intangibles, Net", "$582.1", "$582.1"],
        ["Total Assets", "$2,218.5", "$1,915.3"],
        ["Accounts Payable and Accrued Expenses", "$198.4", "$164.2"],
        ["Current Portion of Long-Term Debt", "$150.0", "$75.0"],
        ["Deferred Subscription Revenue (Current)", "$384.2", "$312.6"],
        ["Total Current Liabilities", "$732.6", "$551.8"],
        ["Long-Term Debt, Less Current Portion", "$650.0", "$725.0"],
        ["Total Stockholders' Equity", "$835.9", "$638.5"],
        ["Total Liabilities and Stockholders' Equity", "$2,218.5", "$1,915.3"],
    ]
    draw_table("Consolidated Balance Sheets Summary", bs_headers, bs_rows, bs_widths)

    draw_heading_2("Note 7. Debt and Financing Obligations")
    draw_paragraph(
        "Our outstanding debt obligations consist of unsecured Senior Notes and a revolving credit facility. "
        "The following table summarizes future contractual principal repayments and maturities as of December 31, 2025:"
    )
    debt_headers = ["Debt Instrument", "Interest Rate", "Maturity Date", "Carrying Amount"]
    debt_widths = [204.0, 95.0, 105.0, 100.0]
    debt_rows = [
        ["Revolving Credit Facility", "SOFR + 1.25%", "June 30, 2026", "$150.0M"],
        ["2027 Senior Notes", "4.25% Fixed", "October 15, 2027", "$300.0M"],
        ["2029 Senior Secured Notes", "5.875% Fixed", "December 1, 2029", "$350.0M"],
        ["Total Outstanding Long-Term Debt", "--", "--", "$800.0M"],
        ["Less: Unamortized Debt Issuance Costs", "--", "--", "($6.2M)"],
        ["Net Carrying Debt Balance", "--", "--", "$793.8M"],
    ]
    draw_table("Schedule of Contractual Debt Maturities", debt_headers, debt_rows, debt_widths)

    doc.save(str(output_path))
    doc.close()
    print(f"Generated Financial 10-K benchmark PDF at: {output_path}")


def build_commercial_contract_pdf(output_path: Path):
    doc = pymupdf.open()
    page_width = 612.0
    page_height = 792.0
    margin_x = 54.0
    margin_top = 54.0
    margin_bottom = 738.0
    content_width = page_width - 2 * margin_x

    page = doc.new_page(width=page_width, height=page_height)
    y = margin_top

    def ensure_space(needed: float):
        nonlocal page, y
        if y + needed > margin_bottom:
            page = doc.new_page(width=page_width, height=page_height)
            y = margin_top

    def draw_heading_1(text: str):
        nonlocal y
        ensure_space(34)
        rect = pymupdf.Rect(margin_x, y, margin_x + content_width, y + 26)
        page.insert_textbox(rect, text, fontsize=14, fontname="helv")
        y += 30

    def draw_heading_2(text: str):
        nonlocal y
        ensure_space(28)
        rect = pymupdf.Rect(margin_x, y, margin_x + content_width, y + 22)
        page.insert_textbox(rect, text, fontsize=12.5, fontname="helv")
        y += 26

    def draw_paragraph(text: str):
        nonlocal y
        lines = max(1, len(text) // 90 + 1)
        needed = lines * 14 + 8
        ensure_space(needed)
        rect = pymupdf.Rect(margin_x, y, margin_x + content_width, y + needed)
        page.insert_textbox(rect, text, fontsize=9.5, fontname="helv")
        y += needed + 4

    # Document Header
    draw_heading_1("MASTER CLOUD SERVICES AND ENTERPRISE LICENSE AGREEMENT")
    draw_paragraph(
        "This Master Cloud Services and Enterprise License Agreement ('Agreement') is entered into as of January 15, 2025 "
        "('Effective Date'), by and between CloudScale Systems, Inc., a Delaware corporation ('Provider'), and "
        "Horizon Global Logistics LLC, a New York limited liability company ('Customer')."
    )

    # Article 1
    draw_heading_1("Article 1. Definitions and Rules of Interpretation")
    draw_heading_2("Section 1.1 Defined Terms")
    draw_paragraph(
        "'Authorized Users' means employees, consultants, and independent contractors of Customer authorized to access the Cloud Services.\n"
        "'Customer Data' means all electronic data, files, and materials submitted by Customer to the Cloud Service environment.\n"
        "'Service Level Agreement (SLA)' means the guaranteed uptime availability commitment set forth in Schedule B.\n"
        "'Subscription Term' means the initial contractual commitment period of thirty-six (36) calendar months."
    )

    # Article 4
    draw_heading_1("Article 4. Fees, Invoicing and Payment Terms")
    draw_heading_2("Section 4.1 Subscription Fees and Invoicing Schedule")
    draw_paragraph(
        "Customer shall pay the annual recurring subscription fees set forth in Order Form A-1. "
        "Provider shall invoice Customer annually in advance thirty (30) days prior to the commencement of each Contract Year. "
        "All invoices are payable in full within thirty (30) days of the invoice date in immediately available U.S. Dollars."
    )
    draw_heading_2("Section 4.2 Late Payments and Interest")
    draw_paragraph(
        "Any unpaid amounts not subject to a good-faith billing dispute shall accrue interest from the due date until paid "
        "at the rate of one and one-half percent (1.5%) per month, or the maximum rate permitted by applicable law, whichever is less. "
        "Customer shall reimburse Provider for all reasonable attorney fees incurred in collecting delinquent accounts."
    )
    draw_heading_2("Section 4.3 Taxes and Withholdings")
    draw_paragraph(
        "Fees stated herein exclude applicable sales, use, value-added, or withholding taxes. Customer is solely responsible "
        "for payment of all such taxes, excluding taxes based upon Provider's net income or corporate franchise."
    )

    # Article 7
    draw_heading_1("Article 7. Confidentiality and Information Security")
    draw_heading_2("Section 7.1 Confidential Information Obligations")
    draw_paragraph(
        "Each party agrees that all code, inventions, business, technical, and financial information disclosed to it by the other party "
        "constitutes confidential property ('Confidential Information'). The Receiving Party will hold in confidence and not disclose "
        "or use any Confidential Information except as expressly permitted under this Agreement, applying at least reasonable care."
    )
    draw_heading_2("Section 7.2 Data Security and SOC 2 Safeguards")
    draw_paragraph(
        "Provider shall maintain administrative, physical, and technical safeguards compliant with SOC 2 Type II and ISO/IEC 27001 standards "
        "to protect Customer Data against unauthorized destruction, loss, alteration, or unauthorized disclosure."
    )

    # Article 9
    draw_heading_1("Article 9. Limitation of Liability")
    draw_heading_2("Section 9.1 Waiver of Consequential and Indirect Damages")
    draw_paragraph(
        "TO THE MAXIMUM EXTENT PERMITTED BY LAW, IN NO EVENT SHALL EITHER PARTY BE LIABLE TO THE OTHER PARTY FOR ANY "
        "INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, PUNITIVE, OR EXEMPLARY DAMAGES, INCLUDING LOSS OF PROFITS, "
        "LOSS OF BUSINESS REPUTATION, GOODWILL, OR BUSINESS INTERRUPTION, ARISING OUT OF OR IN CONNECTION WITH THIS AGREEMENT."
    )
    draw_heading_2("Section 9.2 Aggregate Direct Damages Liability Cap")
    draw_paragraph(
        "EXCEPT AS EXPRESSLY PROVIDED IN SECTION 9.3, NEITHER PARTY'S TOTAL AGGREGATE LIABILITY ARISING OUT OF OR RELATED TO "
        "THIS AGREEMENT, UNDER ANY LEGAL OR EQUITABLE THEORY (INCLUDING CONTRACT, TORT, STRICT LIABILITY, OR NEGLIGENCE), "
        "SHALL EXCEED THE TOTAL FEES ACTUALLY PAID BY CUSTOMER TO PROVIDER UNDER THIS AGREEMENT IN THE TWELVE (12) MONTHS "
        "IMMEDIATELY PRECEDING THE FIRST EVENT GIVING RISE TO LIABILITY."
    )
    draw_heading_2("Section 9.3 Exclusions from Liability Cap")
    draw_paragraph(
        "The limitations and exclusions set forth in Section 9.1 and Section 9.2 shall NOT apply to: "
        "(a) either party's breach of Article 7 (Confidentiality), excluding non-willful security incidents; "
        "(b) Provider's indemnification obligations under Article 10 for intellectual property infringement; or "
        "(c) either party's gross negligence, willful misconduct, or intentional fraud."
    )

    # Article 12
    draw_heading_1("Article 12. Term, Termination and Governing Law")
    draw_heading_2("Section 12.1 Term and Renewal")
    draw_paragraph(
        "This Agreement commences on the Effective Date and continues for the Subscription Term, automatically renewing "
        "for successive twelve (12) month periods unless either party provides written non-renewal notice at least sixty (60) days prior."
    )
    draw_heading_2("Section 12.2 Termination for Material Breach")
    draw_paragraph(
        "Either party may terminate this Agreement immediately upon written notice if the other party materially breaches any provision "
        "and fails to cure such breach within thirty (30) days of receiving written notice describing the breach in reasonable detail."
    )
    draw_heading_2("Section 12.3 Governing Law and Exclusive Venue")
    draw_paragraph(
        "This Agreement and all disputes arising out of or related hereto shall be governed by and construed in accordance with "
        "the laws of the State of Delaware, without regard to its conflict of laws principles. The parties irrevocably consent "
        "to exclusive jurisdiction and venue in the Court of Chancery of the State of Delaware."
    )

    doc.save(str(output_path))
    doc.close()
    print(f"Generated Commercial Contract benchmark PDF at: {output_path}")


if __name__ == "__main__":
    out_dir = Path("data/multi_domain")
    out_dir.mkdir(parents=True, exist_ok=True)
    build_financial_10k_pdf(out_dir / "financial_10k_sample.pdf")
    build_commercial_contract_pdf(out_dir / "commercial_contract_sample.pdf")
