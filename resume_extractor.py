import os
import pdfplumber
import re
import logging
import spacy
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

try:
    nlp = spacy.load("en_core_web_trf")
    logging.info("Loaded transformer model: en_core_web_trf")
except Exception as e:
    logging.info("Transformer model not available, loading en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

def segment_resume_text(text):
    """
    Splits resume text into sections based on candidate header keywords.
    Improved to ignore trailing text on header lines and to stop collecting when a new header is encountered.
    Candidate headers are expanded based on online resume samples.
    """
    # Expanded candidate headers based on public resume formats:
    candidate_headers = {
        "Education": [
            "Education", "Educational Background", "Academic Qualifications", "Qualifications", 
            "Degree", "Degrees", "Academic", "University", "College", "School", "Courses"
        ],
        "Experience": [
            "Experience", "Work Experience", "Employment", "Professional Experience", 
            "Career", "Internship", "Projects", "Relevant Experience"
        ],
        "Skills": [
            "Skills", "Technical Skills", "Core Competencies", "Expertise", "Programming", "Technologies", "Tools"
        ],
        "Certifications": [
            "Certifications", "Licenses", "Accreditations", "Training", "Certificate", "Cert"
        ],
        "Leadership": [
            "Leadership", "Volunteer", "Community Involvement", "Extracurricular", "Social Work", 
            "Civic Engagement", "Nonprofit", "Team Leadership", "Management"
        ],
        "Projects": [
            "Projects", "Project Experience", "Portfolio", "Case Studies", "Research Projects"
        ]
    }
    segments = {}
    current_section = None
    lines = text.splitlines()
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        header_found = None
        for section, keywords in candidate_headers.items():
            for kw in keywords:
                # Pattern: matches header keyword at beginning; allows optional colon/dash; ignores any trailing text.
                pattern = rf"^(?P<header>{re.escape(kw)})\s*[:\-–—]\s*(?P<rest>.*)$|^(?P<header_only>{re.escape(kw)})\s*$"
                match = re.match(pattern, stripped, re.IGNORECASE)
                if match:
                    header_found = section
                    break
            if header_found:
                break

        if header_found:
            # Start a new section. Ignore any trailing words that might incorrectly be captured.
            current_section = header_found
            segments[current_section] = []  
            continue

        # If we are inside a section, add the line.
        if current_section:
            segments[current_section].append(stripped)
    
    # Join collected lines for each section
    for section in segments:
        segments[section] = "\n".join(segments[section]).strip()
    return segments

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file using pdfplumber."""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        logging.error(f"Error extracting text from {pdf_path}: {e}")
    return text.strip()


def extract_section(text, keywords):
    """
    Fallback: Returns the first occurrence of text following any of the given keywords.
    """
    for keyword in keywords:
        pattern = re.compile(rf"{keyword}[:\s]*(.*)", re.IGNORECASE)
        match = pattern.search(text)
        if match:
            return match.group(1).strip()
    return None


def extract_name(text):
    """
    Extracts a person's name from text by:
      1. Looking for a line beginning with "Name:"
      2. If not found, checking the first non-empty line if it is short
      3. Falling back to regex for capitalized words.
    """
    match = re.search(r"(?im)^name\s*:\s*(.+)$", text)
    if match:
        name = match.group(1).strip()
        return re.sub(r"[^\w\s]", "", name)
    
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if lines:
        first_line = lines[0]
        words = first_line.split()
        if len(words) <= 3 and any(word[0].isupper() for word in words):
            return first_line
    fallback = re.search(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b", text)
    return fallback.group(1) if fallback else None


def extract_email(text):
    match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    return match.group(0) if match else None


def extract_phone(text):
    match = re.search(r"\+?\d[\d\s\-\(\)]{8,}\d", text)
    return match.group(0) if match else None


def extract_linkedin(text):
    match = re.search(r"(https?://)?(www\.)?linkedin\.com/in/[a-zA-Z0-9-_/]+", text)
    return match.group(0) if match else None


def extract_fields_from_text(text, file_name):
    segments = segment_resume_text(text)
    
    # Use segmented blocks if available; otherwise fall back on simple extraction.
    education = segments.get("Education") or extract_section(text, ["Education", "Qualification", "Degree"])
    experience = segments.get("Experience") or extract_section(text, ["Experience", "Work History", "Employment"])
    skills = segments.get("Skills") or extract_section(text, ["Skills", "Technical Skills", "Programming Languages"])
    certifications = segments.get("Certifications") or extract_section(text, ["Certifications", "Licenses", "Accreditations"])
    leadership = segments.get("Leadership") or extract_section(text, ["Leadership", "Volunteer", "Community Involvement"])
    projects = segments.get("Projects") or extract_section(text, ["Projects", "Project Experience", "Portfolio", "Case Studies"])
    
    # Use spaCy's NER as an additional signal for name extraction if needed.
    doc = nlp(text)
    ner_names = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    name_extracted = extract_name(text)
    full_name = name_extracted if name_extracted else (ner_names[0] if ner_names else None)
    
    data = {
        "File Name": file_name,
        "Full Name": full_name,
        "Email": extract_email(text),
        "Phone": extract_phone(text),
        "LinkedIn": extract_linkedin(text),
        "Education": education,
        "Experience": experience,
        "Skills": skills,
        "Certifications": certifications,
        "Leadership": leadership,
        "Projects": projects
    }
    return data


def process_resume(file_path):
    text = extract_text_from_pdf(file_path)
    if not text:
        logging.error("No text extracted from file.")
        return None
    extracted_data = extract_fields_from_text(text, os.path.basename(file_path))
    logging.info(f"Extracted data: {extracted_data}")
    return extracted_data


def save_to_excel(data):
    EXCEL_FILE = "resume_data.xlsx"
    df = pd.DataFrame([data])
    try:
        if os.path.exists(EXCEL_FILE):
            existing_df = pd.read_excel(EXCEL_FILE)
            df = pd.concat([existing_df, df], ignore_index=True)
        df.to_excel(EXCEL_FILE, index=False)
        logging.info(f"Saved extracted data to {EXCEL_FILE}")
    except Exception as e:
        logging.error(f"Error writing to {EXCEL_FILE}: {e}")


if __name__ == "__main__":
    test_file = os.path.join("uploads", "sample_resume.pdf")
    if os.path.exists(test_file):
        data = process_resume(test_file)
        if data:
            save_to_excel(data)
            print("✅ Extraction & Saving Complete!")
    else:
        print("⚠️ Test PDF not found in 'uploads/' folder.")
