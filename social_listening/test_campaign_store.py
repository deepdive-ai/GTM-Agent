import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from analyzer import AnalysisError
import test_campaign
from campaign import decide, resume_format_review
from campaign_store import capture, restore, pack_package, unpack_package, save_campaign, load_campaign

class StoreTests(unittest.TestCase):
    def setUp(self):
        self.f=test_campaign.CampaignTests();self.f.setUp()
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.db=Path(self.temp.name)/'campaigns.sqlite'
    def snapshot(self,p):
        brief=dict(self.f.brief,formats=['Blog'])
        return capture({'campaign_package':p,'gemini_key':'NEVER-SAVE','youtube_key':'ALSO-SECRET','entry_mode':'I already have a topic'},self.f.docs,self.f.report,self.f.analysis,None,{},'gemini-2.5-flash',brief,'bm25')
    def test_save_load_and_approval_without_model_or_credentials(self):
        p=self.f.package(['Blog']);snap=self.snapshot(p)
        row=save_campaign(self.db,'Example',snap)
        loaded=load_campaign(self.db,row['id']);state={}
        restore(state,loaded['snapshot'])
        self.assertNotIn('NEVER-SAVE',self.db.read_bytes().decode(errors='ignore'))
        self.assertNotIn('ALSO-SECRET',json.dumps(loaded))
        self.assertEqual(state['saved_campaign_documents'],self.f.docs)
        with patch('urllib.request.urlopen',side_effect=AssertionError('Unexpected API request')):
            decide(state['campaign_package'],'Blog',True)
        self.assertEqual(state['campaign_package']['items']['Blog']['result']['status'],'user_accepted')
        self.assertEqual(self.db.stat().st_mode & 0o777,0o600)
    def test_resume_review_reuses_draft_and_attempt_count(self):
        with patch('workflow.check_claims',side_effect=AnalysisError('Quota exhausted')):
            p=self.f.package(['Blog'])
        before=copy.deepcopy(p['items']['Blog']['result']['draft']);n=len(self.f.calls)
        p=unpack_package(json.loads(json.dumps(pack_package(p))))
        resume_format_review(p,'Blog','new-key',transport=self.f.transport)
        result=p['items']['Blog']['result']
        self.assertEqual(len(self.f.calls)-n,1)
        self.assertEqual(self.f.calls[-1]['task'],'claim_support_review')
        self.assertEqual(result['draft']['blocks'],before['blocks'])
        self.assertEqual(result['attempts'],1)
        self.assertEqual(len(result['history']),2)
        self.assertEqual(result['status'],'awaiting_user_review')
    def test_changed_draft_cannot_reuse_passing_review(self):
        p=unpack_package(pack_package(self.f.package(['Blog'])))
        p['items']['Blog']['result']['draft']['blocks'][0]['text']='Invented claim.'
        with self.assertRaises(AnalysisError):decide(p,'Blog',True)
    def test_concurrent_save_prevents_overwrite(self):
        snap=self.snapshot(self.f.package(['Blog']));row=save_campaign(self.db,'One',snap)
        save_campaign(self.db,'Two',snap,row['id'],row['revision'])
        with self.assertRaises(AnalysisError):save_campaign(self.db,'Stale',snap,row['id'],row['revision'])
        self.assertEqual(load_campaign(self.db,row['id'])['name'],'Two')
    def test_fresh_app_reopens_sources_without_key(self):
        from streamlit.testing.v1 import AppTest
        snap=self.snapshot(None)
        save_campaign(self.db,'Saved example',snap)
        with patch.dict('os.environ',{'GTM_CAMPAIGN_DB':str(self.db)}),patch('urllib.request.urlopen',side_effect=AssertionError('No API calls')):
            app=AppTest.from_file(str(Path(__file__).with_name('app.py'))).run()
            next(b for b in app.button if b.label=='Open campaign').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state['saved_campaign_documents'],self.f.docs)
            self.assertEqual(app.session_state['entry_mode'],'I already have a topic')
            self.assertEqual(app.session_state['gemini_key'],'')
            self.assertTrue(next(b for b in app.button if b.label=='Generate source-grounded topics').disabled)
            next(t for t in app.text_input if t.label=='Gemini API key (session only)').set_value('session-only-test-key').run()
            next(b for b in app.button if b.label=='Open campaign').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state['gemini_key'],'session-only-test-key')
            self.assertNotIn('session-only-test-key',self.db.read_bytes().decode(errors='ignore'))

if __name__=='__main__':unittest.main()
