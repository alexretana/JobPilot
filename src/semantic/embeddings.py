"""
Embedding service for JobPilot semantic matching.
Handles text embedding generation and similarity calculations.
"""

import os
from typing import List, Dict, Optional, Tuple
import numpy as np
from pathlib import Path
import pickle
import hashlib

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import torch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import LoggerMixin, log_error
from utils.config import settings


class EmbeddingService(LoggerMixin):
    """Service for generating and managing text embeddings."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize embedding service with specified model."""
        self.model_name = model_name
        self.model = None
        self.cache_dir = Path("data/embeddings")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize model
        self._load_model()
        
        self.logger.info(f"EmbeddingService initialized with model: {model_name}")
    
    def _load_model(self) -> None:
        """Load the sentence transformer model."""
        try:
            self.logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            
            # Check if CUDA is available and use it
            if torch.cuda.is_available():
                self.model = self.model.cuda()
                self.logger.info("Using CUDA for embeddings")
            else:
                self.logger.info("Using CPU for embeddings")
                
        except Exception as e:
            log_error(e, "loading embedding model")
            raise
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        return hashlib.md5(text.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get cache file path for embedding."""
        return self.cache_dir / f"{cache_key}.pkl"
    
    def _load_from_cache(self, cache_key: str) -> Optional[np.ndarray]:
        """Load embedding from cache if available."""
        cache_path = self._get_cache_path(cache_key)
        if cache_path.exists():
            try:
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                log_error(e, f"loading cached embedding {cache_key}")
        return None
    
    def _save_to_cache(self, cache_key: str, embedding: np.ndarray) -> None:
        """Save embedding to cache."""
        cache_path = self._get_cache_path(cache_key)
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(embedding, f)
        except Exception as e:
            log_error(e, f"saving embedding to cache {cache_key}")
    
    def embed_text(self, text: str, use_cache: bool = True) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text to embed
            use_cache: Whether to use caching for embeddings
            
        Returns:
            Numpy array containing the embedding
        """
        if not text or not text.strip():
            # Return zero vector for empty text
            return np.zeros(self.model.get_sentence_embedding_dimension())
        
        text = text.strip()
        
        # Check cache first
        if use_cache:
            cache_key = self._get_cache_key(text)
            cached_embedding = self._load_from_cache(cache_key)
            if cached_embedding is not None:
                return cached_embedding
        
        try:
            # Generate embedding
            embedding = self.model.encode(text, convert_to_numpy=True)
            
            # Cache the result
            if use_cache:
                cache_key = self._get_cache_key(text)
                self._save_to_cache(cache_key, embedding)
            
            return embedding
            
        except Exception as e:
            log_error(e, f"generating embedding for text: {text[:100]}...")
            # Return zero vector on error
            return np.zeros(self.model.get_sentence_embedding_dimension())
    
    def embed_texts(self, texts: List[str], use_cache: bool = True, batch_size: int = 32) -> List[np.ndarray]:
        """
        Generate embeddings for multiple texts efficiently.
        
        Args:
            texts: List of texts to embed
            use_cache: Whether to use caching
            batch_size: Batch size for processing
            
        Returns:
            List of embeddings as numpy arrays
        """
        if not texts:
            return []
        
        embeddings = []
        texts_to_embed = []
        indices_to_embed = []
        
        # Check cache for each text
        for i, text in enumerate(texts):
            if not text or not text.strip():
                embeddings.append(np.zeros(self.model.get_sentence_embedding_dimension()))
                continue
            
            text = text.strip()
            
            if use_cache:
                cache_key = self._get_cache_key(text)
                cached_embedding = self._load_from_cache(cache_key)
                if cached_embedding is not None:
                    embeddings.append(cached_embedding)
                    continue
            
            # Need to embed this text
            texts_to_embed.append(text)
            indices_to_embed.append(i)
            embeddings.append(None)  # Placeholder
        
        # Embed texts that aren't cached
        if texts_to_embed:
            try:
                self.logger.info(f"Generating embeddings for {len(texts_to_embed)} texts")
                batch_embeddings = self.model.encode(
                    texts_to_embed, 
                    batch_size=batch_size,
                    convert_to_numpy=True,
                    show_progress_bar=True
                )
                
                # Store embeddings and cache them
                for i, (text, embedding) in enumerate(zip(texts_to_embed, batch_embeddings)):
                    original_index = indices_to_embed[i]
                    embeddings[original_index] = embedding
                    
                    # Cache the embedding
                    if use_cache:
                        cache_key = self._get_cache_key(text)
                        self._save_to_cache(cache_key, embedding)
                        
            except Exception as e:
                log_error(e, "batch embedding generation")
                # Fill remaining slots with zero vectors
                zero_vector = np.zeros(self.model.get_sentence_embedding_dimension())
                for i in indices_to_embed:
                    if embeddings[i] is None:
                        embeddings[i] = zero_vector
        
        return embeddings
    
    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings."""
        try:
            # Reshape to 2D arrays for sklearn
            emb1 = embedding1.reshape(1, -1)
            emb2 = embedding2.reshape(1, -1)
            
            similarity = cosine_similarity(emb1, emb2)[0][0]
            return float(similarity)
            
        except Exception as e:
            log_error(e, "calculating embedding similarity")
            return 0.0
    
    def find_most_similar(self, 
                         query_embedding: np.ndarray, 
                         candidate_embeddings: List[np.ndarray],
                         top_k: int = 10) -> List[Tuple[int, float]]:
        """
        Find most similar embeddings to query.
        
        Args:
            query_embedding: Query embedding to match against
            candidate_embeddings: List of candidate embeddings
            top_k: Number of top matches to return
            
        Returns:
            List of (index, similarity_score) tuples, sorted by similarity desc
        """
        if not candidate_embeddings:
            return []
        
        try:
            # Calculate similarities
            similarities = []
            query_emb = query_embedding.reshape(1, -1)
            
            for i, candidate_emb in enumerate(candidate_embeddings):
                if candidate_emb is not None:
                    cand_emb = candidate_emb.reshape(1, -1)
                    similarity = cosine_similarity(query_emb, cand_emb)[0][0]
                    similarities.append((i, float(similarity)))
                else:
                    similarities.append((i, 0.0))
            
            # Sort by similarity descending and return top k
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:top_k]
            
        except Exception as e:
            log_error(e, "finding most similar embeddings")
            return []
    
    def embed_job_description(self, job_dict: Dict) -> np.ndarray:
        """
        Create embedding for a job description by combining relevant fields.
        
        Args:
            job_dict: Job dictionary with title, description, requirements, etc.
            
        Returns:
            Combined embedding for the job
        """
        # Combine relevant text fields
        text_parts = []
        
        # Add title with higher weight by repeating it
        if job_dict.get('title'):
            text_parts.extend([job_dict['title']] * 3)
        
        # Add description
        if job_dict.get('description'):
            text_parts.append(job_dict['description'])
        
        # Add requirements
        if job_dict.get('requirements'):
            if isinstance(job_dict['requirements'], list):
                text_parts.extend(job_dict['requirements'])
            else:
                text_parts.append(str(job_dict['requirements']))
        
        # Add responsibilities
        if job_dict.get('responsibilities'):
            if isinstance(job_dict['responsibilities'], list):
                text_parts.extend(job_dict['responsibilities'])
            else:
                text_parts.append(str(job_dict['responsibilities']))
        
        # Add skills
        if job_dict.get('skills_required'):
            if isinstance(job_dict['skills_required'], list):
                text_parts.append(", ".join(job_dict['skills_required']))
            else:
                text_parts.append(str(job_dict['skills_required']))
        
        if job_dict.get('skills_preferred'):
            if isinstance(job_dict['skills_preferred'], list):
                text_parts.append(", ".join(job_dict['skills_preferred']))
            else:
                text_parts.append(str(job_dict['skills_preferred']))
        
        # Combine all text parts
        combined_text = " ".join(filter(None, text_parts))
        
        # Generate embedding
        return self.embed_text(combined_text)
    
    def embed_user_profile(self, profile_dict: Dict) -> np.ndarray:
        """
        Create embedding for a user profile.
        
        Args:
            profile_dict: User profile dictionary
            
        Returns:
            Combined embedding for the user profile
        """
        text_parts = []
        
        # Add current title with higher weight
        if profile_dict.get('current_title'):
            text_parts.extend([profile_dict['current_title']] * 2)
        
        # Add preferred titles
        if profile_dict.get('preferred_titles'):
            if isinstance(profile_dict['preferred_titles'], list):
                text_parts.extend(profile_dict['preferred_titles'])
            else:
                text_parts.append(str(profile_dict['preferred_titles']))
        
        # Add skills
        if profile_dict.get('skills'):
            if isinstance(profile_dict['skills'], list):
                text_parts.append(", ".join(profile_dict['skills']))
            else:
                text_parts.append(str(profile_dict['skills']))
        
        # Add industry
        if profile_dict.get('industry'):
            text_parts.append(profile_dict['industry'])
        
        # Combine all text parts
        combined_text = " ".join(filter(None, text_parts))
        
        return self.embed_text(combined_text)
    
    def get_model_info(self) -> Dict:
        """Get information about the loaded model."""
        return {
            'model_name': self.model_name,
            'embedding_dimension': self.model.get_sentence_embedding_dimension() if self.model else None,
            'max_sequence_length': self.model.get_max_seq_length() if self.model else None,
            'device': str(self.model.device) if self.model else None,
        }
    
    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        try:
            import shutil
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                self.logger.info("Embedding cache cleared")
        except Exception as e:
            log_error(e, "clearing embedding cache")


# Global embedding service instance
embedding_service = EmbeddingService()
