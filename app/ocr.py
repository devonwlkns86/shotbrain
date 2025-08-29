import easyocr

_reader = None

def get_reader():
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(["en"], gpu=False)
    return _reader

def extract_text(image_path: str, lang: str = "eng") -> str:
    reader = get_reader()
    results = reader.readtext(image_path, detail=0)  # list of strings
    return "\n".join(results).strip()
