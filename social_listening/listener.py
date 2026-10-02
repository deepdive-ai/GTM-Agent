"""Small, local YouTube listening prototype. No model API or paid service."""
import datetime as dt
import html
import json
import re
import sqlite3
import urllib.parse
import urllib.request
import urllib.error

THEMES = {
    'Costs and access': ['cost', 'price', 'expensive', 'afford', 'insurance'],
    'Appointments and assessment': ['appointment', 'assessment', 'consultation', 'fitting', 'trial'],
    'Comfort and daily use': ['uncomfortable', 'comfort', 'insertion', 'insert', 'remove', 'fogging', 'cleaning'],
    'Options and expectations': ['option', 'options', 'crosslinking', 'cross-linking', 'surgery', 'results', 'expect'],
    'Uncertainty and reassurance': ['worried', 'scared', 'confused', 'afraid', 'anxious'],
}

class CollectionError(Exception):
    pass

def request(endpoint, key, **params):
    url = 'https://www.googleapis.com/youtube/v3/' + endpoint + '?' + urllib.parse.urlencode(dict(params, key=key))
    try:
        with urllib.request.urlopen(url, timeout=25) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        try:
            payload = json.loads(error.read())['error']
            reasons = [e.get('reason', '') for e in payload.get('errors', [])]
            reasons += [e.get('reason', '') for e in payload.get('details', [])]
            reason = ', '.join(dict.fromkeys(r for r in reasons if r)) or 'requestRejected'
            message = str(payload.get('message', ''))
            reason = reason + (': ' + message if message else '')
            reason = reason.replace(key, '[redacted]') if key else reason
            reason = re.sub(r'AIza[\w-]+', '[redacted]', reason)
            reason = re.sub(r'https?://\S+', '[Google help link omitted]', reason)
        except (ValueError, KeyError, IndexError, TypeError, AttributeError):
            reason = 'requestRejected'
        # Never expose request URLs containing the key.
        raise CollectionError(endpoint + ' | ' + str(error.code) + ': ' + reason[:1200]) from None
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        raise CollectionError('Network or response error. Check connectivity and retry.') from None

def collect(key, query, video_limit=5, comment_limit=50, days=365, language='en', fetch=request):
    if not key.strip() or not query.strip():
        raise ValueError('An API key and topic are required.')
    if not 1 <= video_limit <= 10 or not 1 <= comment_limit <= 100:
        raise ValueError('Use 1-10 videos and 1-100 comments per video.')
    since = (dt.datetime.now(dt.timezone.utc)-dt.timedelta(days=days)).isoformat().replace('+00:00','Z')
    results = fetch('search', key, part='snippet', q=query, type='video', order='relevance', maxResults=video_limit, publishedAfter=since, relevanceLanguage=language)
    ids = list(dict.fromkeys(x['id']['videoId'] for x in results.get('items', [])))
    report = {'query':query, 'collected_at':dt.datetime.now(dt.timezone.utc).isoformat(), 'settings':{'video_limit':video_limit,'comment_limit':comment_limit,'video_days':days,'language_hint':language}, 'videos':[], 'comments':[], 'warnings':[]}
    if not ids:
        return report
    videos = fetch('videos', key, part='snippet,statistics', id=','.join(ids))
    seen = set()
    for video in videos.get('items', []):
        vid = video['id']; snippet = video['snippet']
        report['videos'].append({'id':vid,'title':html.unescape(snippet['title']),'description':html.unescape(snippet.get('description','')),'channel':snippet['channelTitle'],'published_at':snippet['publishedAt'],'url':'https://www.youtube.com/watch?v='+vid,'statistics':video.get('statistics',{})})
        try:
            threads = fetch('commentThreads', key, part='snippet', videoId=vid, maxResults=comment_limit, order='time', textFormat='plainText')
        except CollectionError as error:
            if 'commentsDisabled' in str(error) or 'videoNotFound' in str(error):
                report['warnings'].append(vid + ': ' + str(error)); continue
            raise
        for thread in threads.get('items', []):
            item = thread['snippet']['topLevelComment']; s = item['snippet']
            if item['id'] in seen: continue
            seen.add(item['id'])
            report['comments'].append({'id':item['id'],'video_id':vid,'text':html.unescape(s['textDisplay']),'published_at':s['publishedAt'],'likes':s.get('likeCount',0),'url':'https://www.youtube.com/watch?v='+vid+'&lc='+urllib.parse.quote(item['id'],safe='')})
    return report

def themes(comments, rules=None):
    """Literal keyword candidates, not inferred facts, sentiment, or audience identities."""
    rules = THEMES if rules is None else rules
    grouped = {name:[] for name in rules}; seen = set(); unmatched = 0
    for c in comments:
        normalized = ' '.join(c['text'].lower().split())
        if normalized in seen: continue
        seen.add(normalized); matched = False
        for name, terms in rules.items():
            if any(re.search(r'(?<!\w)'+re.escape(t.lower())+r'(?!\w)', normalized) for t in terms if t.strip()):
                grouped[name].append(c); matched = True
        if not matched: unmatched += 1
    result = [{'theme':name,'count':len(items),'video_count':len({c['video_id'] for c in items}),'evidence':items} for name,items in grouped.items() if items]
    return sorted(result,key=lambda r:(-r['count'],r['theme'])), unmatched

def connect(path):
    db=sqlite3.connect(path)
    db.execute('CREATE TABLE IF NOT EXISTS runs (id INTEGER PRIMARY KEY, created TEXT, query TEXT, payload TEXT)')
    # Keep local API snapshots short lived; exports must be managed separately.
    cutoff=(dt.datetime.now(dt.timezone.utc)-dt.timedelta(days=29)).isoformat()
    db.execute('DELETE FROM runs WHERE created < ?', (cutoff,)); db.commit()
    return db

def save(db, report):
    with db:
        cursor=db.execute('INSERT INTO runs(created,query,payload) VALUES (?,?,?)',(report['collected_at'], report['query'],json.dumps(report)))
    return cursor.lastrowid

def previous_ids(db, query):
    ids=set()
    for (payload,) in db.execute('SELECT payload FROM runs WHERE query=?',(query,)):
        ids.update(c['id'] for c in json.loads(payload)['comments'])
    return ids

def demo():
    texts=['How much does a fitting cost?', 'I am worried about inserting lenses.', 'What should I expect at my appointment?', 'How do I manage fogging?', 'What options are available after cross-linking?', 'Thank you for explaining.']
    return {'query':'Keratoconus (synthetic demo)', 'collected_at':dt.datetime.now(dt.timezone.utc).isoformat(), 'settings':{}, 'videos':[], 'warnings':[], 'synthetic':True, 'comments':[{'id':'demo-'+str(i),'video_id':'fictional-'+str(i%2),'text':t,'published_at':'Synthetic example','likes':0,'url':''} for i,t in enumerate(texts)]}
