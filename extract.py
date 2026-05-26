import fitz  # PyMuPDF

def extract_text_from_pdf(pdf_path):
    """
    Opens a PDF file and extracts all text from every page.
    Returns one big string with all the text combined.
    """
    doc = fitz.open(pdf_path)  # open the PDF
    full_text = ""

    for page in doc:                        # loop through each page
        full_text += page.get_text()        # grab text from that page

    doc.close()
    return full_text


# --- TEST IT ---
if __name__ == "__main__":
    # Put your own resume PDF in the same folder and update the name below
    text = extract_text_from_pdf("sample_resume.pdf")
    print(text[:1000])  # print first 1000 characters to check