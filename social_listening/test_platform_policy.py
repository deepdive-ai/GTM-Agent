import unittest
import test_campaign
from analyzer import AnalysisError
from campaign import export_package,package_markdown,decide
from platform_policy import assess_platform

class PlatformPolicyTests(unittest.TestCase):
    def test_narrow_rule_does_not_claim_other_formats_are_compliant(self):
        for fmt in ['Blog','LinkedIn post']:
            self.assertEqual(assess_platform({'format':fmt,'headline':'Scleral lenses','blocks':[]})['status'],'checks_passed')
        self.assertEqual(assess_platform({'format':'Google Business Profile post','headline':'Clinic opening hours','blocks':[]})['status'],'blocked')
    def test_withheld_format_cannot_be_accepted_or_exported_as_campaign_copy(self):
        f=test_campaign.CampaignTests();f.setUp();p=f.package()
        d=p['items']['Google Business Profile post']['result']['draft'];d['headline']='Scleral lens lifespan'
        audit=export_package(p)
        self.assertEqual(audit['status'],'platform_review_required')
        self.assertEqual(audit['items']['Google Business Profile post']['platform_review']['status'],'withheld')
        self.assertTrue(audit['items']['Google Business Profile post']['draft']['claim_review']['passed'])
        self.assertEqual(d['headline'],audit['items']['Google Business Profile post']['draft']['headline'])
        self.assertNotIn('Scleral lens lifespan',package_markdown(p))
        self.assertIn('Export tasks',package_markdown(p))
        with self.assertRaises(AnalysisError):decide(p,'Google Business Profile post',True)
    def test_case_hyphen_and_plural_match(self):
        for text in ['SCLERAL LENSES','scleral-lens','scleral lens replacement']:
            self.assertEqual(assess_platform({'format':'Google Business Profile post','headline':'Update','blocks':[{'text':text}]})['status'],'withheld')

class PlatformChecksTests(unittest.TestCase):
    def draft(self,fmt='LinkedIn post',body='x'):
        return {'format':fmt,'headline':'H','blocks':[{'kind':'factual','text':body,'statement_ids':['s1']}],'platform_settings':{}}
    def test_linkedin_exact_boundary_includes_headline_and_breaks(self):
        d=self.draft(body='x'*2997)
        self.assertEqual(assess_platform(d)['status'],'checks_passed')
        d['blocks'][0]['text']+='x'
        self.assertEqual(assess_platform(d)['status'],'blocked')
    def test_emoji_conservative_count_and_cta(self):
        d=self.draft(body='😀'*1499)
        self.assertEqual(assess_platform(d)['characters'],1502)
        self.assertEqual(assess_platform(d)['status'],'blocked')
        d=self.draft(body='x'*2997);d['blocks'].append({'kind':'cta','text':'Go','statement_ids':[]})
        self.assertEqual(assess_platform(d)['status'],'blocked')
    def test_gbp_call_is_separate_and_requires_confirmation(self):
        d=self.draft('Google Business Profile post','Our office opens at 9 AM.')
        d['blocks'].append({'kind':'cta','text':'Call +91 8247710054 to book','statement_ids':[]})
        d['platform_settings']={'action':'CALL'}
        r=assess_platform(d);self.assertEqual(r['status'],'blocked');self.assertNotIn('8247710054',r['payload']['text'])
        d['platform_settings']['phone_verified']=True
        self.assertEqual(assess_platform(d)['status'],'checks_passed')
        self.assertEqual(d['blocks'][-1]['text'],'Call +91 8247710054 to book')
    def test_gbp_destination_and_unsupported_post_type(self):
        d=self.draft('Google Business Profile post');d['platform_settings']={'action':'BOOK','url':'javascript:alert(1)'}
        self.assertEqual(assess_platform(d)['status'],'blocked')
        d['platform_settings']['url']='https://example.com/book';self.assertEqual(assess_platform(d)['status'],'checks_passed')
        d['platform_settings']['post_type']='OFFER';self.assertEqual(assess_platform(d)['status'],'blocked')
    def test_old_saved_draft_is_rechecked_not_trusted(self):
        d=self.draft('Google Business Profile post');d['platform_review']={'status':'checks_passed'}
        self.assertEqual(assess_platform(d)['status'],'blocked')
        d['platform_settings']={'action':'NONE'};d['blocks'][0]['text']='New prescription drugs available.'
        self.assertEqual(assess_platform(d)['status'],'withheld')
    def test_changed_gbp_settings_reach_approval_graph(self):
        f=test_campaign.CampaignTests();f.setUp();p=f.package(['Google Business Profile post'])
        d=p['items']['Google Business Profile post']['result']['draft'];d['platform_settings']={'action':'CALL','phone_verified':True}
        decide(p,'Google Business Profile post',True)
        self.assertEqual(p['items']['Google Business Profile post']['result']['draft']['platform_settings']['action'],'CALL')
        self.assertEqual(p['items']['Google Business Profile post']['result']['status'],'user_accepted')

if __name__=='__main__':unittest.main()

