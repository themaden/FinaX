"""
FinanX — RAG PDF Okuma ve Chunking Modülü
pdfplumber ve PyMuPDF ile PDF işleme, LangChain chunking.
"""

import os
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from loguru import logger

from backend.config import settings


class DocumentChunk:
    """Bir belge parçasını temsil eden veri sınıfı."""

    def __init__(
        self,
        text: str,
        metadata: Dict[str, Any],
        chunk_id: Optional[str] = None
    ):
        self.text = text
        self.metadata = metadata
        self.chunk_id = chunk_id or hashlib.md5(text.encode()).hexdigest()[:12]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "metadata": self.metadata,
        }


class PDFIngestionPipeline:
    """
    PDF faaliyet raporlarını ve KAP bildirimlerini okuyup
    FAISS'e yüklenmeye hazır chunk'lara dönüştürür.
    """

    def __init__(self):
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ".", " ", ""],
            length_function=len,
        )
        self.reports_path = Path(settings.PDF_REPORTS_PATH)
        self.reports_path.mkdir(parents=True, exist_ok=True)

    def compute_file_hash(self, filepath: str) -> str:
        """Dosya hash'i hesapla (tekrar yüklemeyi engeller)."""
        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def extract_text_with_pdfplumber(self, filepath: str) -> str:
        """
        pdfplumber ile metin ve tablo içeriğini koruyarak çıkar.
        Tablolar markdown formatına dönüştürülür.
        """
        try:
            import pdfplumber
        except ImportError:
            logger.warning("pdfplumber kurulu değil, PyMuPDF deneniyor")
            return self._extract_with_pymupdf(filepath)

        full_text_parts = []

        try:
            with pdfplumber.open(filepath) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    page_text = ""

                    # Sayfadaki tabloları çıkar
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            if table:
                                table_md = self._table_to_markdown(table)
                                page_text += f"\n[TABLO - Sayfa {page_num}]\n{table_md}\n"

                    # Tablolar dışındaki metni çıkar (layout parametresi versiyona bağlı)
                    try:
                        raw_text = page.extract_text(
                            x_tolerance=3,
                            y_tolerance=3,
                            layout=True,
                        )
                    except TypeError:
                        # Eski pdfplumber versiyonları layout parametresi desteklemez
                        raw_text = page.extract_text(
                            x_tolerance=3,
                            y_tolerance=3,
                        )

                    if raw_text:
                        page_text += f"\n{raw_text}"

                    if page_text.strip():
                        full_text_parts.append(f"--- Sayfa {page_num} ---\n{page_text}")

        except Exception as e:
            logger.warning(f"pdfplumber hatası {filepath}: {e}. PyMuPDF deneniyor...")
            return self._extract_with_pymupdf(filepath)

        return "\n\n".join(full_text_parts)

    def _extract_with_pymupdf(self, filepath: str) -> str:
        """Yedek: PyMuPDF ile metin çıkar."""
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(filepath)
            text_parts = []
            for page_num, page in enumerate(doc, start=1):
                text = page.get_text("text")
                if text.strip():
                    text_parts.append(f"--- Sayfa {page_num} ---\n{text}")
            doc.close()
            return "\n\n".join(text_parts)
        except ImportError:
            logger.warning("PyMuPDF (fitz) kurulu değil")
            return ""
        except Exception as e:
            logger.error(f"PyMuPDF hatası {filepath}: {e}")
            return ""

    def _table_to_markdown(self, table: List[List]) -> str:
        """Tablo listesini Markdown formatına dönüştür."""
        if not table or not table[0]:
            return ""

        rows = []
        header = table[0]
        rows.append("| " + " | ".join(str(c or "") for c in header) + " |")
        rows.append("|" + "|".join(["---"] * len(header)) + "|")

        for row in table[1:]:
            if row:
                rows.append("| " + " | ".join(str(c or "") for c in row) + " |")

        return "\n".join(rows)

    def chunk_document(
        self,
        text: str,
        metadata: Dict[str, Any]
    ) -> List[DocumentChunk]:
        """
        Metni anlamsal bütünlüğü koruyarak parçalara böl.
        Her chunk'a kaynak metadata ekle.
        """
        raw_chunks = self.text_splitter.split_text(text)
        chunks = []

        for i, chunk_text in enumerate(raw_chunks):
            chunk_metadata = {
                **metadata,
                "chunk_index": i,
                "total_chunks": len(raw_chunks),
                "char_count": len(chunk_text),
            }
            chunk = DocumentChunk(text=chunk_text, metadata=chunk_metadata)
            chunks.append(chunk)

        logger.info(
            f"Belge {len(raw_chunks)} chunk'a bölündü: "
            f"{metadata.get('filename', 'bilinmiyor')}"
        )
        return chunks

    def ingest_pdf(
        self,
        filepath: str,
        ticker: Optional[str] = None,
        doc_type: str = "faaliyet_raporu",
        year: Optional[int] = None,
        quarter: Optional[int] = None,
    ) -> List[DocumentChunk]:
        """
        Tek bir PDF dosyasını işleyip chunk listesi döndür.
        """
        filepath = str(filepath)
        filename = os.path.basename(filepath)
        file_hash = self.compute_file_hash(filepath)

        logger.info(f"PDF işleniyor: {filename} (ticker={ticker}, yıl={year})")

        full_text = self.extract_text_with_pdfplumber(filepath)

        if not full_text.strip():
            logger.warning(f"PDF'den metin çıkarılamadı: {filename}")
            return []

        metadata = {
            "source": "pdf",
            "filename": filename,
            "filepath": filepath,
            "file_hash": file_hash,
            "ticker": ticker or "bilinmiyor",
            "doc_type": doc_type,
            "year": year,
            "quarter": quarter,
            "ingested_at": datetime.utcnow().isoformat(),
        }

        chunks = self.chunk_document(full_text, metadata)

        logger.success(
            f"✅ {filename}: {len(chunks)} chunk oluşturuldu "
            f"({len(full_text):,} karakter)"
        )
        return chunks

    def ingest_text(
        self,
        text: str,
        metadata: Dict[str, Any],
    ) -> List[DocumentChunk]:
        """
        Metin içeriğini doğrudan chunk'lara dönüştür.
        KAP bildirimlerini metin olarak eklemek için kullanılır.
        """
        if not text.strip():
            return []
        return self.chunk_document(text, metadata)

    def ingest_directory(
        self,
        directory: Optional[str] = None,
    ) -> List[DocumentChunk]:
        """
        Bir dizindeki tüm PDF dosyalarını toplu işle.
        """
        dir_path = Path(directory or self.reports_path)
        pdf_files = list(dir_path.glob("**/*.pdf"))

        if not pdf_files:
            logger.warning(f"PDF bulunamadı: {dir_path}")
            return []

        all_chunks: List[DocumentChunk] = []
        for pdf_path in pdf_files:
            parts = pdf_path.stem.split("_")
            ticker = parts[0].upper() if parts else None
            year = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None

            chunks = self.ingest_pdf(
                filepath=str(pdf_path),
                ticker=ticker,
                year=year,
            )
            all_chunks.extend(chunks)

        logger.success(
            f"Toplam {len(all_chunks)} chunk oluşturuldu "
            f"({len(pdf_files)} PDF)"
        )
        return all_chunks


# Singleton instance
ingestion_pipeline = PDFIngestionPipeline()
