import io
import json
import unittest
from copy import deepcopy
from analyzer import AnalysisError, fingerprint
from listener import demo
from planner import prepare_sources, recommend, validate_plan, plan_fingerprint

class PlannerTests(unittest.TestCase):
    def setUp(self):
        self.report=demo()
        self.analysis={'report_fingerprint':fingerprint(self.report),'themes':[{'title':'Cost','evidence_ids':['demo-0']}]}
        self.docs=[{'name':'clinic.md','text':'Lens pricing depends on the fitting assessment.'}]
        self.sources=prepare_sources(self.docs)
        self.brief={'business':'Clinic','audience':'Patients','goal':'Appointments'}
        self.raw={'topics':[{'title':'Understanding lens pricing','theme_index':0,'audience_ids':['demo-0'],'rationale':'One sample comment asks about price.','format':'Blog','statements':[{'text':'Pricing depends on the fitting assessment.','citations':[{'source_id':'source-1','excerpt':self.docs[0]['text']}]}],'missing_evidence':['What is the approved consultation fee?']}]}
    def test_fabricated_excerpt_and_source_rejected(self):
        for replacement in ({'source_id':'source-1','excerpt':'It costs 45000.'},{'source_id':'invented','excerpt':self.docs[0]['text']}):
            raw=deepcopy(self.raw); raw['topics'][0]['statements'][0]['citations']=[replacement]
            with self.assertRaises(AnalysisError): validate_plan(raw,self.report,self.analysis,self.sources)
    def test_audience_evidence_must_belong_to_theme(self):
        self.raw['topics'][0]['audience_ids']=['demo-1']
        with self.assertRaises(AnalysisError): validate_plan(self.raw,self.report,self.analysis,self.sources)
    def test_missing_evidence_must_be_explicit(self):
        topic=self.raw['topics'][0]; topic['statements']=[]
        self.assertEqual(validate_plan(self.raw,self.report,self.analysis,self.sources)[0]['status'],'Needs source evidence')
        topic['missing_evidence']=[]
        with self.assertRaises(AnalysisError): validate_plan(self.raw,self.report,self.analysis,self.sources)
    def test_stale_analysis_and_changed_sources(self):
        first=plan_fingerprint(self.report,self.analysis,self.sources,self.brief)
        changed=prepare_sources([{'name':'clinic.md','text':'New approved information.'}])
        self.assertNotEqual(first,plan_fingerprint(self.report,self.analysis,changed,self.brief))
        self.analysis['report_fingerprint']='stale'
        with self.assertRaises(AnalysisError): recommend(self.report,self.analysis,self.docs,self.brief,'secret')
    def test_transport_and_key_handling(self):
        def transport(req,timeout):
            self.assertNotIn('secret',req.full_url)
            body=json.loads(req.data)
            data=json.loads(body['contents'][0]['parts'][0]['text'])
            if data.get('task')=='check_question_scope':
                return io.BytesIO(json.dumps({'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':json.dumps({'in_scope':True,'reason':'Directly addresses lens pricing.'})}]}}]}).encode())
            self.assertIn('only authority',body['systemInstruction']['parts'][0]['text'])
            data=json.loads(body['contents'][0]['parts'][0]['text'])
            self.assertEqual(data['research_question'],'lens pricing')
            self.assertTrue(data['sources'][0]['id'].startswith('passage-'))
            raw=deepcopy(self.raw); raw['topics'][0]['statements'][0]['citations'][0]['source_id']=data['sources'][0]['id']
            return io.BytesIO(json.dumps({'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':json.dumps(raw)}]}}]}).encode())
        result=recommend(self.report,self.analysis,self.docs,self.brief,'secret',transport=transport,retrieval_query='lens pricing')
        self.assertNotIn('secret',json.dumps(result))
        self.assertEqual(len(result['topics']),1)
        self.assertTrue(result['synthetic'])
    def test_source_limits(self):
        with self.assertRaises(AnalysisError): prepare_sources([])
        with self.assertRaises(AnalysisError): prepare_sources([{'name':'large.txt','text':'a'*100001}])
    def test_ui_renders_planner(self):
        from pathlib import Path
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file(str(Path(__file__).with_name('app.py'))).run()
        next(b for b in app.button if b.label=='Explore synthetic demo').click().run()
        self.assertFalse(app.exception)
        self.assertTrue(next(b for b in app.button if b.label=='Generate source-grounded topics').disabled)
