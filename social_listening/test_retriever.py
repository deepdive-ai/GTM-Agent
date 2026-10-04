import io
import json
import unittest
from copy import deepcopy
from analyzer import AnalysisError, fingerprint
from listener import demo
from planner import prepare_sources, recommend, plan_fingerprint, validate_plan
from retriever import retrieve, split_passages, PassageIndex
from writer import write_content

class RetrievalTests(unittest.TestCase):
    def setUp(self):
        self.docs=[{'name':'lenses.md','text':'Scleral lens replacement may be needed for deposit buildup, damage or changes in prescription. Timing varies by patient.\n\nSource: https://example.org/lenses\nStatus: Clinical review pending.'}, {'name':'software.md','text':'Software invoices renew monthly. Enterprise seats are charged annually.'}]
        self.sources=prepare_sources(self.docs)
    def test_relevant_evidence_ranks_first_and_unrelated_is_excluded(self):
        result=retrieve(self.sources,'scleral lens replacement')
        self.assertEqual([p['name'] for p in result['passages']],['lenses.md'])
        self.assertEqual(result['indexed_documents'],2)
    def test_no_matches_and_stopwords_do_not_return_arbitrary_passages(self):
        for query in ('orchid irrigation','what is it'):
            self.assertEqual(retrieve(self.sources,query)['passages'],[])
    def test_original_offsets_metadata_and_overlap(self):
        text=('Lens replacement depends on deposits and damage. Timing varies by patient.\n\n'*60)+'Source: https://example.org/source\nStatus: Clinical review pending.'
        source=prepare_sources([{'name':'long.md','text':text}])[0]
        chunks=split_passages(source)
        self.assertGreater(len(chunks),3)
        covered=set()
        for p in chunks:
            self.assertEqual(p['text'],text[p['start']:p['end']])
            self.assertLessEqual(len(p['text']),1000)
            self.assertEqual(p['source_urls'],['https://example.org/source'])
            self.assertTrue(p['review_metadata'])
            covered.update(range(p['start'],p['end']))
        self.assertTrue(all(i in covered for i,c in enumerate(text) if not c.isspace()))
        self.assertLess(chunks[1]['start'],chunks[0]['end'])
    def test_changed_documents_cannot_reuse_old_ids_or_corpus(self):
        a=retrieve(self.sources,'replacement')
        changed=prepare_sources([dict(self.docs[0],text=self.docs[0]['text']+' New guidance.')])
        b=retrieve(changed,'replacement')
        self.assertNotEqual(a['corpus_fingerprint'],b['corpus_fingerprint'])
        self.assertNotEqual(a['passages'][0]['id'],b['passages'][0]['id'])
    def test_other_campaign_content_does_not_leak(self):
        retrieve(self.sources,'replacement')
        other=prepare_sources([self.docs[1]])
        self.assertEqual(retrieve(other,'scleral replacement')['passages'],[])
    def test_long_documents_are_bounded_and_qualifications_visible(self):
        source=prepare_sources([{'name':'long.md','text':('Unrelated invoice billing subscription.\n\n'*150)+'Lens replacement timing is individual, not a universal deadline.\n\n'+('Software release deployment.\n\n'*100)}])
        result=retrieve(source,'replacement timing',top_k=2)
        self.assertIn('not a universal deadline',result['passages'][0]['text'])
        self.assertLess(sum(len(p['text']) for p in result['passages']),len(source[0]['text']))
    def test_keyword_match_does_not_claim_sufficiency(self):
        r=retrieve(self.sources,'scleral lens warranty')
        self.assertTrue(r['passages'])
        self.assertIn('warranty',r['unmatched_query_terms'])
        self.assertIn('Candidate',r['status'])
    def test_query_changes_invalidate_topic_brief(self):
        r=demo();self.assertNotEqual(plan_fingerprint(r,{},self.sources,{},'replacement'),plan_fingerprint(r,{},self.sources,{},'price'))
    def test_limits(self):
        for query in ('','a'*1501):
            with self.assertRaises(AnalysisError):retrieve(self.sources,query)
        with self.assertRaises(AnalysisError):retrieve(self.sources,'lens',top_k=0)

