import tempfile
import unittest
from pathlib import Path
from listener import CollectionError, collect, connect, demo, previous_ids, save, themes

class Tests(unittest.TestCase):
    def test_duplicates_and_boundaries(self):
        def c(i,t): return {'id':str(i),'video_id':str(i),'text':t}
        groups,unmatched=themes([c(1,'cost?'),c(2,' COST? '),c(3,'costume')],{'price':['cost']})
        self.assertEqual(groups[0]['count'],1)
        self.assertEqual(unmatched,1)
    def test_disabled_comments_and_provenance(self):
        def fetch(endpoint,key,**kwargs):
            if endpoint=='search': return {'items':[{'id':{'videoId':'a'}},{'id':{'videoId':'b'}}]}
            if endpoint=='videos': return {'items':[{'id':v,'snippet':{'title':'Title','channelTitle':'Channel','publishedAt':'2026-01-01'}} for v in ['a','b']]}
            if kwargs['videoId']=='b': raise CollectionError('403: commentsDisabled')
            return {'items':[{'snippet':{'topLevelComment':{'id':'c','snippet':{'textDisplay':'Cost?','publishedAt':'2026-01-02','likeCount':2}}}}]}
        result=collect('secret','topic',fetch=fetch)
        self.assertEqual(len(result['warnings']),1)
        self.assertIn('&lc=c',result['comments'][0]['url'])
        self.assertNotIn('secret',str(result))
    def test_quota_failure_not_hidden(self):
        def fetch(*args,**kwargs): raise CollectionError('403: quotaExceeded')
        with self.assertRaises(CollectionError): collect('secret','topic',fetch=fetch)
    def test_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            with connect(Path(tmp)/'test.sqlite') as db:
                report=demo(); save(db,report)
                self.assertEqual(len(previous_ids(db,report['query'])),6)
                self.assertEqual(previous_ids(db,'different topic'),set())
    def test_dashboard_demo(self):
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file(str(Path(__file__).with_name('app.py'))).run()
        self.assertFalse(app.exception)
        next(b for b in app.button if b.label=='Explore synthetic demo').click().run()
        self.assertFalse(app.exception)
        self.assertTrue(any('SYNTHETIC' in w.value for w in app.warning))
        self.assertEqual(app.metric[1].value,'6')

if __name__=='__main__': unittest.main()
