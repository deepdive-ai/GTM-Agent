import json
import os
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent / ".deps"))
sys.path.append(str(Path(__file__).parent / ".rag-deps"))
import streamlit as st
from analyzer import AnalysisError, analyze, fingerprint
from writer import write_content, prepare_statements, draft_fingerprint, plain_text, FORMATS
from video_research import fetch_transcript, research, research_fingerprint
from planner import recommend, prepare_sources, plan_fingerprint
from retriever import retrieve
from workflow import plan_workflow, start_content_workflow, workflow_export, can_resume_review, restore_content_workflow
from langgraph.types import Command
from campaign import create_package, package_fingerprint, export_package, package_markdown, decide, retry_format, resume_format_review
from platform_policy import assess_platform
from campaign_store import capture, restore, save_campaign, load_campaign, list_campaigns
from listener import THEMES, CollectionError, collect, connect, demo, previous_ids, save, themes

st.set_page_config(page_title='Audience Listening Lab', page_icon='🔎', layout='wide')
st.title('Audience Listening Lab')
st.write('Explore audience discussions, inspect the evidence, and decide what deserves further research.')
st.caption('YouTube audience research · Gemini interpretation · Source-linked evidence')
root=Path(__file__).parent
campaign_db=Path(os.environ.get('GTM_CAMPAIGN_DB',str(root/'campaigns.sqlite')))
if st.session_state.get('pending_campaign_restore'):
    saved=st.session_state.pop('pending_campaign_restore')
    try:
        restore(st.session_state,saved['snapshot'])
        st.session_state.active_campaign={k:saved[k] for k in ('id','revision','name','updated')}
        st.session_state.campaign_save_name=saved['name']
    except AnalysisError as error:st.error(str(error))
with st.sidebar:
    st.header('Saved campaigns')
    saved_campaigns=list_campaigns(campaign_db)
    if saved_campaigns:
        saved_choice=st.selectbox('Local campaigns',saved_campaigns,format_func=lambda x:x['name']+' · '+x['updated'][:16])
        def queue_campaign_restore():
            try:st.session_state.pending_campaign_restore=load_campaign(campaign_db,saved_choice['id'])
            except AnalysisError as error:st.session_state.campaign_open_error=str(error)
        st.button('Open campaign',on_click=queue_campaign_restore)
        if st.session_state.get('campaign_open_error'):st.error(st.session_state.pop('campaign_open_error'))
    else:st.caption('No saved campaigns yet.')
    st.caption('Opening replaces the current workspace. Save changes first. API keys are never included in campaign snapshots.')
# Preserve an already-open campaign when introducing keyed save controls.
existing_plan=st.session_state.get('topic_brief')
if existing_plan:
    for setting,value in {'brief_formats':existing_plan['brief']['formats'],'campaign_model':existing_plan.get('model','gemini-2.5-flash'),'evidence_search_mode':('hybrid' if existing_plan.get('retrieval',{}).get('method','').startswith('hybrid') else 'bm25')}.items():
        if setting not in st.session_state:st.session_state[setting]=value
    if 'saved_campaign_documents' not in st.session_state:
        st.session_state.saved_campaign_documents=[{'name':d['name'],'text':d['text']} for d in existing_plan.get('source_documents',[])]
        st.session_state.use_saved_campaign_documents=True
entry_mode=st.radio('How would you like to start?', ['Discover topics from audience comments','I already have a topic'],key='entry_mode')
direct_mode=entry_mode=='I already have a topic'
with st.sidebar:
    st.header('Research scope')
    query=st.text_input('Topic', 'keratoconus scleral lenses')
    videos=st.slider('Videos per search',1,10,5)
    comments=st.slider('Recent top-level comments per video',10,100,50,10)
    days=st.selectbox('Video publication window (days)',[30,90,365,1095],index=2)
    st.caption('The window filters videos. Comment dates are shown separately. Search favors English; it does not strictly filter language or location.')
    key=st.text_input('YouTube API key (session only)',type='password',value=os.environ.get('YOUTUBE_API_KEY',''))
    gemini_key=st.text_input('Gemini API key (session only)',type='password',value=os.environ.get('GEMINI_API_KEY',''),key='gemini_key',on_change=lambda:st.session_state.pop('quota_diagnosis',None))
    model=st.text_input('Gemini model',value='gemini-2.5-flash',key='campaign_model',on_change=lambda:st.session_state.pop('quota_diagnosis',None))
    st.caption('Analyze sends comment text, IDs, video titles and the topic to Google Gemini. Your account quota and pricing apply; free access is not guaranteed.')
    if st.button('Check Gemini access and quota',disabled=not gemini_key):
        from gemini_errors import probe_quota
        with st.spinner('Checking Gemini with one small request...'):
            st.session_state.quota_diagnosis=probe_quota(gemini_key,model)
    if st.session_state.get('quota_diagnosis'):st.info(st.session_state.quota_diagnosis)
    st.caption('Quota check sends only a short test prompt and consumes one API request.')
    run=st.button('Collect from YouTube',type='primary',disabled=not(key and query.strip()))
    if st.button('Explore synthetic demo'):
        st.session_state.report=demo(); st.session_state.new_count=None
    st.caption('The demo contains invented examples, not research findings.')
    with st.expander('Edit theme keywords'):
        rules_text=st.text_area('JSON theme definitions',json.dumps(THEMES,indent=2),height=250)
    if st.button('Delete local collection history'):
        with connect(root/'listening.sqlite') as db:
            db.execute('DELETE FROM runs'); db.commit()
        st.session_state.pop('report',None)
        st.success('Local collection history deleted.')
