import io
import json
import unittest
from copy import deepcopy
from types import SimpleNamespace
from analyzer import AnalysisError
from video_research import fetch_transcript, research, validate_research, research_fingerprint

class VideoResearchTests(unittest.TestCase):
    def setUp(self):
        self.report={'query':'lens care','collected_at':'2026-10-02','warnings':[],'videos':[{'id':'hBFQk0CvkIM','title':'Lens care questions','description':'An introduction to lens care.','published_at':'2026-09-01','statistics':{'viewCount':'100'},'url':'https://youtube.com/watch?v=hBFQk0CvkIM'}],'comments':[{'id':'c1','video_id':'hBFQk0CvkIM','text':'How do I clean them?','url':'https://youtube.com/watch?v=hBFQk0CvkIM&lc=c1'}]}
        self.raw={'videos':[{'id':'hBFQk0CvkIM','findings':[{'text':'The title frames the video around lens care questions.','field':'title','excerpt':'Lens care questions'}]}],'opportunities':[{'title':'Cleaning questions','rationale':'One commenter asks about cleaning.','video_ids':['hBFQk0CvkIM'],'comment_ids':['c1'],'source_evidence_needed':'Approved cleaning instructions.'}]}
    def test_no_transcript_no_spoken_claim(self):
        raw=deepcopy(self.raw); raw['videos'][0]['findings'][0]['field']='transcript'
        with self.assertRaises(AnalysisError): validate_research(raw,self.report,{})
    def test_invented_excerpt_and_comment_rejected(self):
        raw=deepcopy(self.raw); raw['videos'][0]['findings'][0]['excerpt']='invented'
        with self.assertRaises(AnalysisError): validate_research(raw,self.report,{})
        self.raw['opportunities'][0]['comment_ids']=['invented']
        with self.assertRaises(AnalysisError): validate_research(self.raw,self.report,{})
    def test_transcript_metadata(self):
        class Result(list): language_code='hi'; is_generated=True
        result=Result([SimpleNamespace(text='Test captions',start=0,duration=3)])
        class API:
            def fetch(self,vid,languages): return result
        output=fetch_transcript('hBFQk0CvkIM',API())
        self.assertEqual(output['language'],'hi'); self.assertTrue(output['auto_generated'])
        self.assertEqual(output['segments'][0]['start'],0)
    def test_failure_no_raw_error_exposure(self):
        class API:
            def fetch(self,*args,**kwargs): raise RuntimeError('secret credentials')
        output=fetch_transcript('hBFQk0CvkIM',API())
        self.assertEqual(output['status'],'unavailable'); self.assertNotIn('secret',json.dumps(output))
    def test_transport_and_stale_input(self):
        def transport(req,timeout):
            self.assertNotIn('secret',req.full_url)
            self.assertEqual(json.loads(req.data)['generationConfig']['thinkingConfig']['thinkingBudget'],0)
            return io.BytesIO(json.dumps({'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':json.dumps(self.raw)}]}}]}).encode())
        result=research(self.report,{},'secret',transport=transport)
        self.assertEqual(len(result['opportunities']),1)
        self.assertNotEqual(result['input_fingerprint'],research_fingerprint(self.report,{'hBFQk0CvkIM':{'status':'unavailable'}}))
    def test_video_ui_and_planner_context(self):
        from pathlib import Path
        from unittest.mock import patch
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file(str(Path(__file__).with_name('app.py'))).run()
        app.session_state.report=self.report
        app.run()
        next(t for t in app.text_input if t.label=='Gemini API key (session only)').set_value('mock-key').run()
        result=dict(self.raw,input_fingerprint=research_fingerprint(self.report,{}))
        with patch('video_research.research',return_value=result):
            next(b for b in app.button if b.label=='Analyze video content and opportunities').click().run()
        self.assertFalse(app.exception)
        self.assertTrue(any('Cleaning questions' in e.label for e in app.expander))

    def test_output_limit_explained(self):
        def transport(req,timeout):
            return io.BytesIO(json.dumps({'candidates':[{'finishReason':'MAX_TOKENS'}]}).encode())
        with self.assertRaisesRegex(AnalysisError,'MAX_TOKENS'):
            research(self.report,{},'secret',transport=transport)

    def test_caption_line_breaks_preserve_original_quote(self):
        transcripts={'hBFQk0CvkIM':{'status':'available','text':'Clean lenses\nwith approved solution.'}}
        finding=self.raw['videos'][0]['findings'][0]
        finding.update(field='transcript',excerpt='Clean lenses with approved solution.')
        validated=validate_research(self.raw,self.report,transcripts)
        self.assertEqual(validated['videos'][0]['findings'][0]['excerpt'],'Clean lenses\nwith approved solution.')
    def test_source_punctuation_is_not_editorial_failure(self):
        self.report['videos'][0]['title']='Lens care — questions'
        finding=self.raw['videos'][0]['findings'][0]
        finding.update(excerpt='Lens care — questions',text='Lens care — topic.')
        result=validate_research(self.raw,self.report,{})
        self.assertIn('—',result['videos'][0]['findings'][0]['excerpt'])
        self.assertNotIn('—',result['videos'][0]['findings'][0]['text'])

    def test_passage_reference_attaches_original_hindi(self):
        transcripts={'hBFQk0CvkIM':{'status':'available','text':'यह मूल पाठ है'}}
        self.raw['videos'][0]['findings']=[{'text':'The speaker describes a topic.','source_id':'hBFQk0CvkIM:transcript:0'}]
        result=validate_research(self.raw,self.report,transcripts)
        self.assertEqual(result['videos'][0]['findings'][0]['excerpt'],'यह मूल पाठ है')
    def test_unknown_passage_rejected(self):
        self.raw['videos'][0]['findings']=[{'text':'Unsupported','source_id':'invented'}]
        with self.assertRaises(AnalysisError): validate_research(self.raw,self.report,{})
