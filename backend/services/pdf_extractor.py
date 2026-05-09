"""
AI Summarization Platform — PDF Text Extractor

WHY pdfplumber OVER PyPDF2?
PyPDF2 is older and struggles with multi-column layouts, tables, and 
complex formatting. pdfplumber uses pdfminer under the hood and handles
these cases much better. In production, reliable extraction = reliable summaries.

EDGE CASES WE HANDLE:
1. Password-protected PDFs → clear error message
2. Scanned/image-only PDFs → no text to extract → clear error
3. Corrupted files → graceful error handling
4. Empty pages → skip them
"""

import pdfplumber
from utils.logger import logger


def extract_text_from_pdf(file_path: str) -> dict:
    """
    Extract all text from a PDF file using pdfplumber.
    
    Args:
        file_path: Path to the PDF file on disk
        
    Returns:
        dict with extracted text, page count, and per-page character counts
        
    Raises:
        ValueError: If PDF is password-protected, scanned, or corrupted
    """
    logger.info(f"Extracting text from PDF: {file_path}")
    
    try:
        with pdfplumber.open(file_path) as pdf:
            total_pages = len(pdf.pages)
            
            if total_pages == 0:
                raise ValueError("PDF has no pages.")
            
            logger.info(f"PDF has {total_pages} pages")
            
            all_text = []
            page_chars = []
            
            for i, page in enumerate(pdf.pages):
                try:
                    page_text = page.extract_text()
                    
                    if page_text and page_text.strip():
                        all_text.append(page_text.strip())
                        page_chars.append(len(page_text.strip()))
                    else:
                        page_chars.append(0)
                        logger.debug(f"Page {i + 1}: no text (might be image/scan)")
                        
                except Exception as e:
                    logger.warning(f"Page {i + 1}: extraction failed — {e}")
                    page_chars.append(0)
            
            full_text = "\n\n".join(all_text)
            
            # Check if we actually extracted anything
            if not full_text.strip():
                raise ValueError(
                    "No extractable text found in this PDF. "
                    "This usually means the PDF is scanned/image-only. "
                    "Try using an OCR tool like Tesseract first, then paste "
                    "the text directly."
                )
            
            pages_with_text = sum(1 for c in page_chars if c > 0)
            
            logger.info(
                f"Extracted {len(full_text)} chars from "
                f"{pages_with_text}/{total_pages} pages"
            )
            
            return {
                "text": full_text,
                "total_pages": total_pages,
                "pages_with_text": pages_with_text,
                "total_characters": len(full_text),
            }
            
    except pdfplumber.pdfminer.pdfparser.PDFSyntaxError:
        raise ValueError(
            "This file is not a valid PDF or is corrupted. "
            "Please upload a valid PDF file."
        )
    except Exception as e:
        error_msg = str(e)
        
        # pdfplumber raises this for password-protected PDFs
        if "password" in error_msg.lower() or "encrypted" in error_msg.lower():
            raise ValueError(
                "This PDF is password-protected. "
                "Please remove the password and try again."
            )
        
        # Re-raise our own ValueErrors as-is
        if isinstance(e, ValueError):
            raise
        
        logger.error(f"PDF extraction failed: {error_msg}")
        raise ValueError(f"Failed to process PDF: {error_msg}")
