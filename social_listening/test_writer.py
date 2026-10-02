import io
import json
import unittest
from copy import deepcopy
from analyzer import AnalysisError
from writer import prepare_statements, validate_draft, write_content, plain_text, draft_fingerprint

class WriterTests(unittest.TestCase):
    def setUp(self):
        self.sources=[{'id':'source-1','name':'care.md','text':'Follow-up examinations help assess changes.'}]
        self.topic={'title':'Monitoring','statements':[{'text':'Follow-up examinations help assess changes.','citations':[{'source_id':'source-1','excerpt':self.sources[0]['text']}]}],'missing_evidence':['What is the clinic follow-up schedule?']}
        self.brief={'business':'Clinic','call_to_action':'Call to book an appointment','source_review_status':'Draft material; review pending'}
        self.statements=prepare_statements(self.topic,[0],self.sources)
        self.raw={'headline':'Understanding follow-up','blocks':[{'kind':'factual','text':self.statements[0]['text'],'statement_ids':['statement-1']},{'kind':'cta','text':self.brief['call_to_action'],'statement_ids':[]}],'review_notes':['Clinic follow-up intervals are unknown. Source review pending.']}
    def test_missing_and_invented_statement_references_rejected(self):
        for refs in ([],['invented']):
            raw=deepcopy(self.raw); raw['blocks'][0]['statement_ids']=refs
            with self.assertRaises(AnalysisError): validate_draft(raw,self.statements,self.brief)
    def test_cta_cannot_be_changed_or_omitted(self):
        raw=deepcopy(self.raw); raw['blocks'][-1]['text']='Call another number'
        with self.assertRaises(AnalysisError): validate_draft(raw,self.statements,self.brief)
        raw=deepcopy(self.raw); raw['blocks'].pop()
        with self.assertRaises(AnalysisError): validate_draft(raw,self.statements,self.brief)
    def test_source_gap_and_fabricated_excerpt(self):
        with self.assertRaises(AnalysisError): prepare_statements(self.topic,[],self.sources)
        self.topic['statements'][0]['citations'][0]['excerpt']='Invented care protocol'
        with self.assertRaises(AnalysisError): prepare_statements(self.topic,[0],self.sources)
    def test_transport_and_review_status_retained(self):
        def transport(req,timeout):
            self.assertNotIn('secret',req.full_url)
            body=json.loads(req.data)
            data=json.loads(body['contents'][0]['parts'][0]['text'])
            self.assertEqual(data['unresolved_questions'],self.topic['missing_evidence'])
            return io.BytesIO(json.dumps({'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':json.dumps(self.raw)}]}}]}).encode())
        draft=write_content(self.topic,self.sources,[0],self.brief,'Understanding follow-up','LinkedIn post','','secret',transport=transport)
        self.assertEqual(draft['brief']['source_review_status'],'Draft material; review pending')
        self.assertNotIn('secret',json.dumps(draft))
        self.assertTrue(plain_text(draft).endswith(self.brief['call_to_action']))
    def test_input_edits_change_fingerprint(self):
        first=draft_fingerprint(self.topic,self.statements,self.brief,'Title','Blog','')
        second=draft_fingerprint(self.topic,self.statements,self.brief,'Revised title','Blog','')
        self.assertNotEqual(first,second)
    def test_em_dash_in_generated_text_rejected(self):
        self.raw['headline']='Care — follow-up'
        with self.assertRaises(AnalysisError): validate_draft(self.raw,self.statements,self.brief)

    def test_uncited_editorial_claim_rejected(self):
        self.raw['blocks'].insert(0,{'kind':'editorial','text':'Our clinic offers expert procedures.','statement_ids':[]})
        with self.assertRaises(AnalysisError): validate_draft(self.raw,self.statements,self.brief)
