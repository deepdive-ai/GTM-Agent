import json
import os
from pathlib import Path
import streamlit as st
from analyzer import AnalysisError, analyze, fingerprint
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
with st.expander('Basic keyword comparison (not AI analysis)'):
    st.write([{'theme':g['theme'],'keyword_matches':g['count']} for g in groups])
    st.caption(str(unmatched)+' distinct texts did not match a configured keyword.')
with st.expander('All collected comments and video context'):
    st.json({'videos':report['videos'],'comments':report['comments']})
export=dict(report,keyword_candidates=groups,ai_analysis=analysis)
st.download_button('Download evidence report (JSON)',json.dumps(export,indent=2),file_name='audience-evidence.json',mime='application/json')
st.caption('API keys are not saved. Local snapshots expire on app access after 29 days. Delete exported reports separately when no longer needed. Analysis is sent to Gemini only when you click Analyze. AI results are held in this session and included in your download; they are not saved to collection history. No content is published.')
