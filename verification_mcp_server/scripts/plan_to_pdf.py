import yaml
import json
import os
import requests
import base64
import warnings
from fpdf import FPDF, XPos, YPos

# Suppress fpdf/deprecation warnings that break MCP stdio
warnings.filterwarnings("ignore")

class VerificationPlanPDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 15)
        self.cell(0, 10, 'Verification Plan Report', align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

    def draw_section_header(self, number, title, fill_color=(200, 220, 255)):
        self.set_font("helvetica", 'B', 14)
        self.set_fill_color(*fill_color)
        self.cell(0, 10, f"{number}. {title}", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)

    def draw_table_row(self, col_widths, col_data, line_height=8):
        safe_data = [safe_str(t) for t in col_data]
        max_lines = 1
        for i, text in enumerate(safe_data):
            lines = len(self.multi_cell(col_widths[i], 5, text, split_only=True))
            if lines > max_lines: max_lines = lines
        
        row_height = max_lines * line_height
        if self.get_y() + row_height > self.page_break_trigger:
            self.add_page()

        x_start = self.get_x()
        y_start = self.get_y()
        
        for i, text in enumerate(safe_data):
            curr_x = self.get_x()
            curr_y = self.get_y()
            self.rect(curr_x, curr_y, col_widths[i], row_height)
            self.multi_cell(col_widths[i], line_height, text, border=0)
            self.set_xy(curr_x + col_widths[i], curr_y)
        
        self.set_xy(x_start, y_start + row_height)

    def draw_code_block(self, code_text):
        """Renders a shaded, monospaced code block for SystemVerilog."""
        self.ln(2)
        self.set_font("courier", size=8)
        self.set_fill_color(240, 244, 248) # Very light slate/blue-ish grey
        self.set_draw_color(180, 180, 180) # Grey border
        
        safe_code = safe_str(code_text)
        
        # multi_cell handles splitting and page breaks
        self.multi_cell(0, 5, txt=safe_code, border=1, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        # Reset colors
        self.set_draw_color(0, 0, 0)
        self.ln(4)

def render_mermaid(mermaid_code, output_path):
    try:
        encoded = base64.b64encode(mermaid_code.encode('utf-8')).decode('utf-8')
        url = f"https://mermaid.ink/img/{encoded}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return True
    except Exception: pass
    return False

def safe_str(text):
    """Replace or strip characters not supported by fpdf helvetica (latin-1 range)."""
    if not isinstance(text, str):
        text = str(text)
    return text.encode('latin-1', errors='replace').decode('latin-1')

def generate_pdf(input_path, output_pdf_path):
    if not os.path.exists(input_path): return False
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            if input_path.endswith('.yaml') or input_path.endswith('.yml'):
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
    except Exception: return False

    pdf = VerificationPlanPDF()
    pdf.add_page()
    
    pdf.set_font("helvetica", 'B', 14)
    pdf.cell(0, 10, safe_str(f"Project: {data.get('project', 'N/A')}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("helvetica", size=12)
    pdf.cell(0, 10, safe_str(f"Version: {data.get('version', '1.0')}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    role = data.get('verification_role') or data.get('dut_role') or 'N/A'
    pdf.cell(0, 10, safe_str(f"Verification Role: {role}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)

    section_idx = 1

    # 1. Architecture
    if 'uvm_environment_diagram' in data:
        pdf.draw_section_header(section_idx, "UVM Environment Architecture")
        section_idx += 1
        temp_img = "temp_mermaid.png"
        mermaid_code = data['uvm_environment_diagram'].strip()
        if render_mermaid(mermaid_code, temp_img):
            pdf.image(temp_img, x=15, w=180)
            pdf.ln(5)
            if os.path.exists(temp_img): os.remove(temp_img)
        else:
            pdf.set_font("courier", size=10)
            pdf.multi_cell(0, 5, txt=safe_str(data['uvm_environment_diagram']), border=1)
        pdf.ln(5)



    # 3. Test Requirements
    if 'test_requirements' in data:
        pdf.draw_section_header(section_idx, "Test Requirements")
        section_idx += 1
        pdf.set_font("helvetica", 'B', 9)
        widths = [20, 35, 45, 90]
        pdf.draw_table_row(widths, ["Index", "Feature/Sub", "Name", "Description"], line_height=8)
        pdf.set_font("helvetica", size=8)
        for req in data['test_requirements']:
            feat = req.get('feature', 'N/A')
            subf = req.get('sub_feature', '')
            feat_str = f"{feat}\n({subf})" if subf else feat
            pdf.draw_table_row(widths, [req.get('id', 'N/A'), feat_str, req.get('name', 'N/A'), req.get('description', 'N/A')], line_height=6)
        pdf.ln(5)

    # 4. Test Cases
    if 'test_cases' in data:
        pdf.draw_section_header(section_idx, "Test Cases & Mapping")
        section_idx += 1
        pdf.set_font("helvetica", 'B', 10)
        widths = [30, 110, 50]
        pdf.draw_table_row(widths, ["Index", "Scenario", "TR Mapping"], line_height=10)
        pdf.set_font("helvetica", size=9)
        for tc in data['test_cases']:
            mapping = ", ".join(tc.get('mapping', []))
            pdf.draw_table_row(widths, [tc.get('id', 'N/A'), tc.get('scenario', 'N/A'), mapping], line_height=7)
        pdf.ln(5)

    # 5. Coverage Groups
    if 'coverage_groups' in data:
        pdf.draw_section_header(section_idx, "Functional Coverage Groups")
        section_idx += 1
        pdf.set_font("helvetica", 'B', 10)
        widths = [50, 140]
        pdf.draw_table_row(widths, ["Group Name", "Description"], line_height=10)
        pdf.set_font("helvetica", size=9)
        for cg in data['coverage_groups']:
            pdf.draw_table_row(widths, [cg.get('name', 'N/A'), cg.get('description', 'N/A')], line_height=7)
        pdf.ln(5)

    # 6. Interface Signals
    if 'interface_signals' in data:
        pdf.draw_section_header(section_idx, "Interface Signals")
        section_idx += 1
        pdf.set_font("helvetica", 'B', 10)
        widths = [40, 25, 25, 100]
        pdf.draw_table_row(widths, ["Signal Name", "Direction", "Width", "Description"], line_height=10)
        pdf.set_font("helvetica", size=9)
        for sig in data['interface_signals']:
            pdf.draw_table_row(widths, [sig.get('name', 'N/A'), sig.get('direction', 'N/A'), sig.get('width', 'N/A'), sig.get('description', 'N/A')], line_height=7)
        pdf.ln(5)

    # 7. Directory Structure
    if 'directory_structure' in data:
        pdf.draw_section_header(section_idx, "Verification Environment Structure")
        section_idx += 1
        ds = data['directory_structure']
        pdf.set_font("courier", 'B', 10)
        pdf.cell(0, 6, safe_str(f"{ds.get('root', '/')}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("courier", size=9)
        folders = ds.get('folders', [])
        for f_idx, fld in enumerate(folders):
            is_last_folder = (f_idx == len(folders) - 1)
            if isinstance(fld, dict):
                for k, v in fld.items():
                    # Folder branching
                    folder_prefix = "|-- " if is_last_folder else "|-- "
                    pdf.cell(0, 6, safe_str(f"{folder_prefix}{k}/"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                    
                    # File branching
                    files = [x.strip() for x in v.split(',') if x.strip()]
                    for i, fname in enumerate(files):
                        is_last_file = (i == len(files) - 1)
                        spacing = "    " if is_last_folder else "|   "
                        file_pointer = "|-- " if is_last_file else "|-- "
                        pdf.cell(0, 5, safe_str(f"{spacing}{file_pointer}{fname}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(5)

    # 8. Code Snippets (e.g., SystemVerilog Boilerplate)
    if 'code_snippets' in data:
        pdf.draw_section_header(section_idx, "SystemVerilog Implementation")
        section_idx += 1
        for snippet in data['code_snippets']:
            title = snippet.get('title', 'Code Snippet')
            code = snippet.get('code', '')
            pdf.set_font("helvetica", 'B', 10)
            pdf.cell(0, 6, safe_str(title), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.draw_code_block(code)

    pdf.output(output_pdf_path)
    return output_pdf_path

if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3:
        generate_pdf(sys.argv[1], sys.argv[2])