try:
    rules=json.loads(rules_text)
    if not isinstance(rules,dict) or not all(isinstance(k,str) and isinstance(v,list) and all(isinstance(t,str) for t in v) for k,v in rules.items()):
        raise ValueError()
except (ValueError,TypeError):
    st.error('Theme definitions must map names to lists of keywords.'); st.stop()
if run:
    try:
        with st.spinner('Collecting a bounded sample of videos and recent comments...'):
            report=collect(key,query.strip(),videos,comments,days)
            with connect(root/'listening.sqlite') as db:
                prior=previous_ids(db,query.strip())
                new_count=sum(c['id'] not in prior for c in report['comments'])
                save(db,report)
            st.session_state.report=report; st.session_state.new_count=new_count
    except (CollectionError,ValueError) as e:
        st.error(str(e))
if not direct_mode:
    with connect(root/'listening.sqlite') as db:
        history=db.execute('SELECT id,created,query FROM runs ORDER BY id DESC LIMIT 20').fetchall()
        if history:
            selection=st.selectbox('Saved runs',history,format_func=lambda r:r[1][:19]+' · '+r[2])
            if st.button('Open saved run'):
                st.session_state.report=json.loads(db.execute('SELECT payload FROM runs WHERE id=?',(selection[0],)).fetchone()[0]); st.session_state.new_count=None
    report=st.session_state.get('report')
    if not report:
        st.info('Start with the synthetic demo, or enter an API key to collect real evidence.'); st.stop()
    if report.get('synthetic'):
        st.warning('SYNTHETIC DEMO: all comments below are invented. No live research has been performed.')
    st.subheader(report['query'])
    st.caption('Collected: '+report['collected_at'])
    groups,unmatched=themes(report['comments'],rules)
    a,b,c=st.columns(3)
    a.metric('Videos collected',len(report['videos'])); b.metric('Comments collected',len(report['comments'])); c.metric('Keyword candidates',len(groups))
    if st.session_state.get('new_count') is not None:
        st.write(str(st.session_state.new_count)+' comment IDs not present in retained runs for this exact topic. This is sample discovery, not audience growth.')
    for warning in report['warnings']: st.warning(warning)
    st.info('AI findings describe the collected sample. They do not establish market demand, commenter location, medical facts, or content performance.')
    report_id=fingerprint(report)
    if st.session_state.get('analysis',{}).get('report_fingerprint')!=report_id:
        st.session_state.pop('analysis',None)
    st.subheader('AI audience analysis')
    st.caption('Interpret all collected comments, including Hindi and Hinglish. Evidence counts and links are checked by the app. Up to 100 comments per analysis.')
    if st.button('Analyze audience signals',type='primary',disabled=not(gemini_key and report['comments'])):
        try:
            with st.spinner('Gemini is interpreting comments and building evidence-linked themes...'):
                result=analyze(report,gemini_key,model)
                st.session_state.analysis=result
        except AnalysisError as error:
            st.error(str(error))
    analysis=st.session_state.get('analysis')
    if not gemini_key:
        st.info('Enter your separate Gemini API key in the sidebar, then click Analyze audience signals. You do not need to collect the comments again.')
    if analysis:
        st.caption('Analyzed by '+analysis['model']+' at '+analysis['analyzed_at'])
        lookup={c['id']:c for c in report['comments']}
        annotations={c['id']:c for c in analysis['comments']}
        totals={label:sum(c['relevance']==label for c in analysis['comments']) for label in ('relevant','irrelevant','uncertain')}
        st.write(' · '.join(str(n)+' '+label for label,n in totals.items()))
        for group in analysis['themes']:
            with st.expander(group['title']+' · '+str(group['comment_count'])+' comments across '+str(group['video_count'])+' videos',expanded=True):
                st.write('Interpretation: '+group['interpretation'])
                st.write('Content suggestion: '+group['suggestion'])
                st.write('Evidence needed before publishing: '+group['evidence_needed'])
                for eid in group['evidence_ids']:
                    evidence=lookup[eid]
                    st.text(evidence['text'])
                    st.write('Comment interpretation: '+annotations[eid]['interpretation'])
                    st.caption('Language: '+annotations[eid]['language']+' · '+evidence['published_at'])
                    if evidence['url']: st.link_button('View supporting comment',evidence['url'])
        with st.expander('Review excluded and uncertain comments'):
            for c in analysis['comments']:
                if c['relevance']=='relevant': continue
                st.text(lookup[c['id']]['text'])
                st.write(c['relevance'].capitalize()+': '+c['reason'])
                st.write('Meaning: '+c['interpretation'])
                if lookup[c['id']]['url']: st.link_button('View comment',lookup[c['id']]['url'])
        if not analysis['themes']: st.info('No supported relevant themes were identified in this sample.')
        st.caption('One comment may support multiple themes. Counts refer to comment IDs, not unique people. Exact duplicate text counts are included in the export. Check interpretations against the originals.')
    st.subheader('Video content research')
    st.caption('Compare this dated sample and inspect what the videos advertise. Spoken-content findings require an available transcript. This does not measure trends or conversions.')
    if st.session_state.get('transcript_report_id')!=report_id:
        st.session_state.transcripts={}; st.session_state.transcript_report_id=report_id
    transcripts=st.session_state.get('transcripts',{})
    if report['videos']:
        st.dataframe([{'Video':v['title'],'Published':v['published_at'],'Views':v.get('statistics',{}).get('viewCount'),'Likes':v.get('statistics',{}).get('likeCount'),'Total comments':v.get('statistics',{}).get('commentCount'),'Transcript':transcripts.get(v['id'],{}).get('status','not attempted'),'Link':v['url']} for v in report['videos']],hide_index=True)
        st.caption('Metrics are accumulated totals at '+report['collected_at']+'. Missing counts are unknown. Different video ages and audiences limit comparisons.')
    if st.button('Attempt free transcript retrieval',disabled=not report['videos']):
        progress=st.progress(0,text='Attempting free caption retrieval...')
        for i,video in enumerate(report['videos']):
            transcripts[video['id']]=fetch_transcript(video['id'])
            progress.progress((i+1)/len(report['videos']),text='Checked '+str(i+1)+' of '+str(len(report['videos']))+' videos')
        st.session_state.transcripts=transcripts
        progress.empty()
        st.rerun()
    for video in report['videos']:
        t=transcripts.get(video['id'],{})
        if t:
            with st.expander('Transcript: '+video['title']):
                if t.get('status')=='available':
                    st.caption(t['provider']+' · '+t['language']+' · '+('Auto-generated captions; may contain errors' if t['auto_generated'] else 'Uploaded captions; review accuracy'))
                    st.text(t['text'])
                else: st.write(t.get('reason','Unavailable'))
    research_id=research_fingerprint(report,transcripts)
    if st.session_state.get('video_research',{}).get('input_fingerprint')!=research_id:
        st.session_state.pop('video_research',None)
    if not gemini_key:
        st.info('To enable video analysis, enter your Gemini API key in the sidebar and press Enter. Keys are session-only; reopening or restarting the app may require entering it again. Transcript retrieval does not need this key.')
    elif not report['videos']:
        st.info('Open a saved YouTube run or collect videos to enable video analysis. The synthetic demo has no real videos.')
    if st.button('Analyze video content and opportunities',type='primary',disabled=not(gemini_key and report['videos'])):
        try:
            with st.spinner('Comparing video positioning, available transcripts and audience comments...'):
                st.session_state.video_research=research(report,transcripts,gemini_key,model)
        except AnalysisError as error: st.error(str(error))
    video_research=st.session_state.get('video_research')
    if video_research:
        st.success('Analysis complete: '+str(len(video_research['videos']))+' videos reviewed and '+str(len(video_research['opportunities']))+' proposed topics. Results are below.')
        vlookup={v['id']:v for v in report['videos']}; clookup={c['id']:c for c in report['comments']}
        st.info('Findings and opportunities describe this sample. Exact excerpt checks establish traceability, not correctness. Speaker claims require independent support before use as facts.')
        for row in video_research['videos']:
            with st.expander(vlookup[row['id']]['title'],expanded=True):
                st.link_button('View video',vlookup[row['id']]['url'])
                for finding in row['findings']:
                    st.write(finding['text']); st.caption('Evidence field: '+finding['field']); st.text(finding['excerpt'])
        for item in video_research['opportunities']:
            with st.expander('Proposed topic: '+item['title'],expanded=True):
                st.write(item['rationale'])
                st.write('Source evidence needed: '+item['source_evidence_needed'])
                for vid in item['video_ids']: st.link_button(vlookup[vid]['title'],vlookup[vid]['url'])
                for cid in item['comment_ids']:
                    st.text(clookup[cid]['text'])
                    if clookup[cid]['url']: st.link_button('View supporting audience comment',clookup[cid]['url'])

