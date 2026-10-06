"""Explicit local JSON campaign snapshots in SQLite. No credentials or executable objects."""
from contextlib import contextmanager
import copy
import datetime as dt
import json
import os
from pathlib import Path
import sqlite3
import uuid
from analyzer import AnalysisError
from campaign import export_package,package_fingerprint
from workflow import workflow_export

VERSION=1
MAX_BYTES=20_000_000
WIDGETS={'entry_mode','brief_business','brief_audience','brief_goal','brief_cta','brief_language','brief_tone','brief_source_status','brief_formats','evidence_search_mode','campaign_model','topic_choice'}
PREFIXES=('research_question_','question_choice_','evidence_review_','title_','facts_','format_','notes_','review_','package_formats_')
def widget_allowed(name):return name in WIDGETS or name.startswith(PREFIXES)

def pack_package(package):
    if not package:return None
    return {'request':copy.deepcopy(package['request']),'audit':export_package(package)}

def unpack_package(saved):
    if not saved:return None
    request=saved['request'];audit=saved['audit']
    expected=package_fingerprint(request['topic'],request['sources'],request['selected'],request['brief'],request['title'],audit['formats'],request['notes'],request['model'])
    if audit['input_fingerprint']!=expected:raise AnalysisError('Saved campaign package does not match its inputs.')
    return {'request':copy.deepcopy(request),'input_fingerprint':expected,'formats':audit['formats'],'items':{name:{'result':copy.deepcopy(row),'previous_runs':copy.deepcopy(row.get('previous_runs',[]))} for name,row in audit['items'].items()}}

def capture(state,documents,report,analysis,video_research,transcripts,model,brief,retrieval_mode):
    widgets={k:copy.deepcopy(v) for k,v in state.items() if widget_allowed(k)}
    widgets.update(campaign_model=model,brief_formats=brief['formats'],evidence_search_mode=retrieval_mode)
    single=None
    if state.get('content_workflow'):
        item=state['content_workflow'];result=item['result']
        if 'request' in item:request=item['request']
        else:request={k:copy.deepcopy(result[k]) for k in ('topic','sources','selected','brief','title','notes')};request['model']=model
        single={'request':request,'format':item.get('format') or result.get('format') or (result.get('draft') or {}).get('format'),'result':workflow_export(result)}
    return {'version':VERSION,'widgets':widgets,'documents':copy.deepcopy(documents),'report':copy.deepcopy(report),'analysis':copy.deepcopy(analysis),'video_research':copy.deepcopy(video_research),'transcripts':copy.deepcopy(transcripts),'topic_brief':copy.deepcopy(state.get('topic_brief')),'content_workflow':single,'campaign_package':pack_package(state.get('campaign_package'))}

def restore(state,snapshot):
    validate(snapshot)
    for key in list(state):
        if widget_allowed(key) or key in ('topic_brief','content_workflow','content_draft','campaign_package','analysis','video_research','transcripts','report','new_count','quota_diagnosis','transcript_report_id'):
            del state[key]
    for key,value in snapshot['widgets'].items():
        if widget_allowed(key):state[key]=copy.deepcopy(value)
    state['saved_campaign_documents']=copy.deepcopy(snapshot['documents'])
    state['use_saved_campaign_documents']=True
    # A new upload widget prevents previous campaign uploads leaking into this one.
    state['upload_generation']=str(uuid.uuid4())
    for key in ('report','analysis','video_research','transcripts','topic_brief'):
        if snapshot.get(key) is not None:state[key]=copy.deepcopy(snapshot[key])
    from analyzer import fingerprint
    state['transcript_report_id']=fingerprint(snapshot['report'])
    if snapshot.get('campaign_package'):state['campaign_package']=unpack_package(snapshot['campaign_package'])
    if snapshot.get('content_workflow'):
        item=copy.deepcopy(snapshot['content_workflow']);state['content_workflow']=item
        if item['result']['status'] in ('awaiting_user_review','user_accepted'):
            state['content_draft']=dict(item['result']['draft'],status=item['result']['status'])

def validate(snapshot):
    if not isinstance(snapshot,dict) or snapshot.get('version')!=VERSION:raise AnalysisError('Unsupported saved campaign version.')
    if not isinstance(snapshot.get('documents'),list) or not isinstance(snapshot.get('widgets'),dict):raise AnalysisError('Invalid saved campaign.')
    if any(not widget_allowed(k) for k in snapshot['widgets']):raise AnalysisError('Saved campaign contains unexpected settings.')
    if snapshot.get('campaign_package'):unpack_package(snapshot['campaign_package'])

@contextmanager
def connect(path):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists():
        fd=os.open(str(path),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(fd)
    db=sqlite3.connect(str(path));db.execute('CREATE TABLE IF NOT EXISTS campaigns (id TEXT PRIMARY KEY,name TEXT NOT NULL,updated TEXT NOT NULL,revision INTEGER NOT NULL,payload TEXT NOT NULL)')
    try:
        with db:yield db
    finally:db.close()

def save_campaign(path,name,snapshot,campaign_id=None,revision=None):
    validate(snapshot)
    if not isinstance(name,str) or not name.strip() or len(name)>160:raise AnalysisError('Enter a campaign name of 1–160 characters.')
    payload=json.dumps(snapshot,ensure_ascii=False)
    if len(payload.encode())>MAX_BYTES:raise AnalysisError('Campaign exceeds the 20 MB local-save limit.')
    updated=dt.datetime.now(dt.timezone.utc).isoformat()
    with connect(path) as db:
        if campaign_id:
            cursor=db.execute('UPDATE campaigns SET name=?,updated=?,revision=revision+1,payload=? WHERE id=? AND revision=?',(name.strip(),updated,payload,campaign_id,revision))
            if cursor.rowcount!=1:raise AnalysisError('This campaign changed in another session. Reopen it or save a new copy.')
            next_revision=revision+1
        else:
            campaign_id=str(uuid.uuid4());next_revision=1
            db.execute('INSERT INTO campaigns VALUES (?,?,?,?,?)',(campaign_id,name.strip(),updated,next_revision,payload))
    return {'id':campaign_id,'revision':next_revision,'name':name.strip(),'updated':updated}

def list_campaigns(path):
    with connect(path) as db:return [dict(zip(('id','name','updated','revision'),row)) for row in db.execute('SELECT id,name,updated,revision FROM campaigns ORDER BY updated DESC')]

def load_campaign(path,campaign_id):
    with connect(path) as db:row=db.execute('SELECT name,updated,revision,payload FROM campaigns WHERE id=?',(campaign_id,)).fetchone()
    if not row:raise AnalysisError('Saved campaign not found.')
    snapshot=json.loads(row[3]);validate(snapshot)
    return {'id':campaign_id,'name':row[0],'updated':row[1],'revision':row[2],'snapshot':snapshot}
