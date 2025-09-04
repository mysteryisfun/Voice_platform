"""
ChromaDB service for vector storage and retrieval
"""
import chromadb
from chromadb.config import Settings
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import openai
from dotenv import load_dotenv
from sqlalchemy.orm import Session

load_dotenv()

class ChromaDBService:
    def __init__(self):
        # Initialize ChromaDB client with persistent storage
        # Create data directory if it doesn't exist
        data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chromadb_data")
        os.makedirs(data_path, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=data_path)
        
        # Initialize OpenAI for embeddings
        openai.api_key = os.getenv("OPENAI_API_KEY")
    
    def get_collection_name(self, agent_id: int) -> str:
        """Generate collection name for agent"""
        return f"agent_{agent_id}_knowledge"
    
    def _get_openai_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI"""
        try:
            response = openai.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating OpenAI embedding: {e}")
            # Fallback to default embedding if OpenAI fails
            return [0.0] * 1536  # text-embedding-3-small dimension
    
    def create_agent_collection(self, agent_id: int) -> chromadb.Collection:
        """Create or get collection for agent with OpenAI embeddings"""
        collection_name = self.get_collection_name(agent_id)
        
        try:
            # Try to get existing collection
            collection = self.client.get_collection(collection_name)
            print(f"Retrieved existing collection: {collection_name}")
            return collection
        except Exception:
            # Create new collection
            print(f"Creating new collection: {collection_name}")
            collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": f"Knowledge base for agent {agent_id}"}
            )
            return collection
    
    def add_documents(self, agent_id: int, documents: List[Dict[str, Any]], db: Optional[Session] = None) -> bool:
        """Add documents to agent's collection with OpenAI embeddings and SQLite tracking"""
        try:
            collection = self.create_agent_collection(agent_id)
            
            # Prepare data for ChromaDB
            ids = []
            texts = []
            metadatas = []
            embeddings = []
            
            for doc in documents:
                doc_id = f"agent_{agent_id}_{doc['source_type']}_{doc['chunk_index']:03d}"
                ids.append(doc_id)
                texts.append(doc['content'])
                metadatas.append({
                    "agent_id": agent_id,
                    "source_type": doc['source_type'],
                    "source_url": doc.get('source_url', ''),
                    "chunk_index": doc['chunk_index'],
                    "created_at": datetime.now().isoformat()
                })
                
                # Generate OpenAI embedding for this document
                embedding = self._get_openai_embedding(doc['content'])
                embeddings.append(embedding)
            
            # Add to ChromaDB collection with embeddings
            collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )
            
            # Also save to SQLite KnowledgeChunk table if db session provided
            if db:
                try:
                    from models.database import KnowledgeChunk
                    
                    for doc in documents:
                        knowledge_chunk = KnowledgeChunk(
                            agent_id=agent_id,
                            content_type=doc['source_type'],  # Map source_type to content_type
                            source_url=doc.get('source_url', ''),
                            chunk_index=doc['chunk_index'],
                            content=doc['content'],
                            chunk_id=f"agent_{agent_id}_{doc['source_type']}_{doc['chunk_index']:03d}",  # ChromaDB document ID
                            created_at=datetime.now()
                        )
                        db.add(knowledge_chunk)
                    
                    db.commit()
                    print(f"Saved {len(documents)} knowledge chunks to SQLite database")
                    
                except Exception as e:
                    print(f"Error saving knowledge chunks to SQLite: {e}")
                    if db:
                        db.rollback()
            
            print(f"Added {len(documents)} documents to collection {self.get_collection_name(agent_id)} with OpenAI embeddings")
            return True
            
        except Exception as e:
            print(f"Error adding documents to ChromaDB: {e}")
            return False
    
    def query_documents(self, agent_id: int, query: str, n_results: int = 5) -> List[Dict]:
        """Query agent's knowledge base using OpenAI embeddings"""
        try:
            collection_name = self.get_collection_name(agent_id)
            collection = self.client.get_collection(collection_name)
            
            # Generate embedding for the query using OpenAI
            query_embedding = self._get_openai_embedding(query)
            
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            for i, doc in enumerate(results['documents'][0]):
                formatted_results.append({
                    "content": doc,
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i],
                    "relevance_score": 1 - results['distances'][0][i]  # Convert distance to similarity
                })
            
            return formatted_results
            
        except Exception as e:
            print(f"Error querying ChromaDB: {e}")
            return []
    
    def delete_agent_collection(self, agent_id: int) -> bool:
        """Delete agent's entire collection"""
        try:
            collection_name = self.get_collection_name(agent_id)
            self.client.delete_collection(collection_name)
            print(f"Deleted collection: {collection_name}")
            return True
        except Exception as e:
            print(f"Error deleting collection: {e}")
            return False
    
    def get_collection_stats(self, agent_id: int) -> Dict:
        """Get statistics about agent's collection"""
        try:
            collection_name = self.get_collection_name(agent_id)
            collection = self.client.get_collection(collection_name)
            
            count = collection.count()
            
            return {
                "collection_name": collection_name,
                "document_count": count,
                "agent_id": agent_id
            }
        except Exception as e:
            print(f"Error getting collection stats: {e}")
            return {"error": str(e)}
