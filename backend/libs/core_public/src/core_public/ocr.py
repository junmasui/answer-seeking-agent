import enum


class OcrStrategy(str, enum.Enum):
    """Supported OCR strategies for document processing."""

    FAST = 'fast'
    HI_RES = 'hi_res'
    OCR_ONLY = 'ocr_only'


class DocumentOcrStrategy(str, enum.Enum):
    """OCR strategy selection for individual documents."""

    USE_DOCUMENT_SET = 'use_document_set'
    FAST = 'fast'
    HI_RES = 'hi_res'
    OCR_ONLY = 'ocr_only'
