def split_documents(documents, chunk_size=1000, chunk_overlap=200):
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except ImportError as exc:
        raise ImportError(
            "langchain-text-splitters is required. Install: pip install langchain-text-splitters"
        ) from exc

    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_documents(documents)
