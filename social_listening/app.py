import json
import os
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent / ".deps"))
import streamlit as st
from analyzer import AnalysisError, analyze, fingerprint
from writer import write_content, prepare_statements, draft_fingerprint, plain_text, FORMATS
from video_research import fetch_transcript, research, research_fingerprint
from planner import recommend, prepare_sources, plan_fingerprint
from retriever import retrieve
from listener import THEMES, CollectionError, collect, connect, demo, previous_ids, save, themes

st.set_page_config(page_title='Audience Listening Lab', page_icon='🔎', layout='wide')
st.title('Audience Listening Lab')
st.write('Explore audience discussions, inspect the evidence, and decide what deserves further research.')
st.caption('YouTube audience research · Gemini interpretation · Source-linked evidence')
root=Path(__file__).parent
with st.sidebar:
    st.header('Research scope')
    query=st.text_input('Topic', 'keratoconus scleral lenses')
    videos=st.slider('Videos per search',1,10,5)
    comments=st.slider('Recent top-level comments per video',10,100,50,10)
    days=st.selectbox('Video publication window (days)',[30,90,365,1095],index=2)
    st.caption('The window filters videos. Comment dates are shown separately. Search favors English; it does not strictly filter language or location.')
    key=st.text_input('YouTube API key (session only)',type='password',value=os.environ.get('YOUTUBE_API_KEY',''))
    gemini_key=st.text_input('Gemini API key (session only)',type='password',value=os.environ.get('GEMINI_API_KEY',''),key='gemini_key')
    model=st.text_input('Gemini model',value='gemini-2.5-flash')
    st.caption('Analyze sends comment text, IDs, video titles and the topic to Google Gemini. Your account quota and pricing apply; free access is not guaranteed.')
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

st.subheader('Topics grounded in your sources')
st.write('Connect audience questions to explanations your business can support.')
uploads=st.file_uploader('Upload source documents (.md or .txt)',type=['md','txt'],accept_multiple_files=True)
st.caption('Use approved material. On Generate, retrieved passages, the campaign brief and relevant comments are sent to Gemini. Documents and topic briefs stay in this session and can be downloaded.')
business=st.text_input('Business or product',key='brief_business')
audience=st.text_input('Target audience',key='brief_audience')
goal=st.text_input('Campaign goal',key='brief_goal')
formats=st.multiselect('Content formats',['LinkedIn post','Blog','Google Business Profile post','Video script','Email'],default=['LinkedIn post','Blog'])
cta=st.text_input('Call to action (optional)',key='brief_cta')
language=st.text_input('Content language',value='English',key='brief_language')
tone=st.text_input('Tone',value='Warm and reassuring',key='brief_tone')
source_status=st.selectbox('Source review status',['Draft material; review pending','Approved by the business'],key='brief_source_status')
brief={'business':business.strip(),'audience':audience.strip(),'goal':goal.strip(),'formats':formats,'call_to_action':cta.strip(),'language':language.strip(),'tone':tone.strip(),'source_review_status':source_status}
documents=[]; sources=[]; source_error=None
try:
    documents=[{'name':f.name,'text':f.getvalue().decode('utf-8')} for f in uploads]
    if documents: sources=prepare_sources(documents)
except (UnicodeDecodeError,AnalysisError) as error:
    source_error='Upload UTF-8 Markdown or plain text.' if isinstance(error,UnicodeDecodeError) else str(error)
    st.error(source_error)
st.subheader('Find evidence for an audience question')
question_choices={'Write my own question': ''}
if analysis:
    supported_ids={eid for group in analysis['themes'] for eid in group['evidence_ids']}
    for comment in analysis.get('comments',[]):
        if comment['id'] in supported_ids:
            question_choices[comment['id']]=comment.get('interpretation','')
comment_text={c['id']:c['text'] for c in report['comments']}
question_choice=st.selectbox('Audience question',list(question_choices),format_func=lambda x:comment_text.get(x,x),key='question_choice_'+report_id[:12])
question_key=report_id[:12]+'_'+question_choice
retrieval_query=st.text_input('Research question (use the language of your documents)',value=question_choices[question_choice],key='research_question_'+question_key).strip()
st.caption('Select an audience comment or enter a question. Its AI interpretation is editable. Evidence search runs locally without an API key.')
retrieval=None
if sources and retrieval_query:
    try:
        retrieval=retrieve(sources,retrieval_query)
        st.caption(str(retrieval['indexed_documents'])+' documents indexed into '+str(retrieval['indexed_passages'])+' passages. Showing '+str(len(retrieval['passages']))+' candidate passages.')
        if not retrieval['passages']:
            st.warning('No matching evidence found. Add relevant sources or revise the question. Content generation is blocked for this search.')
        else:
            st.info('These are keyword matches, not a finding that the question is answered. Check relevance, qualifications and missing details before continuing.')
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
evidence_id=plan_fingerprint(report,analysis,sources,brief,retrieval_query) if sources else 'empty'
evidence_reviewed=st.checkbox('I reviewed the retrieved passages for relevance. Check for missing evidence when proposing the topic.',key='evidence_review_'+evidence_id[:16],disabled=not(retrieval and retrieval['passages']))

