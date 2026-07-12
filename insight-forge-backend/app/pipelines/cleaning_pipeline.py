"""
Insight Forge V2 — Data Cleaning Pipeline.

Orchestrates data engineering cleaning rules and trusted dataset generation.
"""

import csv
import io
import zipfile
import xml.etree.ElementTree as ET
from typing import Any

from app.ai.schemas.cleaning import CleaningLogEntry, TrustedDatasetSummary
from app.ai.utils.cleaning import generate_trusted_dataset
from app.services.exceptions import ValidationError


class CleaningPipeline:
    """Staged data cleaning execution pipeline."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    async def execute(
        self, file_content: bytes, filename: str
    ) -> tuple[TrustedDatasetSummary, list[CleaningLogEntry]]:
        """Run the registered cleaning pipeline stages."""
        fn_lower = filename.lower()
        
        # 1. Supported file validation
        if not (fn_lower.endswith(".csv") or fn_lower.endswith(".xlsx")):
            raise ValidationError(
                "Unsupported file format. Only CSV and XLSX are allowed.",
                error_code="unsupported_format",
            )

        # 2. Parse file content
        df_dict: list[dict[str, Any]] = []
        if fn_lower.endswith(".csv"):
            df_dict = self._parse_csv(file_content)
        else:
            df_dict = self._parse_xlsx(file_content)

        # 3. Handle empty dataset safety
        if not df_dict:
            # Under the hood, generate_trusted_dataset will handle empty lists and flag as Not Certified.
            # We pass a default dummy column list when empty so it doesn't crash on headers retrieval.
            columns: list[str] = ["dataset_empty"]
        else:
            columns = list(df_dict[0].keys())

        # 4. Generate trusted dataset and audit logging
        dataset_name = filename.rsplit(".", 1)[0]
        summary, log_entries = generate_trusted_dataset(df_dict, columns, dataset_name)
        return summary, log_entries

    def _parse_csv(self, content: bytes) -> list[dict[str, Any]]:
        """Parse CSV byte content into list of dictionaries."""
        try:
            decoded = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            decoded = content.decode("latin-1")
            
        f = io.StringIO(decoded)
        reader = csv.DictReader(f)
        rows = []
        for r in reader:
            rows.append(dict(r))
        return rows

    def _parse_xlsx(self, content: bytes) -> list[dict[str, Any]]:
        """Parse XLSX byte content into list of dictionaries using zero-dependency zipfile/XML parsing."""
        if not zipfile.is_zipfile(io.BytesIO(content)):
            raise ValidationError(
                "Invalid XLSX file structure.",
                error_code="invalid_xlsx",
            )
            
        rows: list[dict[str, Any]] = []
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as z:
                # A. Read shared strings if present
                shared_strings: list[str] = []
                try:
                    ss_data = z.read("xl/sharedStrings.xml")
                    ss_root = ET.fromstring(ss_data)
                    ns_ss = {"ns": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
                    for t_elem in ss_root.findall(".//ns:t", ns_ss):
                        shared_strings.append(t_elem.text or "")
                except KeyError:
                    pass  # No sharedStrings in this file

                # B. Read sheet1
                try:
                    sheet_data = z.read("xl/worksheets/sheet1.xml")
                except KeyError:
                    raise ValidationError(
                        "Sheet1 not found in the XLSX workbook.",
                        error_code="sheet_not_found",
                    )
                    
                sheet_root = ET.fromstring(sheet_data)
                ns_sheet = {"ns": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
                
                # C. Extract sheet grid values
                sheet_rows: dict[int, dict[str, Any]] = {}
                for r_elem in sheet_root.findall(".//ns:row", ns_sheet):
                    r_idx_str = r_elem.attrib.get("r")
                    if not r_idx_str:
                        continue
                    r_idx = int(r_idx_str)
                    
                    row_data: dict[str, Any] = {}
                    for c_elem in r_elem.findall("ns:c", ns_sheet):
                        r_ref = c_elem.attrib.get("r")
                        if not r_ref:
                            continue
                        col_letter = "".join([c for c in r_ref if c.isalpha()])
                        
                        t_type = c_elem.attrib.get("t")
                        v_elem = c_elem.find("ns:v", ns_sheet)
                        val: Any = None
                        
                        if v_elem is not None:
                            raw_val = v_elem.text or ""
                            if t_type == "s":  # Shared string reference
                                try:
                                    idx = int(raw_val)
                                    if 0 <= idx < len(shared_strings):
                                        val = shared_strings[idx]
                                except ValueError:
                                    val = raw_val
                            elif t_type == "b":  # Boolean
                                val = raw_val == "1"
                            else:
                                # Try parsing numeric or keep raw text
                                try:
                                    if "." in raw_val:
                                        val = float(raw_val)
                                    else:
                                        val = int(raw_val)
                                except ValueError:
                                    val = raw_val
                        row_data[col_letter] = val
                    sheet_rows[r_idx] = row_data

                if not sheet_rows:
                    return []

                # D. Convert grid representation using Row 1 as headers
                sorted_keys = sorted(sheet_rows.keys())
                first_row_idx = sorted_keys[0]
                header_row = sheet_rows[first_row_idx]
                
                # Build header mapping
                header_map: dict[str, str] = {}
                for col_let, val in header_row.items():
                    if val is not None and str(val).strip() != "":
                        header_map[col_let] = str(val).strip()
                    else:
                        header_map[col_let] = col_let

                # Convert subsequent data rows
                for r_idx in sorted_keys[1:]:
                    row_dict: dict[str, Any] = {}
                    current_row = sheet_rows[r_idx]
                    # Fill keys based on header row columns
                    for col_let, col_name in header_map.items():
                        cell_val = current_row.get(col_let)
                        # Normalize None / empty values
                        row_dict[col_name] = cell_val if cell_val is not None else ""
                    rows.append(row_dict)

        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(
                f"Failed to parse XLSX workbook: {str(e)}",
                error_code="invalid_xlsx_structure",
            )

        return rows