else:
    report={'input_mode':'direct','query':'User-selected topic','videos':[],'comments':[],'synthetic':False,'warnings':[],'collected_at':None}
    report_id=fingerprint(report)
    analysis={'themes':[],'comments':[]}
    video_research=None; transcripts={}; groups=[]; unmatched=0
    st.info('Start with your topic and source documents. No audience research is claimed in this mode. Without matching source evidence, factual drafting is blocked.')

st.subheader('Topics grounded in your sources')
st.write('Connect your topic to explanations your business can support.' if direct_mode else 'Connect audience questions to explanations your business can support.')
uploads=st.file_uploader('Upload source documents (.md or .txt)',type=['md','txt'],accept_multiple_files=True,key='sources_upload_'+st.session_state.get('upload_generation','initial'))
st.caption('Use approved material. On Generate, retrieved passages, the campaign brief and relevant comments are sent to Gemini. Use Save campaign below to keep documents and results locally between sessions.')
business=st.text_input('Business or product',key='brief_business')
audience=st.text_input('Target audience',key='brief_audience')
goal=st.text_input('Campaign goal',key='brief_goal')
formats=st.multiselect('Content formats',list(FORMATS),default=['LinkedIn post','Blog'],key='brief_formats')
cta=st.text_input('Call to action (optional)',key='brief_cta')
language=st.text_input('Content language',value='English',key='brief_language')
tone=st.text_input('Tone',value='Warm and reassuring',key='brief_tone')
source_status=st.selectbox('Source review status',['Draft material; review pending','Approved by the business'],key='brief_source_status')
brief={'business':business.strip(),'audience':audience.strip(),'goal':goal.strip(),'formats':formats,'call_to_action':cta.strip(),'language':language.strip(),'tone':tone.strip(),'source_review_status':source_status}
documents=[]; sources=[]; source_error=None
try:
    use_saved=bool(st.session_state.get('saved_campaign_documents')) and st.checkbox('Use saved campaign documents',key='use_saved_campaign_documents')
    documents=st.session_state['saved_campaign_documents'] if use_saved else [{'name':f.name,'text':f.getvalue().decode('utf-8')} for f in uploads]
    if use_saved:st.caption('Saved sources: '+', '.join(d['name'] for d in documents)+'. Uncheck to replace with uploaded documents.')
    if documents: sources=prepare_sources(documents)
