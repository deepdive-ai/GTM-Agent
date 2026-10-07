"""Multiple independently reviewed formats from one approved topic and brief."""
import hashlib
import json
from analyzer import AnalysisError
from writer import FORMATS, prepare_statements, plain_text
from workflow import start_content_workflow, workflow_export, restore_content_workflow
from langgraph.types import Command
from platform_policy import assess_platform

VERSION='campaign-package-v1'

def package_fingerprint(topic,sources,selected,brief,title,formats,notes,model):
    return hashlib.sha256(json.dumps([VERSION,topic,sources,selected,brief,title,formats,notes,model],sort_keys=True).encode()).hexdigest()

def create_package(topic,sources,selected,brief,title,formats,notes,key,model='gemini-2.5-flash',transport=None,progress=None):
    if not formats or len(formats)!=len(set(formats)) or any(f not in FORMATS for f in formats):
        raise AnalysisError('Select one or more supported campaign formats.')
    prepare_statements(topic,selected,sources)
    package={'input_fingerprint':package_fingerprint(topic,sources,selected,brief,title,formats,notes,model),'formats':list(formats),'items':{},'request':{'topic':topic,'sources':sources,'selected':selected,'brief':brief,'title':title,'notes':notes,'model':model}}
    for i,format_name in enumerate(formats):
        if progress:progress(i,len(formats),format_name)
        try:
            graph,config,result=start_content_workflow(topic,sources,selected,brief,title,format_name,notes,key,model,transport)
            package['items'][format_name]={'graph':graph,'config':config,'result':result}
        except AnalysisError as error:
            package['items'][format_name]={'result':{'status':'blocked','attempts':0,'history':[],'error':str(error)}}
    return package

def retry_format(package,format_name,key,transport=None):
    if format_name not in package['items']:raise AnalysisError('Unknown campaign format.')
    previous=package['items'][format_name]
    if previous['result']['status'] not in ('blocked','user_rejected'):raise AnalysisError('Only blocked or rejected formats can be retried.')
    request=package['request']
    history=previous.get('previous_runs',[])+[workflow_export(previous['result'])]
    try:
        graph,config,result=start_content_workflow(request['topic'],request['sources'],request['selected'],request['brief'],request['title'],format_name,request['notes'],key,request['model'],transport)
        replacement={'graph':graph,'config':config,'result':result}
    except AnalysisError as error:
        replacement={'result':{'status':'blocked','attempts':0,'history':[],'error':str(error)}}
    replacement['previous_runs']=history
    package['items'][format_name]=replacement

def decide(package,format_name,accept,key="",transport=None):
    if type(accept) is not bool:raise AnalysisError('Choose accept or reject.')
    item=package['items'][format_name]
    if accept and assess_platform(item['result'].get('draft') or {})['status'] in ('blocked','withheld'):raise AnalysisError('This format is withheld pending platform-policy review.')
    if item['result']['status']!='awaiting_user_review':raise AnalysisError('This draft is not waiting for review.')
    if 'graph' not in item:
        graph,config,result=restore_content_workflow(package['request'],format_name,item['result'],key,transport)
        item.update(graph=graph,config=config,result=result)
    item['result']=item['graph'].invoke(Command(resume=accept,update={'draft':item['result']['draft']} if accept else {}),item['config'])

def export_package(package):
    items={name:dict(workflow_export(item['result']),previous_runs=item.get('previous_runs',[])) for name,item in package['items'].items()}
    for item in items.values():item['platform_review']=assess_platform(item.get('draft') or {})
    statuses=[item['status'] for item in items.values()]
    state='accepted' if statuses and all(s=='user_accepted' for s in statuses) else 'review_required'
    if any(s in ('blocked','user_rejected') for s in statuses):state='incomplete'
    if any(i.get('draft') and i['platform_review']['status'] in ('blocked','withheld') for i in items.values()):state='platform_review_required'
    return {'version':VERSION,'input_fingerprint':package['input_fingerprint'],'status':state,'formats':package['formats'],'items':items,'notice':'Source-support checks are model-assisted. User acceptance is not clinical approval or publication.'}

def package_markdown(package):
    export=export_package(package)
    lines=['# Campaign package', 'Status: '+export['status'],export['notice']]
    for name,item in export['items'].items():
        lines.extend(['## '+name,'Status: '+item['status']])
        if item['status'] not in ('awaiting_user_review','user_accepted'):
            lines.append('No accepted or reviewable draft. '+item.get('error',''));continue
        if item['platform_review']['status'] in ('blocked','withheld'):
            lines.extend([item['platform_review']['reason'],str(item['platform_review'].get('policy_url') or ''),'Draft text is retained only in the audit for inspection.']);continue
        d=item['draft']
        from draft_display import review_notice
        if d.get('research_question'):lines.append('Original question: '+d['research_question'])
        text=item['platform_review']['payload']['text']
        cta=d.get('brief',{}).get('call_to_action','')
        if cta and text.endswith(cta):text=text[:-len(cta)]+review_notice(d)+'\n\n'+cta
        else:lines.append(review_notice(d))
        lines.append(text)
        action=item['platform_review']['payload']['action']
        if action:lines.extend(['### Separate action button',json.dumps(action,ensure_ascii=False)])
        lines.append('### Source references')
        source_lookup={source['id']:source for source in d['sources']}
        for statement in d['statements']:
            lines.append(statement['id']+': '+statement['text'])
            for citation in statement['citations']:
                source=source_lookup[citation['source_id']]
                lines.append(source['name']+' ('+citation['source_id']+'): '+citation['excerpt'])
                lines.extend(source.get('source_urls',[]))
        lines.append('### Review notes');lines.extend(d['review_notes'])
    return '\n\n'.join(lines)+'\n'


def resume_format_review(package,format_name,key,transport=None):
    item=package['items'][format_name]
    graph,config,result=restore_content_workflow(package['request'],format_name,item['result'],key,transport,resume_review=True)
    item.update(graph=graph,config=config,result=result)
