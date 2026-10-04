import io
import json
import unittest
from unittest.mock import patch
from analyzer import AnalysisError, fingerprint
from listener import demo
from planner import prepare_sources, recommend, plan_fingerprint
from retriever import retrieve

class HybridTests(unittest.TestCase):
    def setUp(self):
        self.sources=prepare_sources([{'name':'export.md','text':'Export tasks as CSV.'},{'name':'clinic.md','text':'Scleral lens care.'}])
    def test_semantic_paraphrase_without_keyword_overlap(self):
        with patch('semantic_retriever.semantic_candidates',return_value={0:0.7}):
            r=retrieve(self.sources,'Download a spreadsheet',mode='hybrid')
        self.assertEqual([p['name'] for p in r['passages']],['export.md'])
        self.assertEqual(r['passages'][0]['semantic_rank'],1)
        self.assertNotIn('keyword_rank',r['passages'][0])
    def test_no_candidates_does_not_fabricate_matches(self):
        with patch('semantic_retriever.semantic_candidates',return_value={}):
            self.assertEqual(retrieve(self.sources,'orchid irrigation',mode='hybrid')['passages'],[])
    def test_fusion_retains_offsets_and_current_campaign(self):
        with patch('semantic_retriever.semantic_candidates',return_value={0:0.8}):
            r=retrieve(self.sources[:1],'export',mode='hybrid')
        p=r['passages'][0]
        self.assertEqual(p['text'],self.sources[0]['text'][p['start']:p['end']])
        self.assertEqual(p['keyword_rank'],1)
        self.assertNotIn('clinic',json.dumps(r))
    def test_backend_failure_does_not_silently_fallback(self):
        with patch('semantic_retriever.semantic_candidates',side_effect=AnalysisError('model unavailable')):
            with self.assertRaisesRegex(AnalysisError,'model unavailable'):retrieve(self.sources,'export',mode='hybrid')
    def test_mode_changes_invalidate_approval(self):
        args=(demo(),{},self.sources,{},'export')
        self.assertNotEqual(plan_fingerprint(*args,'bm25'),plan_fingerprint(*args,'hybrid'))

class ScopeTests(unittest.TestCase):
    def setUp(self):
        self.report=demo()
        self.analysis={'report_fingerprint':fingerprint(self.report),'themes':[{'title':'Pricing','evidence_ids':['demo-0']}]}
        self.docs=[{'name':'lens.md','text':'Lens care requires regular review. No clinic price or warranty is supplied.'}]
        self.brief={'business':'Clinic','audience':'Patients','goal':'Education'}
    def run_plan(self,scope,alternatives=False):
        self.calls=[]
        def transport(req,timeout):
            data=json.loads(json.loads(req.data)['contents'][0]['parts'][0]['text']);self.calls.append(data)
            if data.get('task')=='check_question_scope': raw=scope
            else:
                topic={'title':'Lens price and warranty','theme_index':0,'audience_ids':['demo-0'],'rationale':'Audience asks about price.','format':'Blog','statements':[],'missing_evidence':['Provide approved clinic prices and warranty.']}
                raw={'topics':[topic,dict(topic,title='Lens care')] if alternatives else [topic]}
            return io.BytesIO(json.dumps({'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':json.dumps(raw)}]}}]}).encode())
        return recommend(self.report,self.analysis,self.docs,self.brief,'test',transport=transport,retrieval_query='Lens price and warranty')
    def test_multiple_topics_rejected_before_review(self):
        with self.assertRaisesRegex(AnalysisError,'proposed alternatives'):self.run_plan({},alternatives=True)
        self.assertEqual(len(self.calls),1)
    def test_scope_drift_is_rejected(self):
        with self.assertRaisesRegex(AnalysisError,'Topic scope check failed'):self.run_plan({'in_scope':False,'reason':'Substitutes lens care for pricing.'})
    def test_invalid_scope_verdict_fails_closed(self):
        with self.assertRaisesRegex(AnalysisError,'invalid result'):self.run_plan({'in_scope':'true','reason':'Wrong type'})
    def test_focused_missing_evidence_is_accepted_without_statements(self):
        r=self.run_plan({'in_scope':True,'reason':'Requests the missing price and warranty.'})
        self.assertEqual(len(self.calls),2)
        self.assertEqual(r['topics'][0]['status'],'Needs source evidence')
        self.assertEqual(r['topics'][0]['statements'],[])
        self.assertEqual(r['research_question'],'Lens price and warranty')
        self.assertTrue(r['scope_review']['in_scope'])
