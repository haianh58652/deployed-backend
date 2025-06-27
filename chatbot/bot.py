from huggingface_hub import InferenceClient
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import os
import time

# Simple wrapper for Hugging Face Inference Client
class HuggingFaceInferenceLLM:
    def __init__(self, api_key: str, model_name: str = "meta-llama/Llama-3.1-8B-Instruct"):
        self.client = InferenceClient(
            provider="hf-inference",
            api_key=api_key,
        )
        self.model_name = model_name
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate response from the model"""
        messages = [{"role": "user", "content": prompt}]
        
        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            max_tokens=kwargs.get('max_tokens', 512),
            temperature=kwargs.get('temperature', 0.7),
            **kwargs
        )
        
        return completion.choices[0].message.content

# RAG Query System
class RAGQuerySystem:
    def __init__(self, api_key: str, vectordb_path: str = "vectordb", 
                 model_name: str = "meta-llama/Llama-3.1-8B-Instruct",
                 embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """Initialize the RAG query system"""
        
        # Initialize the LLM
        self.llm = HuggingFaceInferenceLLM(api_key=api_key, model_name=model_name)
        
        # Initialize embeddings (must match the ones used to create the vector DB)
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model
        )
        
        # Load the vector store
        self.vectorstore = self._load_vectorstore(vectordb_path)
        
        # Custom prompt template for RAG
        self.prompt_template = """Use the following pieces of context to answer the human's question. 
If you don't know the answer based on the context, just say that you don't know, don't try to make up an answer.

Context:
{context}

Question: {question}

Helpful Answer:"""
    
    def _load_vectorstore(self, vectordb_path: str):
        """Load the pre-created vector store"""
        if not os.path.exists(vectordb_path):
            raise ValueError(f"Vector database not found at {vectordb_path}. Please create it first using create_vectordb.py")
        
        try:
            print(f"Loading vector database from: {vectordb_path}")
            vectorstore = FAISS.load_local(
                vectordb_path, 
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            print("Vector database loaded successfully!")
            return vectorstore
        except Exception as e:
            raise ValueError(f"Error loading vector database: {e}")
    
    def ask(self, question: str, k: int = 3, include_sources: bool = True):
        """Ask a question and get an answer based on the knowledge base"""
        
        # Retrieve relevant documents
        print(f"Searching for relevant documents...")
        relevant_docs = self.vectorstore.similarity_search(question, k=k)
        
        if not relevant_docs:
            return {
                "answer": "I couldn't find any relevant information to answer your question.",
                "source_documents": []
            }
        
        # Create context from retrieved documents
        context = "\n\n".join([doc.page_content for doc in relevant_docs])
        
        # Format the prompt
        prompt = self.prompt_template.format(context=context, question=question)
        
        # Generate answer using the LLM
        print("Generating answer...")
        answer = self.llm.generate(prompt)
        
        result = {
            "answer": answer,
        }
        
        if include_sources:
            result["source_documents"] = relevant_docs
            
        return result
    
    def chat(self, question: str) -> str:
        """Simple chat interface that returns just the answer"""
        result = self.ask(question, include_sources=False)
        return result["answer"]
    
    def interactive_chat(self):
        """Start an interactive chat session"""
        print("RAG Chatbot is ready! Type 'quit' to exit.")
        print("-" * 50)
        
        while True:
            question = input("\n🤔 Ask a question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not question:
                print("Please enter a question.")
                continue
            
            try:
                response = self.ask(question)
                print(f"\n🤖 Answer: {response['answer']}")
                
                # Show sources if available
                if 'source_documents' in response and response['source_documents']:
                    print(f"\n📚 Sources used:")
                    for i, doc in enumerate(response['source_documents']):
                        preview = doc.page_content[:100].replace('\n', ' ')
                        print(f"   {i+1}. {preview}...")
                        
            except Exception as e:
                print(f"❌ Error: {e}")