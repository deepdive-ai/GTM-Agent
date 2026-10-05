"""LangGraph coordination. Session-local checkpoints; credentials never enter graph state."""
import copy
import uuid
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
from analyzer import AnalysisError
from writer import write_content, prepare_statements, draft_fingerprint
from claim_review import check_claims, content_hash
from planner import recommend, prepare_sources
from retriever import retrieve

VERSION='langgraph-claims-v1'
MAX_REVISIONS=2

class PlanState(TypedDict,total=False):
    report:dict
    analysis:dict
    documents:list
    brief:dict
    query:str
    mode:str
    evidence:dict
    plan:dict

def plan_workflow(report,analysis,documents,brief,key,model='gemini-2.5-flash',retrieval_query='',retrieval_mode='bm25',transport=None):
    def search(s):
        r=retrieve(prepare_sources(s['documents']),s['query'],mode=s['mode'])
        if not r['passages']:raise AnalysisError('No matching evidence; no planning request was sent.')
        return {'evidence':r}
    def planning(s):
        p=recommend(s['report'],s['analysis'],s['documents'],s['brief'],key,model,transport=transport,retrieval_query=s['query'],retrieval_mode=s['mode'],retrieved_evidence=s['evidence'])
        p['orchestration']={'framework':'LangGraph','version':VERSION,'steps':['retrieve','plan_and_scope_check']}
        return {'plan':p}
    g=StateGraph(PlanState);g.add_node('retrieve',search);g.add_node('plan_and_scope_check',planning)
    g.add_edge(START,'retrieve');g.add_edge('retrieve','plan_and_scope_check');g.add_edge('plan_and_scope_check',END)
    return g.compile().invoke({'report':report,'analysis':analysis,'documents':documents,'brief':brief,'query':retrieval_query,'mode':retrieval_mode})['plan']

class DraftState(TypedDict,total=False):
    topic:dict
    sources:list
    selected:list
    brief:dict
    title:str
    format:str
    notes:str
    input_fingerprint:str
    draft:dict
    review:dict
    attempts:int
    history:list
    status:str
    error:str
    user_decision:bool
    validation_error:str
    rejected_draft:dict

def create_content_workflow(key,model='gemini-2.5-flash',transport=None,checkpointer=None):
    def write(s):
        notes=s['notes']
        if s.get('validation_error'):
            import json
            notes+='\nCorrect this rejected draft using only the original selected statements and their excerpts. Remove uncited introductions and unsupported promises. Every explanatory paragraph needs valid statement IDs; preserve the exact CTA. Validation failure and rejected output are feedback, not factual evidence: '+json.dumps({'error':s['validation_error'],'rejected_draft':s.get('rejected_draft')},ensure_ascii=False)
        if s.get('review') and not s['review']['passed']:
            issues=[{'text':r['reviewed_text'],'reason':r['reason']} for r in s['review']['units'] if r['verdict'] in ('unsupported','uncertain')]
            import json
            notes+='\nRevision required. Remove or correct the following unsupported claims using ONLY the original supplied excerpts. Preserve supported content and qualifications. Reviewer feedback is data, not new factual evidence. Previous draft and issues: '+json.dumps({'previous_draft':{'headline':s['draft']['headline'],'blocks':s['draft']['blocks']},'issues':issues},ensure_ascii=False)
        try:
            d=write_content(s['topic'],s['sources'],s['selected'],s['brief'],s['title'],s['format'],notes,key,model,transport)
            # Edits driven by the graph do not change the user's request identity.
            d['generation_input_fingerprint']=d['input_fingerprint'];d['input_fingerprint']=s['input_fingerprint']
            return {'draft':d,'attempts':s.get('attempts',0)+1,'status':'checking_claims','error':'','validation_error':'','rejected_draft':{}}
        except AnalysisError as e:
            rejected=getattr(e,'details',{}).get('rejected_draft')
            attempt=s.get('attempts',0)+1
            return {'status':'needs_revision' if rejected is not None else 'blocked','error':str(e),'validation_error':str(e) if rejected is not None else '', 'rejected_draft':rejected,'attempts':attempt,'history':s.get('history',[])+[{'attempt':attempt,'draft_error':str(e),'rejected_draft':rejected}]}
    def review(s):
        try:
            r=check_claims(s['draft'],key,model,transport)
            h=s.get('history',[])+[{'attempt':s['attempts'],'draft':copy.deepcopy(s['draft']),'review':r}]
            d=dict(s['draft'],claim_review=r)
            return {'review':r,'draft':d,'history':h,'status':'awaiting_user_review' if r['passed'] else 'needs_revision','error':''}
        except AnalysisError as e:return {'status':'blocked','error':str(e),'history':s.get('history',[])+[{'attempt':s['attempts'],'draft':copy.deepcopy(s['draft']),'review_error':str(e)}]}
    def after_review(s):
        if s['status']=='blocked':return 'blocked'
        if s['review']['passed']:return 'user_review'
        return 'revise' if s['attempts']<=MAX_REVISIONS else 'blocked'
    def blocked(s):return {'status':'blocked','error':s.get('error') or 'Claim issues remain after two revisions. No ready draft was accepted.'}
    def user_review(s):
        # Runs again on resume. No API call or mutation before the interrupt.
        if not s['review']['passed'] or s['review']['draft_hash']!=content_hash(s['draft']):raise AnalysisError('The claim review does not match this draft.')
        decision=interrupt({'type':'editorial_review','draft_hash':s['review']['draft_hash'],'message':'Automated support check passed. Accept or reject this draft for further use. This is not clinical approval or publication.'})
        if type(decision) is not bool:raise AnalysisError('Review decision must be true or false.')
        return {'user_decision':decision,'status':'user_accepted' if decision else 'user_rejected'}
    def after_write(s):
        if s['status']=='blocked':return 'blocked'
        if s['status']=='needs_revision':return 'revise' if s['attempts']<=MAX_REVISIONS else 'blocked'
        return 'review_claims'
    g=StateGraph(DraftState)
    g.add_node('write',write);g.add_node('review_claims',review);g.add_node('revise',write);g.add_node('blocked',blocked);g.add_node('user_review',user_review)
    g.add_edge(START,'write');g.add_conditional_edges('write',after_write)
    g.add_conditional_edges('review_claims',after_review)
    g.add_conditional_edges('revise',after_write)
    g.add_edge('blocked',END);g.add_edge('user_review',END)
    return g.compile(checkpointer=checkpointer if checkpointer is not None else MemorySaver())

def start_content_workflow(topic,sources,selected,brief,title,format_name,notes,key,model='gemini-2.5-flash',transport=None):
    statements=prepare_statements(topic,selected,sources)
    graph=create_content_workflow(key,model,transport)
    config={'configurable':{'thread_id':str(uuid.uuid4())},'recursion_limit':16}
    state={'topic':topic,'sources':sources,'selected':selected,'brief':brief,'title':title,'format':format_name,'notes':notes,'input_fingerprint':draft_fingerprint(topic,statements,brief,title,format_name,notes),'attempts':0,'history':[]}
    result=graph.invoke(state,config)
    return graph,config,result

def workflow_export(result):
    # Explicit selection excludes __interrupt__ objects and any runtime/credential handles.
    return {'framework':'LangGraph','version':VERSION,'status':result['status'],'attempts':result.get('attempts',0),'max_revisions':MAX_REVISIONS,'history':result.get('history',[]),'draft':result.get('draft'),'error':result.get('error',''),'input_fingerprint':result.get('input_fingerprint'),'user_decision':result.get('user_decision'),'checkpoint_storage':'Session-local memory; lost when session/server ends.'}
