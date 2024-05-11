import os
import streamlit as st
from datetime import datetime, timedelta
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.question_answering import load_qa_chain

from langchain_community.llms import GooglePalm
from langchain_community.embeddings import GooglePalmEmbeddings
from langchain_community.vectorstores import FAISS

google_api_key = os.environ.get('GOOGLE_API_KEY')
embeddings = GooglePalmEmbeddings()


def get_file_path(company, dateinput, doc_type):
    # Construct file name based on inputs
    file_name = f"{company}_{dateinput}_{doc_type}.pdf"
    folder_path = "C:\\Users\\ANU\\source\\repos\\fintech_app\\sampleinput"  # Update with your folder path
    file_path = os.path.join(folder_path, file_name)
    return file_path

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
        response = chain.invoke(input_documents=docs, question=query)
        print(response)
        return(response)
    return "NO RESPONSE"

def display_pdf(pdf_path):
    images = convert_from_path(pdf_path)
    for image in images:
        st.image(image, use_column_width=True)

# Streamlit app
def main():
    st.title("Sec-Analysis")

    # Sidebar inputs
    # companies = ["Apple", "Google", "Microsoft"]
    # company = st.sidebar.selectbox("Select a company", companies)

    # today = datetime.now().date()
    # start_date = st.sidebar.date_input("Start date", value=today - timedelta(days=30))
    # end_date = st.sidebar.date_input("End date", value=today)

    # doc_types = ["Financial Reports", "News Articles", "Product Reviews"]
    # doc_type = st.sidebar.selectbox("Select document type", doc_types)

    # # Upload PDF
    # uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    # if uploaded_file is not None:
    #     vector_store = load_vector_store(uploaded_file)

    #     # Chat functionality
    #     query = st.text_input("Ask a question")
    #     if st.button("Submit"):
    #         with st.spinner("Getting LLM response..."):
    #             response = get_llm_response(query, vector_store)
    #         st.write(response)


    # Horizontal input elements
    col1, col2, col3 = st.columns(3)
    with col1:
        company = st.selectbox("Select a company", ["Apple", "Google", "Microsoft"])
    with col2:
        dateinput = st.selectbox("Select year", ["2023", "2022", "2021"])
    with col3:
        doc_type = st.selectbox("Select document type", ["FULL", "News Articles", "Product Reviews"])

    # #Button to submit and load the document
    # if st.button("Load Document"):
    #     file_path = get_file_path(company, dateinput, doc_type)
    #     vector_store = load_vector_store(file_path)

    #     if vector_store:
    #         st.subheader("Selected Document:")
    #         st.write(file_path)
    #         # Display the PDF as images
    #         display_pdf(file_path)
    
    st.session_state.company_index = company
    st.session_state.year_index = dateinput
    st.session_state.doctype_index = doc_type

    if st.button("Load Document"):
        file_path = get_file_path(company, dateinput, doc_type)
        st.session_state.vector_store = load_vector_store(file_path)
        st.session_state.file_path = file_path

        if 'vector_store' in st.session_state and 'file_path' in st.session_state:
            st.subheader("Selected Document:")
            st.write(st.session_state.file_path)
            display_pdf(st.session_state.file_path)

            # Chat functionality
            query = st.text_input("Ask a question")
            if st.button("Submit Query"):
                with st.spinner("Getting LLM response..."):
                    response = get_llm_response(query, st.session_state.vector_store)
                st.write(response)

if __name__ == "__main__":
    main()