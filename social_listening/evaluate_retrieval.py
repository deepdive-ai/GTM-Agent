"""Reproducible retrieval evaluation; never calls a model or tests factual correctness."""
import argparse
import json
from pathlib import Path
from planner import prepare_sources
from retriever import retrieve


def evaluate(source_dir,mode="bm25",held_out=False):
    medical = prepare_sources([{'name':p.name,'text':p.read_text()} for p in sorted(Path(source_dir).glob('*.md'))])
    # Synthetic fixtures: no real company's product claims.
    software = prepare_sources([
        {'name':'export.md','text':'Synthetic test company: TaskNest. Workspace owners can export tasks as CSV from Settings > Export. Export includes task titles, due dates and completion status. Attachments are not included.'},
        {'name':'billing.md','text':'Synthetic test company: TaskNest. Billing administrators can switch from monthly to annual billing at renewal. No price or discount is supplied in this fixture.'},
        {'name':'access.md','text':'Synthetic test company: TaskNest. Administrators invite team members by email. Members can edit assigned tasks; only administrators can delete a workspace.'},
    ])
    cases = [
        ('medical','Why do scleral lenses need replacement?', 'scleral_lens_replacement_reasons.md'),
        ('medical','When should I change my lenses?', 'scleral_lens_lifespan_and_review.md'),
        ('medical','How long will my lenses last?', 'scleral_lens_lifespan_and_review.md'),
        ('medical','What is the expected lifespan of scleral lenses?', 'scleral_lens_lifespan_and_review.md'),
        ('medical','Are deposits and cracks reasons to replace a lens?', 'scleral_lens_replacement_reasons.md'),
        ('medical','How much does Nexus charge for scleral lenses?', None),
        ('medical','What is the Nexus lens warranty?', None),
        ('medical','orchid irrigation', None),
        ('software','How do I export tasks as CSV?', 'export.md'),
        ('software','Can I download my work as a spreadsheet?', 'export.md'),
        ('software','How can I pay yearly instead of every month?', 'billing.md'),
        ('software','How do I invite team members?', 'access.md'),
        ('software','How much is the annual plan?', None),
        ('software','Does TaskNest offer a refund?', None),
        ('software','scleral lens replacement', None),
    ]
    if held_out:
        cases=[
            ('software','Can I take a copy of my task list into Excel?', 'export.md'),
            ('software','Will the downloaded task file contain attachments?', 'export.md'),
            ('software','Who is allowed to erase the entire workspace?', 'access.md'),
            ('software','When can our account move to a yearly payment schedule?', 'billing.md'),
            ('medical','My contacts keep moving and are harder to take out. Who should I tell?', 'scleral_lens_lifespan_and_review.md'),
            ('medical','Can daily handling wear out a scleral lens surface?', 'scleral_lens_surface_wear.md'),
            ('software','What refund amount does TaskNest promise?', None),
            ('software','banana bread baking temperature', None),
            ('medical','How do I export tasks as CSV?', None),
        ]
    results=[]
    for campaign,query,expected in cases:
        r=retrieve(medical if campaign=='medical' else software,query,mode=mode)
        names=list(dict.fromkeys(p['name'] for p in r['passages']))
        results.append({'campaign':campaign,'query':query,'expected_document':expected,'expected_answer_available':expected is not None,'retrieved_documents':names,'expected_rank':names.index(expected)+1 if expected in names else None,'assessment':('found' if expected in names else 'missed') if expected else ('no_matches' if not names else 'background_matches_only_missing_answer'),'retrieval':r})
    answerable=[r for r in results if r['expected_answer_available']]
    return {'method':mode,'held_out':held_out,'scope':'Small hand-labelled retrieval evaluation; software documents are synthetic. No live model calls. Missing-answer labels are evaluator judgments, not automated abstention results. Rank is by first occurrence of a document among up to six returned passages.','cases':results,'answerable_cases':len(answerable),'answerable_found_in_top_6_passages':sum(r['expected_rank'] is not None for r in answerable),'answerable_ranked_first':sum(r['expected_rank']==1 for r in answerable),'synthetic_software_sources':software}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source_dir');p.add_argument('output');p.add_argument('--mode',choices=['bm25','hybrid'],default='bm25');p.add_argument('--held-out',action='store_true');a=p.parse_args()
    result=evaluate(a.source_dir,a.mode,a.held_out);Path(a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k not in ('cases','synthetic_software_sources','scope')}))
    for r in result['cases']:print(r['assessment'],r['expected_rank'],r['query'])