planning_analysis=dict(analysis,video_research=video_research) if analysis else None
plan_id=plan_fingerprint(report,planning_analysis,sources,brief,retrieval_query) if planning_analysis and sources else None
if st.session_state.get('topic_brief',{}).get('input_fingerprint')!=plan_id or not evidence_reviewed:
    st.session_state.pop('topic_brief',None)
ready=bool(analysis and analysis['themes'] and sources and business.strip() and audience.strip() and goal.strip() and formats and gemini_key and not source_error and retrieval and retrieval['passages'] and evidence_reviewed)
if st.button('Generate source-grounded topics',type='primary',disabled=not ready):
    try:
        with st.spinner('Connecting audience evidence to your source material...'):
            st.session_state.topic_brief=recommend(report,planning_analysis,documents,brief,gemini_key,model,retrieval_query=retrieval_query)
    except AnalysisError as error: st.error(str(error))
if not ready:
    st.caption('Analyze the audience sample, upload sources, review retrieved evidence, and complete the campaign fields to generate a brief.')
topic_brief=st.session_state.get('topic_brief')
if topic_brief:
    st.info('These are proposed topics and draft statements. Citation checks confirm IDs and exact excerpts; you must review whether each excerpt supports the statement and whether the source is trustworthy.')
    comment_lookup={c['id']:c for c in report['comments']}
    source_lookup={s['id']:s for s in topic_brief['sources']}
    for topic in topic_brief['topics']:
        with st.expander(topic['title'],expanded=True):
            st.caption(topic['status']+' · Suggested format: '+topic['format'])
            st.write('Why this topic: '+topic['rationale'])
            st.write('Audience evidence')
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
else:
    choice=st.selectbox('Topic to review',range(len(topic_brief['topics'])),format_func=lambda i:topic_brief['topics'][i]['title'])
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
    if st.session_state.get('content_draft',{}).get('input_fingerprint')!=draft_id or not reviewed:
        st.session_state.pop('content_draft',None)
    if st.button('Generate complete content draft',type='primary',disabled=not(gemini_key and draft_id and reviewed and reviewed_title.strip())):
        try:
            with st.spinner('Writing from the reviewed statements and source excerpts...'):
                st.session_state.content_draft=write_content(chosen,topic_brief['sources'],selected,topic_brief['brief'],reviewed_title,draft_format,editor_notes,gemini_key,model)
        except AnalysisError as error: st.error(str(error))
    if not chosen['statements']: st.info('This topic has no supported explanation yet. Upload further source material or choose a supported topic.')
    content_draft=st.session_state.get('content_draft')
    if content_draft:
        st.success('Content draft generated. Review the prose and its support before using it.')
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
        st.download_button('Download content draft (TXT)',plain_text(content_draft),file_name='gtm-content-draft.txt',mime='text/plain')
        st.download_button('Download draft with sources (JSON)',json.dumps(content_draft,indent=2,ensure_ascii=False),file_name='gtm-content-draft.json',mime='application/json')

with st.expander('Basic keyword comparison (not AI analysis)'):
    st.write([{'theme':g['theme'],'keyword_matches':g['count']} for g in groups])
    st.caption(str(unmatched)+' distinct texts did not match a configured keyword.')
with st.expander('All collected comments and video context'):
    st.json({'videos':report['videos'],'comments':report['comments']})
export=dict(report,keyword_candidates=groups,ai_analysis=analysis,video_research=video_research,transcripts=transcripts,topic_brief=topic_brief,content_draft=st.session_state.get('content_draft'),retrieval=retrieval)
st.download_button('Download evidence report (JSON)',json.dumps(export,indent=2),file_name='audience-evidence.json',mime='application/json')
st.caption('API keys are not saved. Local snapshots expire on app access after 29 days. Delete exported reports separately when no longer needed. Analysis is sent to Gemini only when you click Analyze. AI results are held in this session and included in your download; they are not saved to collection history. No content is published.')