except (UnicodeDecodeError,AnalysisError) as error:
    source_error='Upload UTF-8 Markdown or plain text.' if isinstance(error,UnicodeDecodeError) else str(error)
    st.error(source_error)
st.subheader('Find evidence for your topic' if direct_mode else 'Find evidence for an audience question')
question_choices={'Write my own question': ''}
if analysis and not direct_mode:
    supported_ids={eid for group in analysis['themes'] for eid in group['evidence_ids']}
    for comment in analysis.get('comments',[]):
        if comment['id'] in supported_ids:
            question_choices[comment['id']]=comment.get('interpretation','')
comment_text={c['id']:c['text'] for c in report['comments']}
question_choice='Write my own question' if direct_mode else st.selectbox('Audience question',list(question_choices),format_func=lambda x:comment_text.get(x,x),key='question_choice_'+report_id[:12])
question_key=report_id[:12]+'_'+question_choice
retrieval_query=st.text_input('Research question (use the language of your documents)',value=question_choices[question_choice],key='research_question_'+question_key).strip()
st.caption('Enter the question your content should answer. Evidence search runs locally without an API key.' if direct_mode else 'Select an audience comment or enter a question. Its AI interpretation is editable. Evidence search runs locally without an API key.')
retrieval_mode=st.selectbox('Evidence search method',['bm25','hybrid'],key='evidence_search_mode',format_func=lambda value: 'Keyword (BM25)' if value=='bm25' else 'Hybrid (experimental, local semantic + keyword)')
if retrieval_mode=='hybrid':
    st.caption('First use downloads a public embedding model. Document text stays local. This experimental English model can still return irrelevant passages.')
