import PyPDF2

try:
    with open(r"c:\Users\Admin\Downloads\Degree life\SEM 6\FYP 2 - Copy\PSM_1_Full_Report\PSM_IDHAM.pdf", "rb") as f:
        reader = PyPDF2.PdfReader(f)
        text = ""
        for i in range(len(reader.pages)):
            text += reader.pages[i].extract_text()
            text += "\n"
        
        with open("extracted_report.txt", "w", encoding="utf-8") as out:
            out.write(text)
        print("Successfully extracted to extracted_report.txt")
except Exception as e:
    print(f"Error: {e}")
