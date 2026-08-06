# Document parsing service placeholder (pdf / docx / txt / eml)
def parse_document(file_content: bytes, filename: str) -> str:
    return file_content.decode("utf-8", errors="ignore")
