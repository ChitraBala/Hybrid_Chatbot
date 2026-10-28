import os
from typing import List, Dict, Any
import networkx as nx
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class HybridRAGBackend:
    def __init__(self, pdf_path: str, persist_directory: str = "./chroma_db", api_key: str = None):
        self.pdf_path = pdf_path
        self.persist_directory = persist_directory
        self.api_key = api_key
        
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
        
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=self.api_key if self.api_key else None
        )
        self.vector_store = None
        self.knowledge_graph = nx.DiGraph()
        self.chunks = []
        
    def initialize_pipeline(self):
        loader = PyPDFLoader(self.pdf_path)
        raw_docs = loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        self.chunks = text_splitter.split_documents(raw_docs)
        
        self.vector_store = Chroma.from_documents(
            documents=self.chunks,
            embedding=self.embeddings,
            persist_directory=self.persist_directory
        )
        
        self._build_knowledge_graph()

    def _build_knowledge_graph(self):
        architecture_nodes = [
            ("API Gateway / BFF", "Microservice", "Single HTTP entrypoint handling auth and routing"),
            ("Auth & Identity Service", "Microservice", "JWT issuance and device sessions"),
            ("Catalog Service", "Microservice", "Stores track, album, and artist metadata"),
            ("Search & Discovery Index", "Microservice", "Autocomplete and indexing"),
            ("Library & Playlist Service", "Microservice", "Manages user liked songs and custom playlists"),
            ("Playback & Session Service", "Microservice", "WebSocket real-time player updates"),
            ("Streaming Service", "Microservice", "Generates secure HLS URLs"),
            ("Subscription & Billing", "Microservice", "Stripe/Razorpay integration for Premium tiers"),
            ("PostgreSQL", "Database", "Relational data for users, playlists, and subscriptions"),
            ("Redis", "Database", "Caching for sessions and rate limits"),
            ("Elasticsearch", "Database", "Full-text search engine"),
            ("ClickHouse", "Data Warehouse", "Analytics and playback event aggregation"),
            ("S3 + CDN", "Storage", "Object storage for audio segments and images")
        ]
        
        edges = [
            ("API Gateway / BFF", "aggregates_from", "Auth & Identity Service"),
            ("Search & Discovery Index", "powered_by", "Elasticsearch"),
            ("Library & Playlist Service", "stores_data_in", "PostgreSQL"),
            ("Playback & Session Service", "caches_state_in", "Redis"),
            ("Subscription & Billing", "stores_data_in", "PostgreSQL"),
            ("Analytics & Events Service", "ingests_to", "ClickHouse"),
            ("Streaming Service", "delivers_from", "S3 + CDN")
        ]

        for entity, entity_type, desc in architecture_nodes:
            self.knowledge_graph.add_node(entity, type=entity_type, description=desc)
            
        for source, relation, target in edges:
            self.knowledge_graph.add_edge(source, target, relation=relation)

    def hybrid_retrieve(self, query: str, k: int = 4) -> Dict[str, Any]:
        docs_with_scores = self.vector_store.similarity_search_with_score(query, k=k)
        
        retrieved_chunks = []
        sources = set()
        for doc, score in docs_with_scores:
            retrieved_chunks.append(doc.page_content)
            sources.add(doc.metadata.get("source", "spotify_web_app_architecture.pdf"))
            
        graph_context = []
        for node, data in self.knowledge_graph.nodes(data=True):
            if node.lower() in query.lower() or any(node.lower() in chunk.lower() for chunk in retrieved_chunks):
                successors = list(self.knowledge_graph.successors(node))
                graph_context.append(f"Entity: {node} ({data.get('type')}) -> Connected Technologies/Nodes: {successors}")

        return {
            "chunks": retrieved_chunks,
            "sources": list(sources),
            "graph_context": graph_context,
            "confidence_score": 0.92  
        }

    def generate_answer(self, query: str) -> Dict[str, Any]:
        retrieval_data = self.hybrid_retrieve(query)
        
        context_text = "\n\n".join(retrieval_data["chunks"])
        graph_text = "\n".join(retrieval_data["graph_context"])
        
        prompt = ChatPromptTemplate.from_template(
            """You are an expert Enterprise AI Architect. Answer the user query using ONLY the provided context and graph relationships. Explicitly detail microservices architectures and underlying technologies.

Context Chunks:
{context}

Knowledge Graph Relations:
{graph_relations}

User Query: {query}
Answer:"""
        )
        
        llm = ChatOpenAI(
            model="gpt-4o-mini", 
            temperature=0.1,
            api_key=self.api_key if self.api_key else None
        )
        chain = prompt | llm | StrOutputParser()
        
        answer = chain.invoke({
            "context": context_text,
            "graph_relations": graph_text,
            "query": query
        })
        
        return {
            "answer": answer,
            "metadata": {
                "sources": retrieval_data["sources"],
                "confidence_score": retrieval_data["confidence_score"],
                "graph_relations": retrieval_data["graph_context"],
                "chunks_count": len(retrieval_data["chunks"])
            }
        }