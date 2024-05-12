import os
import sys
import streamlit as st
from datetime import datetime, timedelta
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.question_answering import load_qa_chain
from langchain_community.llms import GooglePalm
from langchain_community.embeddings import GooglePalmEmbeddings
from langchain_community.vectorstores import FAISS
import fitz 
import streamlit as st
import base64
import sys
from sec_download import download_10k_filings


google_api_key = os.environ.get('GOOGLE_API_KEY')
embeddings = GooglePalmEmbeddings()

# Load the PDF and create a vector store
def load_vector_store(pdf):
    if pdf:
        pdf_reader = PdfReader(pdf)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        # print(text)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200,
            length_function=len
            )
        chunks = text_splitter.split_text(text=text)
        vector_store = FAISS.from_texts(chunks, embedding=embeddings)
    return vector_store

# Create a function to get the LLM response
def get_llm_response(query, vector_store):
    if query:
        docs = vector_store.similarity_search(query=query, k=3)
        chain = load_qa_chain(GooglePalm(), chain_type="stuff")
        response = chain.run(input_documents=docs, question=query)
 
        print(response)
        return(response)
    return "NO RESPONSE"

def display_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    images = []
    for page in doc:
        pix = page.get_pixmap()
        img = pix.tobytes("png")
        images.append(img)
    
    # Create a container and custom CSS for scrolling
    st.markdown(
        """
        <style>
            .reportview-container .main .block-container{
                max-width: 100%;
            }
            .scrolling-wrapper{
                overflow-y: auto;
                height: 500px;
                width: 100%;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        "<div class='scrolling-wrapper'>" +
        "".join(f"<img src='data:image/png;base64,{base64.b64encode(image).decode()}' style='display:block; width:100%'/>"
                for image in images) +
        "</div>",
        unsafe_allow_html=True
    )

def custom_css():
    # This will increase the width of all select dropdowns when they are focused (clicked on)
    st.markdown("""
    <style>
    div.stSelectbox > div > select {
        width: 100% !important;
    }
    div.stSelectbox > div > select:focus {
        width: 250% !important;  /* Attempt to force width change on focus */
    }
    </style>
    """, unsafe_allow_html=True)


# Streamlit app
def main():

    custom_css()  # Apply custom CSS for select dropdowns
    st.title("Sec-Analysis")

    # Horizontal input elements
    col1, col4, col2, col3 = st.columns([2, 2, 2, 4])
    with col1:
        company = st.selectbox("Select a company", ["AAPL", "GOOGL", "MSFT"])
    with col4:
        doc_type = st.selectbox("Select doc type", ["10-K"])
    with col2:
        dateinput = st.selectbox("Select year", [2023, 2022, 2021])
    with col3:
        doc_type = st.selectbox("Select item type", [
    'Business',
    'Risk Factors',
    'Unresolved Staff Comments',
    'C',
    'Properties',
    'Legal Proceedings',
    'Mine Safety Disclosures',
    'Common Equity & Related Matters',
    '[Reserved]',
    'Management’s Discussion & Analysis',
    'Market Risk Disclosures',
    'Financial Statements & Data',
    'Accountant Changes & Disagreements',
    'Controls and Procedures',
    'Other Information',
    'Foreign Inspection Restrictions',
    'Corporate Governance',
    'Executive Compensation',
    'Security Ownership and Management',
    'Related Transactions and Director Independence',
    'Accountant Fees and Services',
    'Exhibit and Financial Schedules',
    'Form 10-K Summary'
], help="Select the specific item type from the document.")

    if st.button("Load Document"):
        file_path = download_10k_filings(company, dateinput, dateinput, doc_type)
        st.session_state.vector_store = load_vector_store(file_path)
        st.session_state.file_path = file_path
        st.session_state.document_loaded = True
    
    if 'document_loaded' in st.session_state:
        display_pdf(st.session_state.file_path)
        query = st.text_input("Ask a question")
        if st.button("Submit Query"):
            with st.spinner("Getting LLM response..."):
                response = get_llm_response(query, st.session_state.vector_store)
            st.write(response)
        else:
            st.error("Please load a document before submitting a query.")


if __name__ == "__main__":
    main()