"""
RAG (Retrieval Augmented Generation) engine that combines document retrieval with LLM generation.
"""
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain.callbacks import get_openai_callback

from .config import OPENAI_API_KEY, CHAT_MODEL, MAX_TOKENS, TEMPERATURE
from .vector_store import VectorStore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGEngine:
    """RAG engine that retrieves relevant documents and generates responses using LLM."""
    
    def __init__(self, vector_store: VectorStore):
        """Initialize the RAG engine with vector store and LLM."""
        self.vector_store = vector_store
        
        # Initialize ChatOpenAI
        self.llm = ChatOpenAI(
            openai_api_key=OPENAI_API_KEY,
            model_name=CHAT_MODEL,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE
        )
        
        # Create prompt templates
        self._create_prompt_templates()
        
        # Store conversation history
        self.conversation_history: List[BaseMessage] = []
        
        logger.info("RAG engine initialized successfully")
    
    def _create_prompt_templates(self):
        """Create prompt templates for different types of queries."""
        
        # System message for general Q&A
        self.system_template = """You are an AI assistant that helps users understand and analyze their documents. 
        You have access to relevant excerpts from the user's uploaded documents.

        Guidelines:
        1. Answer questions based primarily on the provided document context
        2. If the context doesn't contain enough information, clearly state this
        3. Provide specific references to the source material when possible
        4. Be concise but thorough in your explanations
        5. If asked about something not in the documents, politely redirect to document-related questions

        Context from documents:
        {context}

        Previous conversation (if any):
        {chat_history}
        """
        
        # Human message template
        self.human_template = """Question: {question}
        
        Please provide a helpful answer based on the document context above."""
        
        # Create the full prompt
        self.prompt_template = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(self.system_template),
            HumanMessagePromptTemplate.from_template(self.human_template)
        ])
    
    def _format_context(self, retrieved_docs: List) -> str:
        """Format retrieved documents into context string."""
        if not retrieved_docs:
            return "No relevant documents found."
        
        context_parts = []
        for i, doc in enumerate(retrieved_docs, 1):
            metadata = doc.metadata
            filename = metadata.get('filename', 'Unknown file')
            chunk_index = metadata.get('chunk_index', 'Unknown')
            
            context_parts.append(
                f"Document {i} (from {filename}, section {chunk_index}):\n{doc.page_content}\n"
            )
        
        return "\n---\n".join(context_parts)
    
    def _format_chat_history(self, limit: int = 5) -> str:
        """Format recent conversation history."""
        if not self.conversation_history:
            return "No previous conversation."
        
        # Get recent messages (limit to avoid token overflow)
        recent_messages = self.conversation_history[-limit*2:] if len(self.conversation_history) > limit*2 else self.conversation_history
        
        formatted_history = []
        for message in recent_messages:
            if isinstance(message, HumanMessage):
                formatted_history.append(f"Human: {message.content}")
            elif isinstance(message, AIMessage):
                formatted_history.append(f"Assistant: {message.content}")
        
        return "\n".join(formatted_history) if formatted_history else "No previous conversation."
    
    def retrieve_relevant_documents(self, query: str, k: int = None) -> Tuple[List, Dict]:
        """Retrieve relevant documents for a query."""
        try:
            # Perform similarity search with scores
            results_with_scores = self.vector_store.similarity_search_with_score(query, k)
            
            if not results_with_scores:
                return [], {'message': 'No relevant documents found', 'scores': []}
            
            # Extract documents and scores
            documents = [doc for doc, score in results_with_scores]
            scores = [score for doc, score in results_with_scores]
            
            retrieval_info = {
                'document_count': len(documents),
                'scores': scores,
                'average_score': sum(scores) / len(scores) if scores else 0,
                'source_files': list(set([doc.metadata.get('filename', 'Unknown') for doc in documents]))
            }
            
            logger.info(f"Retrieved {len(documents)} relevant documents")
            return documents, retrieval_info
            
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return [], {'error': str(e)}
    
    def generate_response(self, query: str, include_retrieval_info: bool = False) -> Dict:
        """Generate a response to a user query using RAG."""
        try:
            # Retrieve relevant documents
            retrieved_docs, retrieval_info = self.retrieve_relevant_documents(query)
            
            if not retrieved_docs and 'error' not in retrieval_info:
                return {
                    'answer': "I couldn't find any relevant information in your documents to answer this question. Please make sure you have uploaded documents or try rephrasing your question.",
                    'sources': [],
                    'retrieval_info': retrieval_info
                }
            
            # Format context and chat history
            context = self._format_context(retrieved_docs)
            chat_history = self._format_chat_history()
            
            # Create the prompt
            prompt_messages = self.prompt_template.format_messages(
                context=context,
                chat_history=chat_history,
                question=query
            )
            
            # Generate response with token tracking
            with get_openai_callback() as cb:
                response = self.llm(prompt_messages)
                
                # Extract token usage
                token_usage = {
                    'prompt_tokens': cb.prompt_tokens,
                    'completion_tokens': cb.completion_tokens,
                    'total_tokens': cb.total_tokens,
                    'total_cost': cb.total_cost
                }
            
            # Update conversation history
            self.conversation_history.append(HumanMessage(content=query))
            self.conversation_history.append(AIMessage(content=response.content))
            
            # Prepare source information
            sources = []
            for doc in retrieved_docs:
                sources.append({
                    'filename': doc.metadata.get('filename', 'Unknown'),
                    'chunk_index': doc.metadata.get('chunk_index', 'Unknown'),
                    'file_id': doc.metadata.get('file_id', 'Unknown'),
                    'preview': doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                })
            
            result = {
                'answer': response.content,
                'sources': sources,
                'token_usage': token_usage,
                'timestamp': datetime.now().isoformat()
            }
            
            if include_retrieval_info:
                result['retrieval_info'] = retrieval_info
            
            logger.info("Response generated successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                'answer': f"I encountered an error while processing your question: {str(e)}",
                'sources': [],
                'error': str(e)
            }
    
    def ask_question(self, question: str) -> Dict:
        """Simple interface to ask a question and get an answer."""
        return self.generate_response(question)
    
    def clear_conversation_history(self):
        """Clear the conversation history."""
        self.conversation_history = []
        logger.info("Conversation history cleared")
    
    def get_conversation_history(self) -> List[Dict]:
        """Get formatted conversation history."""
        formatted_history = []
        
        for i in range(0, len(self.conversation_history), 2):
            if i + 1 < len(self.conversation_history):
                human_msg = self.conversation_history[i]
                ai_msg = self.conversation_history[i + 1]
                
                formatted_history.append({
                    'question': human_msg.content,
                    'answer': ai_msg.content,
                    'timestamp': datetime.now().isoformat()  # In real app, you'd store actual timestamps
                })
        
        return formatted_history
    
    def summarize_document(self, file_id: str) -> Dict:
        """Generate a summary of a specific document."""
        try:
            # Get all chunks for the specific file
            docs_info = self.vector_store.search_by_metadata({'file_id': file_id})
            
            if not docs_info:
                return {
                    'summary': 'No document found with the specified ID.',
                    'error': 'Document not found'
                }
            
            # Combine all text from the document
            full_text = " ".join([doc['text'] for doc in docs_info])
            
            # Create summarization prompt
            summary_prompt = f"""Please provide a comprehensive summary of the following document:

            {full_text[:4000]}...  # Truncate to avoid token limits

            Focus on:
            1. Main topics and themes
            2. Key points and findings
            3. Important details and conclusions
            4. Overall structure and organization

            Provide a clear, well-structured summary."""
            
            return self.generate_response(summary_prompt)
            
        except Exception as e:
            logger.error(f"Error summarizing document: {e}")
            return {
                'summary': f"Error generating summary: {str(e)}",
                'error': str(e)
            }
    
    def get_statistics(self) -> Dict:
        """Get RAG engine statistics."""
        vector_stats = self.vector_store.get_collection_stats()
        
        return {
            'vector_store': vector_stats,
            'conversation_turns': len(self.conversation_history) // 2,
            'model_info': {
                'chat_model': CHAT_MODEL,
                'embedding_model': self.vector_store.embeddings.model,
                'max_tokens': MAX_TOKENS,
                'temperature': TEMPERATURE
            }
        }