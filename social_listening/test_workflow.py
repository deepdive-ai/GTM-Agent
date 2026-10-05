import io
import json
import unittest
from copy import deepcopy
from unittest.mock import patch
from analyzer import AnalysisError
from claim_review import review_units, validate_review, check_claims
from workflow import start_content_workflow, workflow_export, plan_workflow
from langgraph.types import Command

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.sources=[{'id':'source-1','name':'manual.md','text':'Tasks can be exported as CSV from the Tasks menu.'}]
        self.topic={'title':'Exporting tasks','statements':[{'text':self.sources[0]['text'],'citations':[{'source_id':'source-1','excerpt':self.sources[0]['text']}]}]}
        self.brief={'business':'Example','call_to_action':'Try the demo','source_review_status':'Draft material; review pending'}
        self.raw={'headline':'How to export tasks','blocks':[{'kind':'factual','text':self.sources[0]['text'],'statement_ids':['statement-1']},{'kind':'cta','text':'Try the demo','statement_ids':[]}],'review_notes':['Test material; review pending.']}
        self.draft=dict(deepcopy(self.raw),sources=self.sources,brief=self.brief,statements=[dict(self.topic['statements'][0],id='statement-1')])
        self.calls=[]
    def rows(self,units,bad=False):
        return {'units':[{'unit_id':u['id'],'reviewed_text':u['text'],'verdict':'unsupported' if bad and u['kind']=='body' else 'supported','reason':'Unsupported extra promise.' if bad else 'Matches supplied excerpt.','evidence_ids':[u['evidence'][0]['id']]} for u in units]}
    def transport(self,bad_reviews=0,broken=False):
        def send(req,timeout):
            data=json.loads(json.loads(req.data)['contents'][0]['parts'][0]['text']);self.calls.append(data)
            if data.get('task')=='claim_support_review':
                if broken:raise OSError('network down')
                count=sum(x.get('task')=='claim_support_review' for x in self.calls)
                raw=self.rows(data['units'],count<=bad_reviews)
            else:raw=self.raw
            return io.BytesIO(json.dumps({'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':json.dumps(raw)}]}}]}).encode())
        return send
    def start(self,**kwargs):
        return start_content_workflow(self.topic,self.sources,[0],self.brief,'Exporting tasks','Blog','','secret-key',transport=self.transport(**kwargs))
    def test_pause_then_accept_without_model_call(self):
        graph,config,result=self.start()
        self.assertEqual(result['status'],'awaiting_user_review');self.assertIn('__interrupt__',result)
        self.assertEqual(len(self.calls),2)
        accepted=graph.invoke(Command(resume=True),config)
        self.assertEqual(accepted['status'],'user_accepted');self.assertEqual(len(self.calls),2)
        self.assertNotIn('secret-key',json.dumps(workflow_export(accepted)))
        self.assertNotIn('secret-key',str(graph.get_state(config).values))
    def test_reject_without_model_call(self):
        graph,config,result=self.start()
        self.assertEqual(graph.invoke(Command(resume=False),config)['status'],'user_rejected')
        self.assertEqual(len(self.calls),2)
    def test_failed_claim_causes_revision_and_preserves_original(self):
        graph,config,result=self.start(bad_reviews=1)
        self.assertEqual(result['status'],'awaiting_user_review');self.assertEqual(result['attempts'],2)
        self.assertFalse(result['history'][0]['review']['passed']);self.assertTrue(result['history'][1]['review']['passed'])
        self.assertIn('Unsupported extra promise',self.calls[2]['editor_notes'])
    def test_persistent_failure_stops_at_two_revisions(self):
        graph,config,result=self.start(bad_reviews=99)
        self.assertEqual(result['status'],'blocked');self.assertEqual(result['attempts'],3)
        self.assertEqual(len(self.calls),6);self.assertNotIn('__interrupt__',result)
    def test_review_connection_error_blocks(self):
        graph,config,result=self.start(broken=True)
        self.assertEqual(result['status'],'blocked');self.assertEqual(len(self.calls),2)
        self.assertIn('review_error',result['history'][0])
    def test_incomplete_altered_duplicate_and_unknown_reviews_rejected(self):
        units=review_units(self.draft);good=self.rows(units)
        bads=[]
        bad=deepcopy(good);bad['units'].pop();bads.append(bad)
        bad=deepcopy(good);bad['units'][1]=deepcopy(bad['units'][0]);bads.append(bad)
        for field,value in [('reviewed_text','Different sentence'),('verdict','approved'),('verdict','not_factual'),('evidence_ids',['invented']),('evidence_ids',[])]:
            bad=deepcopy(good);bad['units'][1][field]=value;bads.append(bad)
        for bad in bads:
            with self.subTest(bad=bad),self.assertRaises(AnalysisError):validate_review(bad,units,self.draft)
    def test_uncertain_review_does_not_pass(self):
        units=review_units(self.draft);raw=self.rows(units);raw['units'][1]['verdict']='uncertain'
        self.assertFalse(validate_review(raw,units,self.draft)['passed'])
    def test_fabricated_excerpt_fails_before_network(self):
        draft=deepcopy(self.draft);draft['statements'][0]['citations'][0]['excerpt']='Invented evidence'
        with self.assertRaises(AnalysisError):check_claims(draft,'secret-key',transport=self.transport())
        self.assertEqual(self.calls,[])
    def test_all_sentences_reviewed_cta_excluded(self):
        self.draft['blocks'][0]['text']+=' Exports always finish instantly.'
        units=review_units(self.draft)
        self.assertEqual(len(units),3);self.assertIn('instantly',units[-1]['text'])
        self.assertFalse(any(u['text']=='Try the demo' for u in units))
    def test_invalid_writer_output_cannot_reach_review(self):
        self.raw['blocks'][0]['statement_ids']=['invented']
        graph,config,result=self.start()
        self.assertEqual(result['status'],'blocked');self.assertEqual(len(self.calls),3)
    def test_planning_no_hits_never_calls_model(self):
        with patch('workflow.recommend') as generate:
            with self.assertRaises(AnalysisError):plan_workflow({}, {},[{'name':'manual.md','text':self.sources[0]['text']}],self.brief,'secret-key',retrieval_query='keratoconus')
            generate.assert_not_called()

    def test_structural_failure_revised_before_claim_review(self):
        normal=self.transport();count=[0]
        def transport(req,timeout):
            count[0]+=1
            if count[0]==1:
                raw=deepcopy(self.raw);raw['blocks'][0]['statement_ids']=[]
                return io.BytesIO(json.dumps({'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':json.dumps(raw)}]}}]}).encode())
            return normal(req,timeout)
        graph,config,result=start_content_workflow(self.topic,self.sources,[0],self.brief,'Exporting tasks','Blog','','secret-key',transport=transport)
        self.assertEqual(result['status'],'awaiting_user_review')
        self.assertEqual(result['attempts'],2)
        self.assertIn('rejected_draft',result['history'][0])
        self.assertTrue(result['history'][1]['review']['passed'])
        self.assertEqual(count[0],3)

if __name__=='__main__':unittest.main()
