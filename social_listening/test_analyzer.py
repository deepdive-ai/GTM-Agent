import io,json,unittest
from copy import deepcopy
from analyzer import analyze,validate,AnalysisError
from listener import demo

class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.report=demo()
        self.raw={'comments':[{'id':c['id'],'relevance':'relevant' if i==0 else 'uncertain','language':'English','interpretation':c['text'],'reason':'Sample classification'} for i,c in enumerate(self.report['comments'])],'themes':[{'title':'Cost','interpretation':'A cost question','suggestion':'Explain pricing','evidence_needed':'Approved pricing','evidence_ids':['demo-0']}]}
    def test_counts_computed_and_unknown_ids_rejected(self):
        r=validate(self.raw,self.report)
        self.assertEqual(r['themes'][0]['comment_count'],1)
        self.raw['themes'][0]['evidence_ids']=['invented']
        with self.assertRaises(AnalysisError): validate(self.raw,self.report)
    def test_missing_classification_rejected(self):
        self.raw['comments'].pop()
        with self.assertRaises(AnalysisError): validate(self.raw,self.report)
    def test_uncertain_evidence_rejected(self):
        self.raw['themes'][0]['evidence_ids']=['demo-1']
        with self.assertRaises(AnalysisError): validate(self.raw,self.report)
    def test_transport_and_export(self):
        def transport(req,timeout):
            self.assertNotIn('secret',req.full_url)
            body=json.loads(req.data)
            self.assertIn('Hindi',body['systemInstruction']['parts'][0]['text'])
            return io.BytesIO(json.dumps({'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':json.dumps(self.raw)}]}}]}).encode())
        result=analyze(self.report,'secret',transport=transport)
        self.assertEqual(result['model'],'gemini-2.5-flash')
        self.assertNotIn('secret',json.dumps(result))
    def test_ui_analysis(self):
        from unittest.mock import patch
        from pathlib import Path
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file(str(Path(__file__).with_name('app.py'))).run()
        next(b for b in app.button if b.label=='Explore synthetic demo').click().run()
        next(t for t in app.text_input if t.label=='Gemini API key (session only)').set_value('test-key').run()
        result=validate(self.raw,self.report)
        from analyzer import fingerprint
        result.update(report_fingerprint=fingerprint(app.session_state.report),model='mock-model',analyzed_at='test')
        with patch('analyzer.analyze',return_value=result):
            next(b for b in app.button if b.label=='Analyze audience signals').click().run()
        self.assertFalse(app.exception)
        self.assertIn('analysis',app.session_state)
        self.assertTrue(any('Explain pricing' in m.value for m in app.markdown))