retrieval=None
if sources and retrieval_query:
    try:
        with st.spinner('Searching document passages...'):
            retrieval=retrieve(sources,retrieval_query,mode=retrieval_mode)
        st.success('Results updated for: '+retrieval_query)
        st.caption('Search method: '+('Hybrid semantic + keyword' if retrieval_mode=='hybrid' else 'Keyword (BM25)')+'. This updates evidence only; topic generation requires the review step below.')
        st.caption(str(retrieval['indexed_documents'])+' documents indexed into '+str(retrieval['indexed_passages'])+' passages. Showing '+str(len(retrieval['passages']))+' candidate passages.')
        if not retrieval['passages']:
            st.warning('No matching evidence found. Add relevant sources or revise the question. Content generation is blocked for this search.')
        else:
            st.info('These are candidate passages, not a finding that the question is answered. Check relevance, qualifications and missing details before continuing.')
            for passage in retrieval['passages']:
                with st.expander(passage['name']+' · lines '+str(passage['line_start'])+'–'+str(passage['line_end']),expanded=True):
                    st.text(passage['text'])
                    st.caption(passage['id']+' · Relevance score '+str(passage['score'])+' (not confidence)')
                    for url in passage['source_urls']: st.link_button('Original source',url)
                    for note in passage['review_metadata']: st.caption(note)
        with st.expander('Search coverage and limitations'):
            st.write(retrieval['limitations'])
            st.write('Question terms absent from retrieved passages: '+(', '.join(retrieval['unmatched_query_terms']) or 'None'))
        st.download_button('Download retrieved evidence (JSON)',json.dumps(retrieval,indent=2,ensure_ascii=False),file_name='retrieved-evidence.json',mime='application/json')
    except AnalysisError as error: st.error(str(error))
evidence_id=plan_fingerprint(report,analysis,sources,brief,retrieval_query,retrieval_mode) if sources else 'empty'
evidence_reviewed=st.checkbox('I reviewed the retrieved passages for relevance. Check for missing evidence when proposing the topic.',key='evidence_review_'+evidence_id[:16],disabled=not(retrieval and retrieval['passages']))

planning_analysis=dict(analysis,video_research=video_research) if analysis else None
plan_id=plan_fingerprint(report,planning_analysis,sources,brief,retrieval_query,retrieval_mode) if planning_analysis and sources else None
if st.session_state.get('topic_brief',{}).get('input_fingerprint')!=plan_id or not evidence_reviewed:
    st.session_state.pop('topic_brief',None)
ready=bool((direct_mode or (analysis and analysis['themes'])) and sources and business.strip() and audience.strip() and goal.strip() and formats and gemini_key and not source_error and retrieval and retrieval['passages'] and evidence_reviewed)
if st.button('Generate source-grounded topics',type='primary',disabled=not ready):
    try:
        with st.spinner('Planning from retrieved evidence, then checking question scope...'):
            st.session_state.topic_brief=plan_workflow(report,planning_analysis,documents,brief,gemini_key,model,retrieval_query=retrieval_query,retrieval_mode=retrieval_mode)
    except AnalysisError as error:
        st.error(str(error))
        if getattr(error,'details',None):
            with st.expander('Inspect rejected citation',expanded=True):st.json(error.details)
if not ready:
    st.caption('Upload sources, enter a research question, review retrieved evidence, and complete the campaign fields.' if direct_mode else 'Analyze the audience sample, upload sources, review retrieved evidence, and complete the campaign fields to generate a brief.')
topic_brief=st.session_state.get('topic_brief')
if topic_brief:
    if topic_brief.get('citation_location_corrections'):
        with st.expander('Exact-quote citation location corrections'):
            st.json(topic_brief['citation_location_corrections'])
    if topic_brief.get('scope_review'):
        st.caption('Question-scope review: '+topic_brief['scope_review']['reason']+' This is a model check, not factual approval.')
    st.info('These are proposed topics and draft statements. Citation checks confirm IDs and exact excerpts; you must review whether each excerpt supports the statement and whether the source is trustworthy.')
    comment_lookup={c['id']:c for c in report['comments']}
    source_lookup={s['id']:s for s in topic_brief['sources']}
    for topic in topic_brief['topics']:
        with st.expander(topic['title'],expanded=True):
            st.caption(topic['status']+' · Suggested format: '+topic['format'])
            st.write('Why this topic: '+topic['rationale'])
            st.write('User-selected topic; no audience evidence claimed.' if direct_mode else 'Audience evidence')
            for eid in topic['audience_ids']:
                comment=comment_lookup[eid]
                st.text(comment['text'])
                if comment.get('url'): st.link_button('View audience evidence',comment['url'])
            st.write('Draft explanation with source support')
            if not topic['statements']: st.warning('The uploaded sources do not support an explanation yet.')
            for statement in topic['statements']:
                st.write(statement['text'])
                for citation in statement['citations']:
                    st.caption(source_lookup[citation['source_id']]['name']+' · '+citation['source_id'])
                    st.text(citation['excerpt'])
            if topic['missing_evidence']:
                st.write('Questions to resolve before publishing')
                for gap in topic['missing_evidence']: st.write('• '+gap)
    st.download_button('Download topic brief (JSON)',json.dumps(topic_brief,indent=2,ensure_ascii=False),file_name='source-grounded-topic-brief.json',mime='application/json')