class RagPipelineTests(unittest.TestCase):
    def setUp(self):
        self.report=demo();self.analysis={'report_fingerprint':fingerprint(self.report),'themes':[{'title':'Replacement','evidence_ids':['demo-0']}]}
        self.docs=[{'name':'care.md','text':'Lens replacement timing varies by patient.'},{'name':'unrelated.md','text':'Invoice billing uses monthly subscriptions.'}]
        self.brief={'business':'Clinic','audience':'Patients','goal':'Education','call_to_action':'Call to book','source_review_status':'Review pending'}
    def response(self,raw):
        return io.BytesIO(json.dumps({'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':json.dumps(raw)}]}}]}).encode())
    def test_no_matches_blocks_api_call(self):
        def forbidden(*args,**kwargs):self.fail('API called without evidence')
        with self.assertRaisesRegex(AnalysisError,'No matching evidence'):
            recommend(self.report,self.analysis,self.docs,self.brief,'test',transport=forbidden,retrieval_query='orchid irrigation')
    def test_only_retrieved_passages_sent_then_writer_keeps_provenance(self):
        def planner_transport(req,timeout):
            payload=json.loads(json.loads(req.data)['contents'][0]['parts'][0]['text'])
            self.assertEqual(len(payload['sources']),1)
            self.assertNotIn('Invoice',json.dumps(payload))
            p=payload['sources'][0]
            return self.response({'topics':[{'title':'Lens replacement','theme_index':0,'audience_ids':['demo-0'],'rationale':'Audience question','format':'Blog','statements':[{'text':p['text'],'citations':[{'source_id':p['id'],'excerpt':p['text']}]}],'missing_evidence':[]}]})
        result=recommend(self.report,self.analysis,self.docs,self.brief,'test',transport=planner_transport,retrieval_query='lens replacement')
        self.assertEqual(result['retrieval']['indexed_documents'],2)
        def writer_transport(req,timeout):
            payload=json.loads(json.loads(req.data)['contents'][0]['parts'][0]['text'])
            st=payload['statements'][0]
            return self.response({'headline':'Lens replacement','blocks':[{'kind':'factual','text':st['text'],'statement_ids':[st['id']]},{'kind':'cta','text':'Call to book','statement_ids':[]}],'review_notes':['Review pending']})
        draft=write_content(result['topics'][0],result['sources'],[0],self.brief,'Lens replacement','Blog','','test',transport=writer_transport)
        self.assertEqual(draft['sources'][0]['name'],'care.md')
        self.assertEqual(draft['sources'][0]['start'],0)
        self.assertEqual(draft['statements'][0]['citations'][0]['source_id'],draft['sources'][0]['id'])
    def test_unretrieved_citation_rejected_even_if_real_in_other_document(self):
        def transport(req,timeout):
            return self.response({'topics':[{'title':'Replacement','theme_index':0,'audience_ids':['demo-0'],'rationale':'Question','format':'Blog','statements':[{'text':'Monthly invoices','citations':[{'source_id':'source-2','excerpt':self.docs[1]['text']}]}],'missing_evidence':[]}]})
        with self.assertRaisesRegex(AnalysisError,'citation checks'):
            recommend(self.report,self.analysis,self.docs,self.brief,'test',transport=transport,retrieval_query='replacement')
    def test_missing_answer_can_be_flagged_despite_keyword_matches(self):
        def transport(req,timeout):
            return self.response({'topics':[{'title':'Lens warranty','theme_index':0,'audience_ids':['demo-0'],'rationale':'Question','format':'Blog','statements':[],'missing_evidence':['Provide the approved lens warranty.']}]})
        result=recommend(self.report,self.analysis,self.docs,self.brief,'test',transport=transport,retrieval_query='lens warranty')
        self.assertEqual(result['topics'][0]['status'],'Needs source evidence')
