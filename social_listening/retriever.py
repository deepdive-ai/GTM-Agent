"""Local BM25 passage retrieval. Scores indicate lexical relevance, never truth."""
import hashlib
import math
import re
from collections import Counter, defaultdict
from analyzer import AnalysisError

VERSION = 'passages-v2'
MODES = ('bm25', 'hybrid')
STOP = set('a an and are as at be been but by can could do does for from had has have how i if in is it its may of on or our should that the their them there these they this those to was we were what when where which who why will with would you your'.split())

def tokens(text):
    text = re.sub(r'https?://\S+', ' ', text.lower())
    # Conservative English inflections; no domain-specific synonym rules.
    result = []
    for term in re.findall(r'[^\W_]+', text, re.UNICODE):
        if term in STOP or len(term) < 2:
            continue
        if len(term) > 5 and term.endswith('ies'):
            term = term[:-3] + 'y'
        elif len(term) > 5 and term.endswith('s') and not term.endswith(('ss', 'us')):
            term = term[:-1]
        result.append(term)
    return result

def split_passages(source, size=1000, overlap=180):
    if not 0 <= overlap < size:
        raise ValueError('Overlap must be smaller than passage size.')
    text = source['text']
    urls = list(dict.fromkeys(re.findall(r'https?://[^\s<>]+', text)))
    status = [line.strip() for line in text.splitlines() if 'review pending' in line.lower() or 'review of this summary pending' in line.lower() or line.lower().startswith('status:')]
    result = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            # Prefer paragraph/sentence boundaries without creating tiny chunks.
            candidates = [text.rfind('\n\n', start + size // 2, end), text.rfind('. ', start + size // 2, end)]
            boundary = max(candidates)
            if boundary >= 0:
                end = boundary + (1 if text[boundary] == '.' else 2)
            else:
                boundary = text.rfind(' ', start + size // 2, end)
                if boundary >= 0:
                    end = boundary
        lo, hi = start, end
        while lo < hi and text[lo].isspace(): lo += 1
        while hi > lo and text[hi - 1].isspace(): hi -= 1
        if hi > lo:
            passage_id = 'passage-' + hashlib.sha256((source['name'] + '\0' + text + '\0' + str(lo)).encode()).hexdigest()[:16]
            result.append({'id': passage_id, 'document_id': source['id'], 'name': source['name'], 'text': text[lo:hi], 'start': lo, 'end': hi, 'line_start': text.count('\n', 0, lo) + 1, 'line_end': text.count('\n', 0, hi) + 1, 'source_urls': urls, 'review_metadata': status})
        if end == len(text): break
        next_start = max(start + 1, end - overlap)
        # Start overlap at a word boundary.
        while next_start < end and next_start > 0 and not text[next_start - 1].isspace(): next_start += 1
        start = next_start
    return result

class PassageIndex:
    def __init__(self, sources):
        self.passages = [p for s in sources for p in split_passages(s)]
        self.postings = defaultdict(dict)
        self.lengths = []
        for i, passage in enumerate(self.passages):
            counts = Counter(tokens(passage['text']))
            self.lengths.append(sum(counts.values()))
            for term, count in counts.items(): self.postings[term][i] = count
        self.average = sum(self.lengths) / max(1, len(self.lengths)) or 1

    def search(self, query, top_k=6):
        query_terms = set(tokens(query))
        scores = defaultdict(float)
        count = len(self.passages)
        for term in query_terms:
            posting = self.postings.get(term, {})
            idf = math.log(1 + (count - len(posting) + .5) / (len(posting) + .5))
            for i, frequency in posting.items():
                denominator = frequency + 1.5 * (.25 + .75 * self.lengths[i] / self.average)
                scores[i] += idf * frequency * 2.5 / denominator
        ranked = sorted(scores, key=lambda i: (-scores[i], self.passages[i]['id']))[:top_k]
        return [dict(self.passages[i], score=round(scores[i], 5), matched_terms=sorted(query_terms & set(tokens(self.passages[i]['text'])))) for i in ranked]

def retrieve(sources, query, top_k=6, mode="bm25"):
    if mode not in MODES:
        raise AnalysisError("Unknown retrieval method.")
    if not query.strip() or len(query) > 1500:
        raise AnalysisError('Enter a research question of 1-1,500 characters.')
    if not 1 <= top_k <= 12:
        raise AnalysisError('Retrieve between 1 and 12 passages.')
    index = PassageIndex(sources)
    passages = index.search(query, top_k)
    if mode == 'hybrid' and index.passages and tokens(query):
        from semantic_retriever import semantic_candidates
        semantic = semantic_candidates(index.passages, query)
        # Reciprocal rank fusion: avoid adding incomparable BM25/cosine scores.
        lexical = index.search(query, len(index.passages))
        by_id = {p['id']:i for i,p in enumerate(index.passages)}
        ranks = {}
        for rank,p in enumerate(lexical,1):
            i=by_id[p['id']]; ranks.setdefault(i,{})['keyword_rank']=rank
        for rank,i in enumerate(sorted(semantic,key=lambda i:(-semantic[i],index.passages[i]['id'])),1):
            ranks.setdefault(i,{})['semantic_rank']=rank
        fused={i:sum(1/(60+r) for r in values.values()) for i,values in ranks.items()}
        order=sorted(fused,key=lambda i:(-fused[i],-semantic.get(i,-1),index.passages[i]['id']))[:top_k]
        passages=[dict(index.passages[i],score=round(fused[i],6),matched_terms=sorted(set(tokens(query)) & set(tokens(index.passages[i]['text']))),semantic_similarity=round(semantic[i],5) if i in semantic else None,**ranks[i]) for i in order]
    matched = {term for p in passages for term in p['matched_terms']}
    corpus_id = hashlib.sha256(repr([(s['id'], s['name'], s['text']) for s in sources]).encode()).hexdigest()
    return {'method': mode+'-'+VERSION, 'query': query.strip(), 'corpus_fingerprint': corpus_id, 'indexed_documents': len(sources), 'indexed_passages': len(index.passages), 'top_k': top_k, 'passages': passages, 'unmatched_query_terms': sorted(set(tokens(query)) - matched), 'status': 'Candidate evidence; review relevance and completeness' if passages else 'No matching evidence', 'semantic_model': 'sentence-transformers/all-MiniLM-L6-v2' if mode == 'hybrid' else None, 'semantic_cutoff': 0.35 if mode == 'hybrid' else None, 'limitations': ('Experimental hybrid retrieval uses local English embeddings and rank fusion. The similarity cutoff is provisional; matching does not establish evidence sufficiency. The encoder reads up to 256 tokens per passage. ' if mode == 'hybrid' else '') + 'Keyword retrieval can miss paraphrases and cross-language matches. Matching passages do not establish that the question is answered. Review qualifications and source authority.'}
