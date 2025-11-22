"""
NITISARA RAG System
Retrieval Augmented Generation for trade compliance, documentation, and logistics knowledge
"""

import json
import re
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from gemini_chain import get_llm_response

@dataclass
class Document:
    """Structure for knowledge base documents"""
    id: str
    title: str
    content: str
    category: str
    tags: List[str]
    relevance_score: float = 0.0

class NitisaraRAG:
    """NITISARA RAG System for logistics knowledge retrieval"""
    
    def __init__(self):
        self.knowledge_base = self._initialize_knowledge_base()
        self.vector_embeddings = {}  # Simplified vector storage
        self.retrieval_threshold = 0.7
    
    def _initialize_knowledge_base(self) -> List[Document]:
        """Initialize knowledge base with trade compliance and logistics information"""
        documents = [
            Document(
                id="hs_codes_steel",
                title="HS Codes for Steel Products",
                content="Steel products fall under HS Chapter 72-73. Stainless steel articles: 7323.93.90, Carbon steel: 7225.40.00, Steel pipes: 7306.30.00",
                category="trade_compliance",
                tags=["steel", "hs_code", "classification"]
            ),
            Document(
                id="dgft_notifications",
                title="DGFT Export Notifications",
                content="DGFT notifications for export procedures, documentation requirements, and compliance standards for Indian exports.",
                category="trade_compliance",
                tags=["dgft", "export", "procedures", "india"]
            ),
            Document(
                id="shipping_documentation",
                title="Required Shipping Documents",
                content="Standard shipping documents: Commercial Invoice, Packing List, Bill of Lading, Certificate of Origin, Insurance Certificate, Export Declaration",
                category="documentation",
                tags=["documents", "shipping", "export", "import"]
            ),
            Document(
                id="co2e_calculations",
                title="CO2e Emission Calculations",
                content="Sea freight: 0.015 kg CO2e per kg per km. Air freight: 0.285 kg CO2e per kg per km. Road freight: 0.1 kg CO2e per kg per km.",
                category="esg",
                tags=["carbon", "emissions", "sustainability", "esg"]
            ),
            Document(
                id="port_congestion",
                title="Port Congestion Information",
                content="Major ports and congestion patterns: JNPT (Mumbai) - peak congestion Dec-Mar, Hamburg - peak congestion Oct-Dec, Singapore - generally efficient",
                category="logistics",
                tags=["ports", "congestion", "delays", "shipping"]
            ),
            Document(
                id="trade_restrictions",
                title="Trade Restrictions and Sanctions",
                content="Current trade restrictions: Steel anti-dumping duties in EU, Textile quotas in US, Electronics BIS certification in India",
                category="trade_compliance",
                tags=["restrictions", "sanctions", "duties", "quotas"]
            ),
            Document(
                id="payment_methods",
                title="International Payment Methods",
                content="Common payment methods: Letter of Credit (LC), Telegraphic Transfer (TT), Documentary Collection, Open Account, Advance Payment",
                category="payments",
                tags=["payment", "finance", "lc", "tt"]
            ),
            Document(
                id="insurance_requirements",
                title="Cargo Insurance Requirements",
                content="Standard cargo insurance covers: All Risks, General Average, War Risks. Minimum coverage: 110% of CIF value. Required for most shipments.",
                category="insurance",
                tags=["insurance", "coverage", "risk", "cargo"]
            )
        ]
        return documents
    
    def retrieve_relevant_documents(self, query: str, category: str = None, limit: int = 5) -> List[Document]:
        """Retrieve relevant documents based on query"""
        query_lower = query.lower()
        relevant_docs = []
        
        for doc in self.knowledge_base:
            # Filter by category if specified
            if category and doc.category != category:
                continue
            
            # Calculate relevance score
            relevance_score = self._calculate_relevance_score(query_lower, doc)
            
            if relevance_score >= self.retrieval_threshold:
                doc.relevance_score = relevance_score
                relevant_docs.append(doc)
        
        # Sort by relevance score and return top results
        relevant_docs.sort(key=lambda x: x.relevance_score, reverse=True)
        return relevant_docs[:limit]
    
    def _calculate_relevance_score(self, query: str, doc: Document) -> float:
        """Calculate relevance score between query and document"""
        score = 0.0
        
        # Title matching
        if any(word in doc.title.lower() for word in query.split()):
            score += 0.3
        
        # Content matching
        content_words = doc.content.lower().split()
        query_words = query.split()
        
        for query_word in query_words:
            if query_word in content_words:
                score += 0.2
        
        # Tag matching
        for tag in doc.tags:
            if tag in query:
                score += 0.1
        
        # Category matching
        if doc.category in query:
            score += 0.2
        
        return min(score, 1.0)
    
    def generate_rag_response(self, user_query: str, context: Dict = None) -> str:
        """Generate response using RAG system"""
        # Retrieve relevant documents
        relevant_docs = self.retrieve_relevant_documents(user_query)
        
        if not relevant_docs:
            return "I don't have specific information about that topic. Please provide more details or try a different query."
        
        # Build context from retrieved documents
        context_text = self._build_context_from_documents(relevant_docs)
        
        # Generate response using LLM with retrieved context
        rag_prompt = f"""
        You are Captain, NITISARA's AI logistics assistant. Use the following knowledge base information to answer the user's question accurately and comprehensively.
        
        KNOWLEDGE BASE CONTEXT:
        {context_text}
        
        USER QUESTION: {user_query}
        
        ADDITIONAL CONTEXT: {context or 'No additional context'}
        
        Instructions:
        1. Answer based on the knowledge base information provided
        2. If information is not available in the knowledge base, say so clearly
        3. Provide specific, actionable information
        4. Cite relevant sources when possible
        5. Maintain professional tone appropriate for logistics business
        
        Response:
        """
        
        try:
            response = get_llm_response(rag_prompt)
            return response
        except Exception as e:
            return f"I encountered an error while processing your request: {str(e)}. Please try again."
    
    def _build_context_from_documents(self, documents: List[Document]) -> str:
        """Build context string from retrieved documents"""
        context_parts = []
        
        for i, doc in enumerate(documents, 1):
            context_parts.append(f"""
Document {i}: {doc.title}
Category: {doc.category}
Content: {doc.content}
Relevance Score: {doc.relevance_score:.2f}
""")
        
        return "\n".join(context_parts)
    
    def add_document(self, title: str, content: str, category: str, tags: List[str]) -> str:
        """Add new document to knowledge base"""
        doc_id = f"custom_{len(self.knowledge_base) + 1}"
        new_doc = Document(
            id=doc_id,
            title=title,
            content=content,
            category=category,
            tags=tags
        )
        self.knowledge_base.append(new_doc)
        return doc_id
    
    def search_knowledge_base(self, query: str, category: str = None) -> List[Dict[str, Any]]:
        """Search knowledge base and return structured results"""
        relevant_docs = self.retrieve_relevant_documents(query, category)
        
        results = []
        for doc in relevant_docs:
            results.append({
                'id': doc.id,
                'title': doc.title,
                'content': doc.content,
                'category': doc.category,
                'tags': doc.tags,
                'relevance_score': doc.relevance_score
            })
        
        return results
    
    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base"""
        categories = {}
        total_docs = len(self.knowledge_base)
        
        for doc in self.knowledge_base:
            if doc.category not in categories:
                categories[doc.category] = 0
            categories[doc.category] += 1
        
        return {
            'total_documents': total_docs,
            'categories': categories,
            'retrieval_threshold': self.retrieval_threshold
        }

# Global RAG system instance
rag_system = NitisaraRAG()

def get_rag_response(query: str, category: str = None, context: Dict = None) -> str:
    """Convenience function to get RAG response"""
    return rag_system.generate_rag_response(query, context)

def search_knowledge_base(query: str, category: str = None) -> List[Dict[str, Any]]:
    """Convenience function to search knowledge base"""
    return rag_system.search_knowledge_base(query, category)

