"""Read only quota metadata from Google errors; never expose raw responses or credentials."""
import datetime as dt
import json
import re
from zoneinfo import ZoneInfo

def describe_http_error(error):
    code=error.code
    if code!=429:
        return 'Gemini HTTP '+str(code)+'. '+({400:'Check the request and model configuration.',401:'Check API credentials.',403:'Check API permissions.',500:'Google is temporarily unavailable; retry later.',503:'Google is temporarily unavailable; retry later.'}.get(code,'Google could not complete the request.'))
    try:
        payload=json.loads(error.read(65536));body=payload.get('error',{})
        details=body.get('details',[]);identifiers=[];delay=None;zero=False
        for detail in details:
            if not isinstance(detail,dict):continue
            if str(detail.get('@type','')).endswith('QuotaFailure'):
                for violation in detail.get('violations',[]):
                    if not isinstance(violation,dict):continue
                    identifiers.extend(str(violation.get(k,'')) for k in ('quotaMetric','quotaId'))
                    if str(violation.get('quotaValue',''))=='0':zero=True
            if str(detail.get('@type','')).endswith('RetryInfo'):
                value=str(detail.get('retryDelay',''))
                if re.fullmatch(r'\d+(?:\.\d+)?s',value):delay=float(value[:-1])
        # Classify Google's message, but never display it: it may contain project/key data.
        signal=' '.join(identifiers)+' '+str(body.get('message',''))
        daily=bool(re.search(r'per[_ ]?day|perday|daily',signal,re.I))
        minute=bool(re.search(r'per[_ ]?minute|perminute',signal,re.I))
        if delay is None and error.headers:
            header=error.headers.get('Retry-After','')
            if re.fullmatch(r'\d+(?:\.\d+)?',header):delay=float(header)
    except (ValueError,TypeError,AttributeError,OSError):
        daily=minute=zero=False;delay=None
    if zero:
        return 'Gemini HTTP 429: Google reports a quota limit of zero. Waiting alone may not restore access. Check this model’s availability and project quota in Google AI Studio.'
    if daily:
        now=dt.datetime.now(dt.timezone.utc).astimezone(ZoneInfo('America/Los_Angeles'))
        reset=dt.datetime.combine(now.date()+dt.timedelta(days=1),dt.time(),tzinfo=ZoneInfo('America/Los_Angeles')).astimezone(ZoneInfo('Asia/Kolkata'))
        return 'Gemini HTTP 429: daily quota exhausted'+(' (a per-minute limit was also reported)' if minute else '')+'. Google resets daily request quotas at midnight Pacific time. Next reset: '+reset.strftime('%d %B %Y, %I:%M %p IST')+'. Do not keep retrying before the reset; availability afterward still depends on your project quota.'
    if minute:
        return 'Gemini HTTP 429: per-minute request or token limit reached. '+('Google suggests retrying after '+str(round(delay,1))+' seconds. ' if delay is not None else 'Wait for the short rate-limit window to clear before retrying. ')+'Reduce request frequency; the daily quota was not identified as the cause in this response.'
    return 'Gemini HTTP 429: Google did not identify a daily or per-minute limit in usable error details. '+('Suggested retry delay: '+str(round(delay,1))+' seconds. ' if delay is not None else '')+'Check model usage and active limits in Google AI Studio; no reset time can be confirmed.'

def probe_quota(key,model,transport=None):
    import urllib.request
    import urllib.error
    if not re.fullmatch(r'[A-Za-z0-9._-]+',model):return 'Invalid model name.'
    if not key.strip():return 'Enter your Gemini key first.'
    body={'contents':[{'parts':[{'text':'Reply OK.'}]}],'generationConfig':{'maxOutputTokens':8}}
    if model=='gemini-2.5-flash':body['generationConfig']['thinkingConfig']={'thinkingBudget':0}
    req=urllib.request.Request('https://generativelanguage.googleapis.com/v1beta/models/'+model+':generateContent',data=json.dumps(body).encode(),headers={'Content-Type':'application/json','x-goog-api-key':key.strip()},method='POST')
    try:
        with (transport or urllib.request.urlopen)(req,timeout=30) as response:response.read(65536)
        return 'Gemini accepted a small test request. Access is available now, but a full draft or review may still exceed token or rate limits.'
    except urllib.error.HTTPError as error:return describe_http_error(error)
    except (OSError,TimeoutError):return 'The quota test could not connect. No quota diagnosis is available.'
