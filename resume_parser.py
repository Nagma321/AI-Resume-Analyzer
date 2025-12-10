import PyPDF2
import re

def clean_text(text: str) -> str:
    # Replace bullet symbols with dashes
    text = re.sub(r"[•●▪►]", "-", text)

    # Remove excessive line breaks and spaces
    text = re.sub(r"\n{2,}", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)

    # Remove weird broken hyphen splits like "Devel-\noper"
    text = re.sub(r"-\s*\n\s*", "-", text)

    # Normalize spacing again
    text = re.sub(r"\n\s+", "\n", text)

    return text.strip()

def extract_text(file_path):
    text = ""

    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)

            pages = []
            for page in reader.pages:
                page_text = page.extract_text() or ""
                pages.append(page_text)

            text = "\n".join(pages)
    except Exception as e:
        text = "Error reading file: " + str(e)

    return clean_text(text)
