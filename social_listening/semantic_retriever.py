"""Optional local semantic candidates. No document text is sent to an API."""
import os
from functools import lru_cache
from pathlib import Path
from analyzer import AnalysisError

MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
MIN_SIMILARITY = 0.35  # Provisional relevance cutoff, not confidence or sufficiency.

@lru_cache(maxsize=1)
def embedding_model():
    os.environ.setdefault('HF_HOME', str(Path(__file__).parent / '.model-cache' / 'huggingface'))
    try:
        from fastembed import TextEmbedding
    except ImportError:
        raise AnalysisError('Hybrid retrieval requires requirements-hybrid.txt. Choose Keyword (BM25) or install the optional local model dependencies.') from None
    try:
        return TextEmbedding(model_name=MODEL,cache_dir=os.environ.get('GTM_MODEL_CACHE',str(Path(__file__).parent / '.model-cache')),threads=2)
    except Exception:
        raise AnalysisError('The local embedding model could not load. Check the first-download connection or choose Keyword (BM25).') from None

# Document vectors are request-local; only the public model is cached.
def document_vectors(texts):
    import numpy as np
    vectors=np.asarray(list(embedding_model().embed(list(texts))),dtype=float)
    return vectors / np.maximum(np.linalg.norm(vectors,axis=1,keepdims=True),1e-12)

def semantic_candidates(passages,query,threshold=MIN_SIMILARITY):
    try:
        import numpy as np
        vectors=document_vectors(tuple(p['text'] for p in passages))
        q=np.asarray(list(embedding_model().query_embed(query))[0],dtype=float)
        q=q/max(float(np.linalg.norm(q)),1e-12)
        scores=np.sum(vectors*q,axis=1)
        if not np.all(np.isfinite(scores)):
            raise AnalysisError('Semantic similarity calculation was invalid; no matches were accepted.')
        return {i:float(score) for i,score in enumerate(scores) if score>=threshold}
    except AnalysisError: raise
    except Exception:
        raise AnalysisError('Local semantic retrieval failed. No silent fallback was used; choose Keyword (BM25) to continue.') from None
