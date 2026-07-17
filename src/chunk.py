"""
chunk.py
Stage 2: split document text using LangChain's text splitters.

MarkdownHeaderTextSplitter splits along the document's own header structure
first (so a requirement/section stays intact), then RecursiveCharacterTextSplitter
re-splits any section still too long, trying paragraph -> line -> sentence ->
word boundaries in order before ever cutting mid-word.
"""

from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter


def chunk_document(text: str, chunk_size: int, chunk_overlap: int):
    headers_to_split_on = [
        ("##", "h2"),
        ("###", "h3"),
    ]
    md_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    header_splits = md_splitter.split_text(text)

    recursive_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    return recursive_splitter.split_documents(header_splits)


if __name__ == "__main__":
    from ingest import load_documents_from_dir
    from config import load_config

    cfg = load_config()
    docs = load_documents_from_dir(cfg.paths.raw_docs_dir)

    all_chunks = []
    for doc in docs:
        chunks = chunk_document(
            doc.text,
            chunk_size=cfg.chunking.max_chunk_size,
            chunk_overlap=cfg.chunking.overlap,
        )
        # tag each chunk with which source file it came from -- needed once
        # we have more than one doc, so retrieval results are traceable
        for c in chunks:
            c.metadata["source"] = doc.source_path
        all_chunks.extend(chunks)
        print(f"{doc.source_path}: {doc.char_count} chars -> {len(chunks)} chunks")

    print(f"\nTotal: {len(all_chunks)} chunks across {len(docs)} document(s)\n")

    for i, c in enumerate(all_chunks):
        section = c.metadata.get("h3", c.metadata.get("h2", "no header"))
        preview = c.page_content[:80].replace("\n", " ")
        print(f"[{i:2}] {section:45} | {preview}...")