"""Shared draft presentation; notices are review metadata, not generated claims."""
SECTION_LABELS={'answer':'Answer to your question','additional_advice':'Additional advice'}

def review_notice(draft):
    status=draft.get('brief',{}).get('source_review_status','')
    if status!='Approved by the business':
        return 'Sample draft. Source review pending. Medical content also requires clinical approval. Not approved for publication.'
    return 'Draft for review. Business source approval is not publication approval or clinical approval for medical content.'

def display_blocks(draft):
    last=None
    for block in draft.get('blocks',[]):
        section=block.get('section')
        if section in SECTION_LABELS and section!=last:
            yield 'heading',SECTION_LABELS[section]
        if block['kind']=='cta':yield 'notice',review_notice(draft)
        yield 'text',block['text']
        last=section
