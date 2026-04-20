"""
RAG Retriever module using ChromaDB for vector storage and retrieval.
Handles scheme embeddings and similarity search.
"""

import hashlib
import logging
import re
from typing import Dict, List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class RAGRetriever:
    """Vector-based RAG retriever for welfare schemes."""

    embedding_dim = 384
    
    def __init__(self, schemes_df: pd.DataFrame):
        """
        Initialize RAG retriever with schemes data.
        
        Args:
            schemes_df: DataFrame containing welfare schemes
        """
        self.schemes_df = schemes_df
        self.vector_db = None
        self.embeddings = None
        self.scheme_texts = []
        
        try:
            import chromadb
            self.chromadb = chromadb
            self._initialize_chromadb()
        except ImportError:
            logger.error("chromadb not installed. Install with: pip install chromadb")
            self.chromadb = None
    
    def _initialize_chromadb(self):
        """Initialize ChromaDB vector database."""
        try:
            logger.info("Initializing ChromaDB vector database...")
            
            # Create ephemeral client (in-memory)
            self.vector_db = self.chromadb.Client()
            
            # Create collection for schemes
            self.collection = self.vector_db.get_or_create_collection(
                name="welfare_schemes",
                metadata={"hnsw:space": "cosine"}
            )
            
            logger.info("ChromaDB initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            return False

    def _text_to_embedding(self, text: str) -> List[float]:
        """Convert text to a deterministic normalized embedding vector."""
        vector = np.zeros(self.embedding_dim, dtype=np.float32)

        tokens = re.findall(r"[\w']+", text.lower())
        if not tokens:
            return vector.tolist()

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "little") % self.embedding_dim
            vector[index] += 1.0

        norm = float(np.linalg.norm(vector))
        if norm > 0:
            vector /= norm

        return vector.tolist()
    
    def _prepare_scheme_text(self, scheme: pd.Series) -> str:
        """
        Prepare searchable text from scheme data.
        
        Args:
            scheme: Single scheme row from DataFrame
            
        Returns:
            Concatenated scheme text for embedding
        """
        # Extract key fields for embeddings
        fields_to_include = [
            'scheme_name',
            'category',
            'sub_category',
            'benefit_type',
            'eligibility_age_min',
            'eligibility_age_max',
            'eligible_gender',
            'eligible_caste',
            'eligible_religion',
            'income_limit_annual',
            'occupation',
            'education_required',
            'other_conditions',
            'keywords'
        ]
        
        text_parts = []
        for field in fields_to_include:
            if field in scheme.index and pd.notna(scheme[field]):
                value = str(scheme[field]).strip()
                if value and value.lower() != 'nan':
                    text_parts.append(value)
        
        return " ".join(text_parts)
    
    def build_index(self) -> bool:
        """
        Build vector index from schemes.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.vector_db is None:
                logger.error("Vector DB not initialized")
                return False
            
            logger.info(f"Building index for {len(self.schemes_df)} schemes...")
            
            # Prepare scheme texts
            self.scheme_texts = []
            embeddings = []
            ids = []
            metadatas = []
            
            for idx, scheme in self.schemes_df.iterrows():
                scheme_text = self._prepare_scheme_text(scheme)
                self.scheme_texts.append(scheme_text)
                embeddings.append(self._text_to_embedding(scheme_text))
                
                ids.append(f"scheme_{idx}")
                metadatas.append({
                    'scheme_name': str(scheme.get('scheme_name', '')),
                    'scheme_id': str(scheme.get('scheme_id', '')),
                    'category': str(scheme.get('category', '')),
                })
            
            # Add to collection with local embeddings to avoid external model downloads.
            self.collection.add(
                ids=ids,
                documents=self.scheme_texts,
                metadatas=metadatas,
                embeddings=embeddings
            )
            
            logger.info(f"Index built successfully with {len(self.scheme_texts)} schemes")
            return True
            
        except Exception as e:
            logger.error(f"Failed to build index: {e}")
            return False
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Retrieve top-K relevant schemes for query.
        
        Args:
            query: User query or eligibility criteria
            top_k: Number of top results to return
            
        Returns:
            List of relevant schemes with scores
        """
        try:
            if self.collection is None:
                logger.error("Vector DB collection not initialized")
                return []
            
            logger.debug(f"Retrieving top {top_k} schemes for query: {query[:100]}")

            query_embedding = self._text_to_embedding(query)
            
            # Query the collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=['distances', 'metadatas', 'documents']
            )
            
            # Transform results
            retrieved_schemes = []
            
            if results and results['metadatas'] and len(results['metadatas']) > 0:
                for i, (distance, metadata) in enumerate(
                    zip(results['distances'][0], results['metadatas'][0])
                ):
                    # Convert distance to similarity score (cosine distance to similarity)
                    similarity_score = 1 - distance  # Normalize distance to similarity
                    
                    scheme_id = metadata.get('scheme_id', '')
                    scheme_name = metadata.get('scheme_name', '')
                    
                    # Get full scheme from dataframe
                    matching_schemes = self.schemes_df[
                        self.schemes_df['scheme_id'] == scheme_id
                    ]
                    
                    if not matching_schemes.empty:
                        scheme_data = matching_schemes.iloc[0].to_dict()
                        scheme_data['similarity_score'] = similarity_score
                        retrieved_schemes.append(scheme_data)
            
            logger.debug(f"Retrieved {len(retrieved_schemes)} schemes")
            return retrieved_schemes
            
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return []
    
    def reload_schemes(self, schemes_df: pd.DataFrame) -> bool:
        """
        Reload schemes and rebuild index.
        
        Args:
            schemes_df: Updated DataFrame containing welfare schemes
            
        Returns:
            True if successful
        """
        try:
            self.schemes_df = schemes_df
            
            # Clear existing collection
            if self.collection:
                self.vector_db.delete_collection(name="welfare_schemes")
            
            # Recreate collection
            self.collection = self.vector_db.get_or_create_collection(
                name="welfare_schemes",
                metadata={"hnsw:space": "cosine"}
            )
            
            # Rebuild index
            return self.build_index()
            
        except Exception as e:
            logger.error(f"Failed to reload schemes: {e}")
            return False
