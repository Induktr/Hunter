import pandas as pd
import os
from src.shared.core.logger import logger

class ExcelGenerator:
    """
    Converts TSD-powered research results into a professionally formatted Excel matrix.
    """
    
    @staticmethod
    def generate(data: list, filename: str = "research_results.xlsx") -> str:
        if not data:
            logger.warning("No data provided to ExcelGenerator.")
            return ""

        try:
            df = pd.DataFrame(data)
            
            # Rich TSD Columns:
            # ['Name', 'Location', 'Root Concept & Tech', 'Pain Type & Friction', 'Price/Value', 'SPOF & Risk Diagnosis', 'Outreach Pitch Hook', 'Link']
            expected_cols = [
                "Name",
                "Location",
                "Root Concept & Tech",
                "Pain Type & Friction",
                "Price/Value",
                "SPOF & Risk Diagnosis",
                "Outreach Pitch Hook",
                "Link"
            ]
            
            for col in expected_cols:
                if col not in df.columns:
                    df[col] = "N/A"
            
            df = df[expected_cols] # Reorder to exact TSD structure
            
            # Create a Pandas Excel writer using XlsxWriter as the engine.
            filepath = os.path.join("docs", filename)
            os.makedirs("docs", exist_ok=True)
            
            writer = pd.ExcelWriter(filepath, engine='xlsxwriter')
            df.to_excel(writer, index=False, sheet_name='TSD_Lead_Matrix')

            workbook = writer.book
            worksheet = writer.sheets['TSD_Lead_Matrix']

            # Freeze the top row (header) so it stays visible while scrolling
            worksheet.freeze_panes(1, 0)

            # --- Formatting ---
            
            # Header Row Style: Navy Blue (#1B2A41) with White Bold text
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#1B2A41',
                'font_color': '#FFFFFF',
                'border': 1
            })

            # Alternating Row Colors
            even_row_format = workbook.add_format({'bg_color': '#F8F9FA', 'border': 1, 'text_wrap': True, 'valign': 'top'})
            odd_row_format = workbook.add_format({'bg_color': '#FFFFFF', 'border': 1, 'text_wrap': True, 'valign': 'top'})
            
            # Write headers with formatting
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)

            # Apply row formatting and links
            for row_num in range(1, len(df) + 1):
                fmt = even_row_format if row_num % 2 == 0 else odd_row_format
                for col_num in range(len(df.columns)):
                    val = df.iloc[row_num - 1, col_num]
                    col_name = df.columns[col_num]
                    
                    # Clickable Hyperlinks in "Link" column
                    if col_name == "Link" and str(val).startswith("http"):
                         worksheet.write_url(row_num, col_num, val, string="Source Website", cell_format=fmt)
                    else:
                         worksheet.write(row_num, col_num, val, fmt)

            # Auto-adjust columns width for readability
            for i, col in enumerate(df.columns):
                column_len = max(df[col].astype(str).str.len().max(), len(col)) + 2
                worksheet.set_column(i, i, min(max(column_len, 15), 45))

            writer.close()
            logger.info(f"📊 TSD Lead Matrix Excel generated successfully: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Excel generation error: {e}")
            return ""

excel_manager = ExcelGenerator()
