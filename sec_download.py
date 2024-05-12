import os
import re
import subprocess
import platform
import pdfkit
from sec_edgar_downloader import Downloader
from bs4 import BeautifulSoup



# Table contents
item_table = {
    'Business': 'Item 1.',
    'Risk Factors': 'Item 1A.',
    'Unresolved Staff Comments': 'Item 1B.',
    'C': 'Item 1C.',
    'Properties': 'Item 2.',
    'Legal Proceedings': 'Item 3.',
    'Mine Safety Disclosures': 'Item 4.',
    'Common Equity & Related Matters': 'Item 5.',
    '[Reserved]': 'Item 6.',
    'Management’s Discussion & Analysis': 'Item 7.',
    'Market Risk Disclosures': 'Item 7A.',
    'Financial Statements & Data': 'Item 8.',
    'Accountant Changes & Disagreements': 'Item 9.',
    'Controls and Procedures': 'Item 9A.',
    'Other Information': 'Item 9B.',
    'Foreign Inspection Restrictions': 'Item 9C.',
    'Corporate Governance': 'Item 10.',
    'Executive Compensation': 'Item 11.',
    'Security Ownership and Management': 'Item 12',
    'Related Transactions and Director Independence': 'Item 13',
    'Accountant Fees and Services': 'Item 14.',
    'Exhibit and Financial Schedules': 'Item 15.',
    'Form 10-K Summary': 'Item 16.'
}

def configure_pdfkit(path_to_wkhtmltopdf):
    """
    Configures and returns the pdfkit configuration using a specified path to wkhtmltopdf.
    
    Args:
        path_to_wkhtmltopdf (str): The file path to the wkhtmltopdf executable.
        
    Returns:
        pdfkit.configuration: The configuration object for pdfkit.
    """
    try:
        return pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)
    except IOError:
        print("Failed to configure PDFKit. Please check the wkhtmltopdf path.")
        raise

def convert_html_to_pdf(source_html, output_pdf):
    """
    Converts an HTML file to a PDF using pdfkit.
    
    Args:
        source_html (str): The path to the source HTML file.
        output_pdf (str): The path where the output PDF should be saved.
        config (pdfkit.configuration): The configuration for pdfkit.
        
    Raises:
        Exception: If the HTML to PDF conversion fails.
    """
    
    if platform.system() == 'Windows':
        # On Windows, specify the path to wkhtmltopdf executable directly
        pdfkit_config = pdfkit.configuration(
            wkhtmltopdf=os.environ.get('WKHTMLTOPDF_PATH', r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')
        )
    else:
        # On non-Windows, use 'which' to find the path to wkhtmltopdf
        wkhtmltopdf_path = subprocess.Popen(
            ['which', os.environ.get('WKHTMLTOPDF_PATH', '/usr/local/bin/wkhtmltopdf')],
            stdout=subprocess.PIPE
        ).communicate()[0].strip().decode('utf-8')
        # pdfkit_config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
    
    # path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'  # Adjust this as needed
    config = configure_pdfkit(wkhtmltopdf_path)

    try:
        pdfkit.from_file(source_html, output_pdf, configuration=config)
        print(f"PDF successfully created at {output_pdf}.")
    except Exception as e:
        print(f"Failed to convert HTML to PDF: {e}")
        raise

def read_html_file(file_path):
    """Reads and returns the content of an HTML file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except IOError as e:
        print(f"Error reading file {file_path}: {e}")
        return None

def write_html_file(file_path, content):
    """Writes content to an HTML file at the specified path."""
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content.strip())
    except IOError as e:
        print(f"Error writing to file {file_path}: {e}")
        return False
    return True

def create_output_directory(directory):
    """Ensures the existence of the specified directory."""
    try:
        os.makedirs(directory, exist_ok=True)
    except OSError as e:
        print(f"Error creating directory {directory}: {e}")
        return False
    return True
    
def sanitize_filename(filename):
    """
    Sanitizes and formats the filename to avoid filesystem errors, preserving the file extension.
    """
    # Split the filename from its extension
    name, ext = os.path.splitext(filename)
    
    # Remove unwanted characters from the name part, replace spaces with underscores, and remove additional dots
    sanitized_name = re.sub(r'[^\w_-]', '', name.replace(' ', '_').replace('.', ''))
    filename = re.sub(r'[^\w_.)(-]', '', sanitized_name)
    
    # Combine the sanitized name with the original extension
    return f"{sanitized_name}{ext}"

def extract_text_from_html(html_content):
    """Extracts visible text from HTML content using BeautifulSoup."""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup.get_text(separator=' ', strip=True)
    except Exception as e:
        print(f"Error processing HTML content: {e}")
        return None

def find_items_in_html(html_content, item_pattern):
    """Finds and returns items in HTML content based on the specified pattern."""
    try:
        return re.findall(item_pattern, html_content, flags=re.IGNORECASE | re.DOTALL)
    except re.error as e:
        print(f"Error in regex pattern: {e}")
        return []

def disintegrate_file(file_path, output_dir, item=""):
    """
    Extracts sections from SEC filing HTML based on items and saves them as separate documents.
    
    Args:
        file_path (str): Path to the SEC HTML file.
        output_dir (str): Directory to save the output documents.
        item (str): Specific item to extract, defaults to all items.
    """
    html_content = read_html_file(file_path)
    if html_content is None:
        return "Failed to read HTML file."

    pattern = (fr"({re.escape(item)})(.*?)(?=Item \d+\.|$)" if item 
               else r"(Item \d+\.)(.*?)(?=Item \d+\.|$)")
    items = find_items_in_html(html_content, pattern)
    documents = []

    for title, doc in items:
        visible_text = extract_text_from_html(doc)
        if visible_text and len(visible_text) > 120:
            filename = sanitize_filename(f"{title}.html")
            documents.append((filename, doc))

    if not create_output_directory(output_dir):
        return "Failed to create output directory."

    saved_docs_count = 0
    for filename, doc in documents:
        output_file_path = os.path.join(output_dir, filename) 
        name, ext = os.path.splitext(filename)
        pdf_output = os.path.join(output_dir, f'{name}.pdf')
        if write_html_file(output_file_path, doc):
            saved_docs_count += 1

    if saved_docs_count > 0:
        print(f"{saved_docs_count} documents saved successfully.")
        
        convert_html_to_pdf(output_file_path, pdf_output)
        return pdf_output
    
    else:
        return "Failed to save any documents."

def download_10k_filings(ticker, start_year, end_year, item_title):
    """
    Downloads and processes 10-K filings from the SEC EDGAR database for a specified company and time frame.

    Args:
        ticker (str): Stock ticker symbol.
        start_year (int): Start year of the filing period.
        end_year (int): End year of the filing period.
        item_title (str): The title of the item to extract from the filings.
    """
    downloader = Downloader("MyCompanyName", "my.email@domain.com")

    for year in range(start_year, end_year + 1):
        try:
            downloader.get("10-K", ticker, after=f"{year-1}-12-31", before=f"{year+1}-01-01", download_details = True)
        except Exception as e:
            print(f"Error downloading files for year {year}: {e}")
            continue

        filing_path = os.path.join("sec-edgar-filings", ticker, "10-K")
        for root, _, files in os.walk(filing_path):
            for file in files:
                if file == "primary-document.html":
                    full_file_path = os.path.join(root, file)
                    if item_title == "Full Submission":
                        return full_file_path
                    else:
                        return disintegrate_file(full_file_path, root, item_table[item_title])
    return "No filings found or failed to process filings."
