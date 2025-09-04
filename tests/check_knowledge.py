#!/usr/bin/env python3
"""
Check SQLite knowledge records
"""
import sys
sys.path.append('backend')

from models import SessionLocal
from models.database import KnowledgeChunk

def check_knowledge_records():
    """Check knowledge chunks in SQLite"""
    db = SessionLocal()
    
    try:
        # Get all knowledge chunks
        chunks = db.query(KnowledgeChunk).all()
        
        print(f"Total knowledge chunks in SQLite: {len(chunks)}")
        
        if chunks:
            # Group by agent_id
            agent_chunks = {}
            for chunk in chunks:
                if chunk.agent_id not in agent_chunks:
                    agent_chunks[chunk.agent_id] = []
                agent_chunks[chunk.agent_id].append(chunk)
            
            for agent_id, agent_chunk_list in agent_chunks.items():
                print(f"\nAgent {agent_id}: {len(agent_chunk_list)} chunks")
                
                # Group by source type
                by_source = {}
                for chunk in agent_chunk_list:
                    if chunk.source_type not in by_source:
                        by_source[chunk.source_type] = []
                    by_source[chunk.source_type].append(chunk)
                
                for source_type, source_chunks in by_source.items():
                    print(f"  - {source_type}: {len(source_chunks)} chunks")
                    if source_chunks:
                        print(f"    First chunk preview: {source_chunks[0].content[:100]}...")
        else:
            print("No knowledge chunks found in SQLite database")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_knowledge_records()