st.subheader('Review a topic and create content')
if not topic_brief:
    st.info('Generate a source-grounded topic brief first. Topics without source-backed statements need more evidence before content generation.')
    st.session_state.pop('content_draft',None)
    st.session_state.pop('content_workflow',None)
    st.session_state.pop('campaign_package',None)
else:
    choice=st.selectbox('Topic to review',range(len(topic_brief['topics'])),key='topic_choice',format_func=lambda i:topic_brief['topics'][i]['title'])
    chosen=topic_brief['topics'][choice]
    scope_key=topic_brief['input_fingerprint'][:12]+'_'+str(choice)
    reviewed_title=st.text_input('Reviewed topic title',value=chosen['title'],key='title_'+scope_key)
    selected=st.multiselect('Statements to use',range(len(chosen['statements'])),default=list(range(len(chosen['statements']))),format_func=lambda i:chosen['statements'][i]['text'],key='facts_'+scope_key)
    if chosen['missing_evidence']:
        st.warning('Unresolved questions remain. The draft must omit answers that these sources cannot support.')
        for question in chosen['missing_evidence']: st.write('• '+question)
    draft_format=st.selectbox('Draft format',list(FORMATS),key='format_'+scope_key)
    editor_notes=st.text_area('Editorial direction (adds no factual evidence)',key='notes_'+scope_key)
    reviewed=st.checkbox('I reviewed the selected statements and topic scope. Generate a draft for review, with source approval status retained.',key='review_'+scope_key)
    st.caption('Source status: '+topic_brief['brief'].get('source_review_status','Review status unknown')+'. This review step does not certify clinical accuracy or approve publication. On Generate, selected statements, source excerpts and the brief are sent to Gemini.')
    draft_id=None
    if selected:
        try:
            selected_statements=prepare_statements(chosen,selected,topic_brief['sources'])
            draft_id=draft_fingerprint(chosen,selected_statements,topic_brief['brief'],reviewed_title,draft_format,editor_notes)
        except AnalysisError as error: st.error(str(error))
    current_workflow=st.session_state.get('content_workflow')
    if not reviewed or (current_workflow and current_workflow['result'].get('input_fingerprint')!=draft_id):
        st.session_state.pop('content_workflow',None)
        st.session_state.pop('content_draft',None)
    if st.session_state.get('content_draft',{}).get('input_fingerprint')!=draft_id:
        st.session_state.pop('content_draft',None)
    if st.button('Generate complete content draft',type='primary',disabled=not(gemini_key and draft_id and reviewed and reviewed_title.strip())):
        try:
            with st.spinner('LangGraph: drafting, checking each claim, and revising if needed (up to two revisions)...'):
                st.session_state.pop('content_draft',None)
                st.session_state.pop('content_workflow',None)
                graph,config,result=start_content_workflow(chosen,topic_brief['sources'],selected,topic_brief['brief'],reviewed_title,draft_format,editor_notes,gemini_key,model)
                st.session_state.content_workflow={'graph':graph,'config':config,'result':result}
                if result['status']=='awaiting_user_review':
                    st.session_state.content_draft=dict(result['draft'],workflow=workflow_export(result),status='Automated source-support check passed; awaiting user review; not publication approval')
        except AnalysisError as error: st.error(str(error))
    if not chosen['statements']: st.info('This topic has no supported explanation yet. Upload further source material or choose a supported topic.')
    current_workflow=st.session_state.get('content_workflow')
    if current_workflow:
        outcome=current_workflow['result']
        st.caption('LangGraph workflow: '+outcome['status']+' · '+str(outcome.get('attempts',0))+' draft attempt(s). Save the campaign below to reopen this review after a restart.')
        with st.expander('Automated claim checks and revision history',expanded=outcome['status']=='blocked'):
            for attempt in outcome.get('history',[]):
                st.write('Attempt '+str(attempt['attempt']))
                if attempt.get('review_error'):st.error(attempt['review_error'])
                if attempt.get('draft_error'):st.error(attempt['draft_error'])
                for unit in attempt.get('review',{}).get('units',[]):
                    st.write(unit['verdict']+': '+unit['reviewed_text'])
                    st.caption(unit['reason'])
        if outcome['status']=='blocked':
            st.error(outcome['error'])
            if can_resume_review(outcome) and st.button('Resume existing draft review',disabled=not gemini_key):
                try:
                    request=current_workflow.get('request') or {k:outcome[k] for k in ('topic','sources','selected','brief','title','notes')}
                    request=dict(request,model=model)
                    graph,config,result=restore_content_workflow(request,draft_format,outcome,gemini_key,resume_review=True)
                    current_workflow.update(graph=graph,config=config,result=result,request=request)
                    if result['status']=='awaiting_user_review':st.session_state.content_draft=dict(result['draft'],status='Automated check passed; awaiting user review')
                    st.rerun()
                except AnalysisError as error:st.error(str(error))
            st.warning('No draft is ready for user acceptance. Inspect the audit, add evidence or change the scope before retrying.')
        st.download_button('Download workflow audit (JSON)',json.dumps(workflow_export(outcome),indent=2,ensure_ascii=False),file_name='gtm-workflow-audit.json',mime='application/json')
        if outcome['status']=='awaiting_user_review':
            st.info('Automated claim support passed. Review the text and evidence below, then accept or reject. This check does not establish source truth or clinical approval.')
            policy=assess_platform(outcome['draft'])
            if policy['status']=='withheld':st.warning(policy['reason']);st.link_button('Google post policy',policy['policy_url'])
            accept=st.button('Accept reviewed draft',disabled=policy['status']=='withheld')
            reject=st.button('Reject draft')
            if accept or reject:
                try:
                    if 'graph' not in current_workflow:
                        graph,config,result=restore_content_workflow(current_workflow['request'],draft_format,outcome)
                        current_workflow.update(graph=graph,config=config,result=result)
                    result=current_workflow['graph'].invoke(Command(resume=bool(accept)),current_workflow['config'])
                    current_workflow['result']=result
                    if accept:
                        st.session_state.content_draft=dict(result['draft'],workflow=workflow_export(result),status='User accepted; source and clinical approval requirements still apply')
                    else:st.session_state.pop('content_draft',None)
                    st.rerun()
                except AnalysisError as error:st.error(str(error))
    content_draft=st.session_state.get('content_draft')
    if content_draft:
        st.success(content_draft['status'])
        st.subheader(content_draft['headline'])
        for paragraph in content_draft['blocks']: st.write(paragraph['text'])
        with st.expander('Check paragraph sources and limitations',expanded=True):
            statement_lookup={s['id']:s for s in content_draft['statements']}
            names={s['id']:s['name'] for s in topic_brief['sources']}
            for paragraph in content_draft['blocks']:
                if paragraph['kind']!='factual': continue
                st.write(paragraph['text'])
                for sid in paragraph['statement_ids']:
                    st.caption(sid+': '+statement_lookup[sid]['text'])
                    for citation in statement_lookup[sid]['citations']:
                        st.caption(names[citation['source_id']]); st.text(citation['excerpt'])
            for note in content_draft['review_notes']: st.write('• '+note)
        single_policy=assess_platform(content_draft)
        st.download_button('Download content draft (TXT)',plain_text(content_draft),disabled=single_policy['status']=='withheld',file_name='gtm-content-draft.txt',mime='text/plain')
        st.download_button('Download draft with sources (JSON)',json.dumps(content_draft,indent=2,ensure_ascii=False),file_name='gtm-content-draft.json',mime='application/json')


    st.subheader('Create a campaign package')
    package_formats=st.multiselect('Formats in this package',list(FORMATS),default=list(FORMATS),key='package_formats_'+scope_key)
    st.caption('Each format gets its own draft, source-support review and up to two revisions. A three-format package uses 6–18 drafting/review model calls. Review and accept each format separately; nothing is published.')
    package_id=package_fingerprint(chosen,topic_brief['sources'],selected,topic_brief['brief'],reviewed_title,package_formats,editor_notes,model)
    package=st.session_state.get('campaign_package')
    if not reviewed or (package and package['input_fingerprint']!=package_id):
        st.session_state.pop('campaign_package',None)
        package=None
    if st.button('Generate campaign package',type='primary',disabled=not(gemini_key and draft_id and reviewed and package_formats and reviewed_title.strip())):
        try:
            st.session_state.pop('campaign_package',None)
            progress=st.progress(0,text='Starting campaign package...')
            def package_progress(index,total,name):
                progress.progress(index/total,text='Drafting and reviewing '+name+' ('+str(index+1)+'/'+str(total)+')')
            package=create_package(chosen,topic_brief['sources'],selected,topic_brief['brief'],reviewed_title,package_formats,editor_notes,gemini_key,model,progress=package_progress)
            st.session_state.campaign_package=package
            progress.empty()
        except AnalysisError as error:st.error(str(error))
    if package:
        if 'request' not in package:
            package['request']={'topic':chosen,'sources':topic_brief['sources'],'selected':selected,'brief':topic_brief['brief'],'title':reviewed_title,'notes':editor_notes,'model':model}
        st.write('Package status: '+export_package(package)['status'])
        tabs=st.tabs(package['formats'])
        for tab,name in zip(tabs,package['formats']):
            with tab:
                item=package['items'][name]; result=item['result']
                policy=assess_platform(result.get('draft') or {})
                if policy['status']=='withheld':st.warning(policy['reason']);st.link_button('Platform policy for '+name,policy['policy_url'])
                st.caption(name+' · '+result['status']+' · '+str(result.get('attempts',0))+' draft attempt(s)')
                if result['status'] in ('awaiting_user_review','user_accepted'):
                    draft=result['draft'];st.subheader(draft['headline'])
                    for paragraph in draft['blocks']:st.write(paragraph['text'])
                    with st.expander('Sources and review notes for '+name):
                        for statement in draft['statements']:
                            st.write(statement['id']+': '+statement['text'])
                            for citation in statement['citations']:st.text(citation['source_id']+': '+citation['excerpt'])
                        for note in draft['review_notes']:st.write(note)
                elif result['status']=='blocked':st.error(result.get('error','Draft blocked.'))
                else:st.info('Draft rejected. Generate a new package after revising the brief or evidence.')
                if result['status'] in ('blocked','user_rejected') and package.get('request'):
                    if can_resume_review(result) and st.button('Resume review '+name,key='package_resume_'+name,disabled=not gemini_key):
                        try:
                            with st.spinner('Reviewing the existing '+name+' draft...'):resume_format_review(package,name,gemini_key)
                            st.rerun()
                        except AnalysisError as error:st.error(str(error))
                    if st.button('Retry '+name,key='package_retry_'+name,disabled=not gemini_key):
                        with st.spinner('Retrying only '+name+'...'):
                            retry_format(package,name,gemini_key)
                        st.rerun()
                if item.get('previous_runs'):st.caption(str(len(item['previous_runs']))+' earlier run(s) retained in the campaign audit.')
                with st.expander('Automatic review history for '+name):
                    for attempt in result.get('history',[]):
                        st.write('Attempt '+str(attempt['attempt']))
                        if attempt.get('review_error'):st.error(attempt['review_error'])
                        if attempt.get('draft_error'):st.error(attempt['draft_error'])
                        for unit in attempt.get('review',{}).get('units',[]):
                            st.write(unit['verdict']+': '+unit['reviewed_text']);st.caption(unit['reason'])
                if result['status']=='awaiting_user_review':
                    accepted=st.button('Accept '+name,key='package_accept_'+name,disabled=policy['status']=='withheld')
                    rejected=st.button('Reject '+name,key='package_reject_'+name)
                    if accepted or rejected:
                        try:
                            decide(package,name,bool(accepted),key=gemini_key);st.rerun()
                        except AnalysisError as error:st.error(str(error))
        st.download_button('Download campaign package (Markdown)',package_markdown(package),file_name='campaign-package.md',mime='text/markdown')
        st.download_button('Download campaign audit (JSON)',json.dumps(export_package(package),indent=2,ensure_ascii=False),file_name='campaign-audit.json',mime='application/json')

