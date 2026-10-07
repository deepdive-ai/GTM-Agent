import io
import json
import unittest
from copy import deepcopy
from unittest.mock import patch
from pathlib import Path
from analyzer import AnalysisError
from planner import validate_plan, resolve_citation_locations
from workflow import plan_workflow
from campaign import create_package, export_package, package_markdown, decide, package_fingerprint, retry_format

class CampaignTests(unittest.TestCase):
    def setUp(self):
        self.report={'input_mode':'direct','query':'User-selected topic','videos':[],'comments':[],'synthetic':False}
        self.analysis={'themes':[],'comments':[]}
        self.docs=[{'name':'software.md','text':'Tasks can be exported as CSV from the Tasks menu.'}]
        self.sources=[dict(self.docs[0],id='source-1')]
        self.topic={'title':'Export tasks as CSV','theme_index':-1,'audience_ids':[],'rationale':'User-selected topic.','format':'Blog','statements':[{'text':self.docs[0]['text'],'citations':[{'source_id':'source-1','excerpt':self.docs[0]['text']}]}],'missing_evidence':[]}
        self.brief={'business':'TaskNest','audience':'Project managers','goal':'Explain CSV export','call_to_action':'Explore the demo','source_review_status':'Synthetic test material','platform_settings':{'action':'NONE','post_type':'UPDATE'}}
        self.calls=[]
    def transport(self,req,timeout):
        data=json.loads(json.loads(req.data)['contents'][0]['parts'][0]['text']);self.calls.append(data)
        if data.get('task')=='check_question_scope':raw={'in_scope':True,'reason':'CSV export only.'}
        elif data.get('task')=='claim_support_review':
            raw={'units':[{'unit_id':u['id'],'reviewed_text':u['text'],'verdict':'not_factual' if u['kind']=='headline' else 'supported','reason':'Matches source.','evidence_ids':[u['evidence'][0]['id']]} for u in data['units']]}
        elif 'reviewed_title' in data:
            raw={'headline':'Export tasks','blocks':[{'kind':'factual','text':self.docs[0]['text'],'statement_ids':['statement-1']},{'kind':'cta','text':self.brief['call_to_action'],'statement_ids':[]}],'review_notes':['Synthetic software example.']}
        else:
            raw={'topics':[deepcopy(self.topic)]};raw['topics'][0]['statements'][0]['citations'][0]['source_id']=data['sources'][0]['id']
        if data.get('research_question'):
            if data.get('task')=='claim_support_review':raw['scope_review']={'answers_question':True,'advice_separated':True,'reason':'Answers export question without extra advice.'}
            elif 'reviewed_title' in data:
                for b in raw['blocks']:b['section']='cta' if b['kind']=='cta' else 'answer'
        return io.BytesIO(json.dumps({'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':json.dumps(raw)}]}}]}).encode())
    def package(self,formats=None):
        return create_package(self.topic,self.sources,[0],self.brief,'Export tasks',formats or ['LinkedIn post','Blog','Google Business Profile post'],'','test-secret',transport=self.transport)
    def test_direct_plan_no_audience_analysis_or_fabrication(self):
        plan=plan_workflow(self.report,self.analysis,self.docs,self.brief,'test-secret',retrieval_query='export tasks CSV',transport=self.transport)
        self.assertEqual(plan['input_mode'],'direct');self.assertEqual(plan['topics'][0]['audience_ids'],[])
        self.assertIn('no audience research',plan['topics'][0]['rationale'])
        self.assertEqual(len(self.calls),2)
    def test_direct_plan_rejects_fabricated_audience_evidence(self):
        raw={'topics':[deepcopy(self.topic)]};raw['topics'][0]['audience_ids']=['fake']
        with self.assertRaises(AnalysisError):validate_plan(raw,self.report,self.analysis,self.sources)
    def test_three_formats_independently_pause_and_export(self):
        package=self.package();export=export_package(package)
        self.assertEqual(len(self.calls),6)
        self.assertEqual(len(export['items']),3)
        self.assertTrue(all(i['status']=='awaiting_user_review' for i in export['items'].values()))
        self.assertNotIn('test-secret',json.dumps(export))
        for name in package['formats']:self.assertIn('## '+name,package_markdown(package))
    def test_approval_is_per_format(self):
        p=self.package();decide(p,'Blog',True)
        self.assertEqual(export_package(p)['status'],'review_required')
        self.assertEqual(p['items']['LinkedIn post']['result']['status'],'awaiting_user_review')
        decide(p,'LinkedIn post',True);decide(p,'Google Business Profile post',True)
        self.assertEqual(export_package(p)['status'],'accepted');self.assertEqual(len(self.calls),6)
    def test_rejected_format_not_in_markdown(self):
        p=self.package();p['items']['Blog']['result']['draft']['headline']='REJECTED CONTENT'
        decide(p,'Blog',False)
        self.assertEqual(export_package(p)['status'],'incomplete');self.assertNotIn('REJECTED CONTENT',package_markdown(p))
    def test_one_failure_does_not_discard_other_results(self):
        from workflow import start_content_workflow
        def start(*args,**kwargs):
            if args[5]=='Blog':raise AnalysisError('Test failure')
            return start_content_workflow(*args,**kwargs)
        with patch('campaign.start_content_workflow',side_effect=start):p=self.package()
        self.assertEqual(export_package(p)['status'],'incomplete')
        self.assertEqual(p['items']['Blog']['result']['status'],'blocked')
        self.assertEqual(p['items']['LinkedIn post']['result']['status'],'awaiting_user_review')
    def test_bad_formats_and_sources_block_before_calls(self):
        for formats in (['Email'],['Blog','Blog']):
            with self.assertRaises(AnalysisError):self.package(formats)
        self.topic['statements'][0]['citations'][0]['excerpt']='Invented'
        with self.assertRaises(AnalysisError):self.package()
        self.assertEqual(self.calls,[])
    def test_changed_brief_invalidates_package(self):
        p=self.package(['Blog']);changed=dict(self.brief,call_to_action='Different CTA')
        self.assertNotEqual(p['input_fingerprint'],package_fingerprint(self.topic,self.sources,[0],changed,'Export tasks',['Blog'],'','gemini-2.5-flash'))
    def test_direct_ui_works_without_saved_run_or_key(self):
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file(str(Path(__file__).with_name('app.py'))).run()
        app.radio[0].set_value('I already have a topic').run()
        self.assertFalse(app.exception)
        self.assertTrue(any(t.label=='Business or product' for t in app.text_input))
        self.assertFalse(any(b.label=='Analyze audience signals' for b in app.button))
        self.assertTrue(next(b for b in app.button if b.label=='Generate source-grounded topics').disabled)

    def test_direct_ui_package_and_stale_input_invalidation(self):
        from streamlit.testing.v1 import AppTest
        upload=io.BytesIO(self.docs[0]['text'].encode());upload.name='software.md'
        with patch('streamlit.file_uploader',return_value=[upload]),patch('urllib.request.urlopen',side_effect=self.transport):
            app=AppTest.from_file(str(Path(__file__).with_name('app.py'))).run()
            app.radio[0].set_value('I already have a topic').run()
            values={'Gemini API key (session only)':'test-secret','Business or product':'TaskNest','Target audience':'Project managers','Campaign goal':'Explain export','Call to action (optional)':'Explore the demo','Research question (use the language of your documents)':'export tasks CSV'}
            for widget in app.text_input:
                if widget.label in values:widget.set_value(values[widget.label])
            app.run()
            next(c for c in app.checkbox if c.label.startswith('I reviewed the retrieved')).check().run()
            next(b for b in app.button if b.label=='Generate source-grounded topics').click().run()
            self.assertFalse(app.exception)
            next(c for c in app.checkbox if c.label.startswith('I reviewed the selected')).check().run()
            next(b for b in app.button if b.label=='Generate campaign package').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(len(app.tabs),3)
            next(w for w in app.selectbox if w.label=='GBP action button').set_value('NONE').run()
            next(b for b in app.button if b.label=='Accept Blog').click().run()
            self.assertEqual(app.session_state['campaign_package']['items']['Blog']['result']['status'],'user_accepted')
            import tempfile
            with tempfile.TemporaryDirectory() as folder,patch.dict('os.environ',{'GTM_CAMPAIGN_DB':str(Path(folder)/'campaigns.sqlite')}):
                app.run()
                next(t for t in app.text_input if t.label=='Campaign name').set_value('Round trip').run()
                next(b for b in app.button if b.label=='Save campaign').click().run()
                self.assertFalse(app.exception)
                calls_before=len(self.calls)
                # Fresh session: no file upload and no key. Restore the actual saved workspace.
                with patch('streamlit.file_uploader',return_value=[]):
                    reopened=AppTest.from_file(str(Path(__file__).with_name('app.py'))).run()
                    next(b for b in reopened.button if b.label=='Open campaign').click().run()
                    self.assertFalse(reopened.exception)
                    self.assertEqual(reopened.session_state['campaign_package']['items']['Blog']['result']['status'],'user_accepted')
                    next(b for b in reopened.button if b.label=='Accept LinkedIn post').click().run()
                    self.assertFalse(reopened.exception)
                    self.assertEqual(reopened.session_state['campaign_package']['items']['LinkedIn post']['result']['status'],'user_accepted')
                    self.assertEqual(len(self.calls),calls_before)
            next(t for t in app.text_input if t.label=='Reviewed topic title').set_value('New scope').run()
            self.assertFalse(app.exception)
            self.assertNotIn('campaign_package',app.session_state)

    def test_quote_location_correction_requires_unique_same_document_match(self):
        sources=[{'id':'a','document_id':'doc','text':'partial quote'}, {'id':'b','document_id':'doc','text':'Exact complete quote.'}]
        raw={'topics':[{'statements':[{'citations':[{'source_id':'a','excerpt':'Exact complete quote.'}]}]}]}
        fixed,log=resolve_citation_locations(raw,sources)
        self.assertEqual(fixed['topics'][0]['statements'][0]['citations'][0]['source_id'],'b')
        self.assertEqual(log[0]['original_source_id'],'a')
        self.assertEqual(raw['topics'][0]['statements'][0]['citations'][0]['source_id'],'a')
        for extra in ([dict(sources[1],id='c')],):
            fixed,log=resolve_citation_locations(raw,sources+extra);self.assertFalse(log)
        sources[1]['document_id']='other'
        self.assertFalse(resolve_citation_locations(raw,sources)[1])
        raw['topics'][0]['statements'][0]['citations'][0]['excerpt']='Invented quotation'
        self.assertFalse(resolve_citation_locations(raw,sources)[1])

    def test_retry_only_failed_format_retains_previous_audit(self):
        p=self.package();decide(p,'Blog',False)
        other=p['items']['LinkedIn post']['result']
        before=len(self.calls);retry_format(p,'Blog','test-secret',transport=self.transport)
        self.assertEqual(len(self.calls)-before,2)
        self.assertIs(p['items']['LinkedIn post']['result'],other)
        self.assertEqual(p['items']['Blog']['result']['status'],'awaiting_user_review')
        self.assertEqual(export_package(p)['items']['Blog']['previous_runs'][0]['status'],'user_rejected')
        with self.assertRaises(AnalysisError):retry_format(p,'LinkedIn post','test-secret',transport=self.transport)

if __name__=='__main__':unittest.main()
