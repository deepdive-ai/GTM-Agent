"""Versioned local checks of the exact export payload; not legal/platform approval."""
import hashlib
import json
import re
from urllib.parse import urlsplit

VERSION='platform-checks-v2'
GOOGLE_POSTS_POLICY='https://support.google.com/business/answer/7342169?hl=en'
LINKEDIN_POLICY='https://www.linkedin.com/help/linkedin/answer/a528176'
GOOGLE_ACTIONS='https://developers.google.com/my-business/reference/rest/v4/accounts.locations.localPosts'
ACTIONS=('UNCONFIGURED','NONE','CALL','BOOK','LEARN_MORE','ORDER','SHOP','SIGN_UP')

def export_payload(draft):
    settings=draft.get('platform_settings',{})
    gbp=draft.get('format')=='Google Business Profile post'
    # CTA is a separate platform field only after the user explicitly selects a button.
    separate=gbp and settings.get('action') in ACTIONS[2:]
    from draft_display import SECTION_LABELS
    blocks=[];last=None
    for b in draft.get('blocks',[]):
        if separate and b['kind']=='cta':continue
        section=b.get('section')
        if section in SECTION_LABELS and section!=last:blocks.append(SECTION_LABELS[section])
        blocks.append(b['text']);last=section
    text='\n\n'.join([draft.get('headline','')]+blocks)
    action=None
    if separate:
        action={'type':settings['action']}
        if settings['action']=='CALL':action['uses_verified_profile_number']=settings.get('phone_verified') is True
        else:action['url']=settings.get('url','').strip()
    return {'text':text,'action':action,'post_type':settings.get('post_type','UPDATE') if gbp else None}

def assess_platform(draft):
    payload=export_payload(draft);text=payload['text'];fmt=draft.get('format');settings=draft.get('platform_settings',{})
    errors=[];flags=[];warnings=[]
    count=len(text);utf16=len(text.encode('utf-16-le'))//2
    limit=None;basis=None
    if fmt=='LinkedIn post':
        limit=3000;basis='Published LinkedIn post limit'
        if max(count,utf16)>limit:errors.append('LinkedIn post exceeds 3,000 characters including headline, spaces, line breaks and CTA. Shorten and recheck the draft.')
        if utf16!=count:warnings.append('Emoji/non-BMP characters are counted conservatively as UTF-16 units; confirm the destination composer count.')
    elif fmt=='Google Business Profile post':
        limit=1500;basis='Conservative application cap; current official numeric limit not verified'
        warnings.append('1,500 characters is an application cap, not a verified current Google rule. Check the destination composer before posting.')
        if max(count,utf16)>limit:errors.append('GBP copy exceeds this app’s 1,500-character cap.')
        if settings.get('post_type','UPDATE')!='UPDATE':errors.append('Only GBP Update posts are supported. Offer/Event fields are not implemented.')
        action=settings.get('action','UNCONFIGURED')
        if action not in ACTIONS or action=='UNCONFIGURED':errors.append('Choose a GBP action button or explicitly choose NONE.')
        if action=='CALL' and settings.get('phone_verified') is not True:errors.append('Confirm that the Business Profile phone number is verified before using Call now.')
        if action in ACTIONS[3:]:
            try:
                value=settings.get('url','').strip();parsed=urlsplit(value)
                valid=parsed.scheme in ('https','http') and bool(parsed.hostname) and not parsed.username and not parsed.password and not re.search(r'\s',value)
            except ValueError:valid=False
            if not valid:errors.append('Enter a valid HTTP(S) destination URL without embedded credentials for the GBP action button.')
        if re.search(r'(?:\+?\d[\d ()-]{6,}\d)|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|(?<!\w)@[\w.]+',text):flags.append('Contact information appears in the post text. Verify its connection to this Business Profile or use a verified action button.')
        sensitive=r'\b(scleral[\s-]+lens(?:es)?|contact lenses|medical devices?|prescription drugs?|pharmaceutical|tobacco|cigarettes?|vaping|cannabis|alcohol|gambling|firearms?|weapons?|fireworks?|financial services|adult services)\b'
        if re.search(sensitive,text,re.I):flags.append('Potential regulated-product content: manual platform-policy review required. This keyword flag is a conservative interpretation, not a Google rejection.')
        if re.search(r'\bscleral[\s-]+lens(?:es)?\b',text,re.I):flags.append('Scleral-lens GBP content is withheld pending platform-policy review.')
    elif fmt=='Blog':warnings.append('No universal blog character limit is applied. Validate headings, links, media and metadata against the chosen CMS before publishing.')
    else:errors.append('Unsupported content format.')
    if re.search(r'<\s*/?\s*[a-zA-Z][^>]*>|\*\*[^*]+\*\*|(?m:^#{1,6} )',text):warnings.append('Markup detected. This export is plain text; inspect its appearance in the destination.')
    status='withheld' if flags else 'blocked' if errors else 'checks_passed'
    reason=' '.join(flags+errors) if flags or errors else 'Implemented checks passed; platform policy and publication approval still require human review.'
    return {'version':VERSION,'status':status,'reason':reason,'errors':errors,'policy_flags':flags,'warnings':warnings,'characters':count,'utf16_units':utf16,'limit':limit,'limit_basis':basis,'checked_on':'2026-10-06','policy_url':GOOGLE_POSTS_POLICY if fmt=='Google Business Profile post' else LINKEDIN_POLICY if fmt=='LinkedIn post' else None,'payload':payload,'payload_hash':hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest(),'limitations':'Text-only checks. Keyword flags are incomplete, primarily English, and can overflag. Images, videos, legal compliance, destination availability and account eligibility are not verified.'}

def platform_blocked(draft):return assess_platform(draft)['status'] in ('blocked','withheld')
