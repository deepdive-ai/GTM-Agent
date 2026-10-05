import io,json,unittest,urllib.error
from gemini_errors import describe_http_error,probe_quota
class QuotaTests(unittest.TestCase):
    def error(self,metric='',delay='12s',value=None,message=''):
        v={'quotaId':metric}
        if value is not None:v['quotaValue']=value
        p={'error':{'message':message,'details':[{'@type':'type.googleapis.com/google.rpc.QuotaFailure','violations':[v]},{'@type':'type.googleapis.com/google.rpc.RetryInfo','retryDelay':delay}]}}
        return urllib.error.HTTPError('https://example.test',429,'quota',{},io.BytesIO(json.dumps(p).encode()))
    def test_daily_overrides_short_retry_hint(self):
        text=describe_http_error(self.error('GenerateRequestsPerDayPerProjectPerModel'))
        self.assertIn('daily quota exhausted',text);self.assertIn('IST',text);self.assertNotIn('12.0 seconds',text)
    def test_minute_delay(self):
        text=describe_http_error(self.error('GenerateRequestsPerMinutePerProjectPerModel'))
        self.assertIn('per-minute',text);self.assertIn('12.0 seconds',text)
    def test_unknown_not_assumed_daily_and_no_raw_details(self):
        text=describe_http_error(self.error(message='private-project API-key=secret-value'))
        self.assertIn('did not identify',text);self.assertNotIn('secret',text);self.assertNotIn('private-project',text)
    def test_zero_quota_is_not_promised_reset(self):
        self.assertIn('Waiting alone may not restore access',describe_http_error(self.error('PerDay',value='0')))
    def test_invalid_json_does_not_crash(self):
        error=urllib.error.HTTPError('https://example.test',429,'quota',{},io.BytesIO(b'not json'))
        self.assertIn('no reset time',describe_http_error(error))
    def test_probe_small_request_and_error(self):
        def send(req,timeout):
            self.assertNotIn('secret',req.full_url)
            self.assertEqual(json.loads(req.data)['generationConfig']['maxOutputTokens'],8)
            raise self.error('GenerateRequestsPerDay')
        self.assertIn('daily quota exhausted',probe_quota('secret','gemini-2.5-flash',transport=send))
    def test_probe_success_does_not_promise_full_workflow(self):
        text=probe_quota('secret','gemini-2.5-flash',transport=lambda req,timeout:io.BytesIO(b'{}'))
        self.assertIn('may still exceed',text)