with st.expander('Basic keyword comparison (not AI analysis)'):
    st.write([{'theme':g['theme'],'keyword_matches':g['count']} for g in groups])
    st.caption(str(unmatched)+' distinct texts did not match a configured keyword.')
with st.expander('All collected comments and video context'):
    st.json({'videos':report['videos'],'comments':report['comments']})
export=dict(report,campaign_package=export_package(st.session_state.campaign_package) if st.session_state.get('campaign_package') else None,keyword_candidates=groups,ai_analysis=analysis,video_research=video_research,transcripts=transcripts,topic_brief=topic_brief,content_draft=st.session_state.get('content_draft'),retrieval=retrieval,workflow=workflow_export(st.session_state.content_workflow['result']) if st.session_state.get('content_workflow') else None)
st.download_button('Download evidence report (JSON)',json.dumps(export,indent=2),file_name='audience-evidence.json',mime='application/json')
st.caption('API keys are not saved. Collection-history snapshots expire on app access after 29 days; explicitly saved campaigns do not. Delete exported reports separately when no longer needed. Analysis is sent to Gemini only when you click Analyze. AI results are held in this session and included in your download; they are not saved to collection history. No content is published.')


st.subheader('Save this campaign')
st.caption('Keeps source documents, campaign details, drafts and review history on this computer. API keys are excluded. Save again after making changes. Campaign saves remain until removed from local storage.')
if 'campaign_save_name' not in st.session_state:
    st.session_state.campaign_save_name=st.session_state.get('active_campaign',{}).get('name','')
name=st.text_input('Campaign name',key='campaign_save_name')
save_current=st.button('Save campaign',disabled=not(name.strip() and documents))
save_copy=st.button('Save as new campaign',disabled=not(name.strip() and documents)) if st.session_state.get('active_campaign') else False
if save_current or save_copy:
    try:
        snapshot=capture(st.session_state,documents,report,analysis,video_research,transcripts,model,brief,retrieval_mode)
        active=st.session_state.get('active_campaign',{}) if not save_copy else {}
        saved=save_campaign(campaign_db,name,snapshot,active.get('id'),active.get('revision'))
        st.session_state.active_campaign=saved
        st.success('Saved locally: '+saved['name']+'. Reopen it from Saved campaigns in the sidebar.')
    except AnalysisError as error:st.error(str(error))
