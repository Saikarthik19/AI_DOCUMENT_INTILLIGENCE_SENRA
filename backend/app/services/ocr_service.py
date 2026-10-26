import io
import shutil
from typing import Optional
from PIL import Image
from backend.app.core.config import settings
from backend.app.core.logging import logger

try:
    import pytesseract
    PYTESSERACT_INSTALLED = True
except ImportError:
    PYTESSERACT_INSTALLED = False

class OCRService:
    def __init__(self):
        self._enabled = settings.OCR_ENABLED
        self._tesseract_available = False
        self._init_tesseract()

    def _init_tesseract(self):
        if not self._enabled:
            logger.info("OCR is disabled in configuration.")
            return

        if not PYTESSERACT_INSTALLED:
            logger.warning("pytesseract Python package is not installed. OCR will be unavailable.")
            return

        if settings.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

        # Verify executable existence
        try:
            cmd = pytesseract.pytesseract.tesseract_cmd
            # Check if command is on PATH or valid file
            if shutil.which(cmd) or (cmd and shutil.which(str(cmd))):
                self._tesseract_available = True
                logger.info("Tesseract OCR binary detected and ready.")
            else:
                # Test with get_tesseract_version
                pytesseract.get_tesseract_version()
                self._tesseract_available = True
                logger.info("Tesseract OCR binary verified via version check.")
        except Exception:
            self._tesseract_available = False
            logger.warning("Tesseract OCR executable not found on system PATH. Scanned images will report OCR unavailable.")

    def is_available(self) -> bool:
        return self._enabled and PYTESSERACT_INSTALLED and self._tesseract_available

    def extract_text_from_image_bytes(self, image_bytes: bytes) -> str:
        if not self.is_available():
            raise RuntimeError(
                "OCR is not available. Please install Tesseract OCR binary and ensure it is in system PATH, "
                "or set TESSERACT_CMD in .env"
            )
        try:
            image = Image.open(io.BytesIO(image_bytes))
            # Convert to RGB if palette or alpha
            if image.mode not in ("L", "RGB"):
                image = image.convert("RGB")
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            logger.error("OCR extraction failed: %s", str(e))
            raise RuntimeError(f"OCR processing failed: {str(e)}")

    def extract_text_from_pil(self, image: Image.Image) -> str:
        if not self.is_available():
            return ""
        try:
            if image.mode not in ("L", "RGB"):
                image = image.convert("RGB")
            return pytesseract.image_to_string(image).strip()
        except Exception as e:
            logger.error("OCR PIL extraction error: %s", str(e))
            return ""

ocr_service = OCRService()
