"""Narrow platform safety hold, not a complete platform-policy validator."""
import re

GOOGLE_POSTS_POLICY='https://support.google.com/business/answer/7342169?hl=en'

def assess_platform(draft):
    text=' '.join([draft.get('headline','')]+[b.get('text','') for b in draft.get('blocks',[])])
    if draft.get('format')=='Google Business Profile post' and re.search(r'\bscleral[\s-]+lens(?:es)?\b',text,re.I):
        return {'status':'withheld','rule':'gbp-scleral-lens-review-v1','checked_on':'2026-10-06','reason':'Withheld from Google Business Profile use pending platform-policy review. Google restricts posts about regulated products, including health and medical devices. Applying that rule to this scleral-lens draft is our conservative interpretation, not a Google rejection. Source-support checks do not establish platform suitability.','policy_url':GOOGLE_POSTS_POLICY}
    return {'status':'not_assessed','reason':'Full platform suitability has not been assessed. This narrow check does not certify compliance.'}
