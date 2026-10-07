import io,json,unittest
from copy import deepcopy
import test_workflow
from workflow import start_content_workflow,restore_content_workflow,workflow_export
from claim_review import content_hash,validate_review,review_units
from writer import validate_sections
from analyzer import AnalysisError
from draft_display import display_blocks
from platform_policy import export_payload

class FeedbackTests(unittest.TestCase):
    def setUp(self):
        f=test_workflow.WorkflowTests();f.setUp();self.f=f
        f.topic['research_question']='How do I export tasks as CSV?'
        for b in f.raw['blocks']:b['section']='cta' if b['kind']=='cta' else 'answer'
    def run_flow(self,failures=0,missing=False,separation=False):
        f=self.f;calls=[];reviews=0
        def send(req,timeout):
            nonlocal reviews
            d=json.loads(json.loads(req.data)['contents'][0]['parts'][0]['text']);calls.append(d)
            self.assertEqual(d['research_question'],f.topic['research_question'])
            if d.get('task')=='claim_support_review':
                reviews+=1;raw=f.rows(d['units'])
                if not missing:raw['scope_review']={'answers_question':True if separation else reviews>failures,'advice_separated':reviews>failures if separation else True,'reason':'Separate advice and remove unrelated content.'}
            else:raw=f.raw
            return io.BytesIO(json.dumps({'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':json.dumps(raw)}]}}]}).encode())
        result=start_content_workflow(f.topic,f.sources,[0],f.brief,'Export tasks','Blog','','test',transport=send)[2]
        return result,calls
    def test_supported_but_off_topic_revises(self):
        r,c=self.run_flow(1)
        self.assertEqual(r['status'],'awaiting_user_review');self.assertEqual(r['attempts'],2)
        self.assertIn('Separate advice',c[2]['editor_notes'])
        self.assertTrue(all(u['verdict']=='supported' for u in r['history'][0]['review']['units']))
    def test_mixed_advice_revises(self):
        r,_=self.run_flow(1,separation=True);self.assertEqual(r['attempts'],2)
    def test_persistent_scope_drift_blocks(self):
        r,_=self.run_flow(99);self.assertEqual(r['status'],'blocked');self.assertEqual(r['attempts'],3)
    def test_missing_scope_verdict_blocks(self):
        r,_=self.run_flow(missing=True);self.assertEqual(r['status'],'blocked')
    def test_question_is_bound_to_review_hash(self):
        r,_=self.run_flow();d=deepcopy(r['draft']);h=content_hash(d)
        d['research_question']='What does this cost?';self.assertNotEqual(h,content_hash(d))
    def test_bad_section_order_rejected(self):
        d=deepcopy(self.f.raw);d['blocks'][0]['section']='additional_advice'
        with self.assertRaises(AnalysisError):validate_sections(d)
    def test_scope_survives_saved_review_restore(self):
        r,_=self.run_flow();f=self.f
        request={'topic':f.topic,'sources':f.sources,'selected':[0],'brief':f.brief,'title':'Export tasks','notes':''}
        restored=restore_content_workflow(request,'Blog',workflow_export(r))[2]
        self.assertEqual(restored['draft']['research_question'],f.topic['research_question'])
        altered=deepcopy(request);altered['topic']['research_question']='Different question'
        with self.assertRaises(AnalysisError):restore_content_workflow(altered,'Blog',workflow_export(r))
    def test_notice_immediately_before_cta_and_export_sections(self):
        d=dict(deepcopy(self.f.raw),brief=self.f.brief)
        d['blocks'].insert(1,{'kind':'factual','section':'additional_advice','text':'Extra supported advice.','statement_ids':['statement-1']})
        rows=list(display_blocks(d));self.assertEqual(rows[-2][0],'notice');self.assertIn('clinical approval',rows[-2][1])
        self.assertEqual(rows[-1][1],'Try the demo')
        text=export_payload(d)['text'];self.assertIn('Additional advice\n\nExtra supported advice.',text)
    def test_starter_sets_question_without_generation(self):
        from streamlit.testing.v1 import AppTest
        from pathlib import Path
        app=AppTest.from_file(str(Path(__file__).with_name('app.py'))).run()
        app.radio[0].set_value('I already have a topic').run()
        next(b for b in app.button if b.label=='When might it need replacement?').click().run()
        self.assertFalse(app.exception)
        self.assertEqual(next(t.value for t in app.text_input if t.label.startswith('Research question')),'When might it need replacement?')
