import unittest
import test_campaign
from analyzer import AnalysisError
from campaign import export_package,package_markdown,decide
from platform_policy import assess_platform

class PlatformPolicyTests(unittest.TestCase):
    def test_narrow_rule_does_not_claim_other_formats_are_compliant(self):
        for fmt in ['Blog','LinkedIn post']:
            self.assertEqual(assess_platform({'format':fmt,'headline':'Scleral lenses','blocks':[]})['status'],'not_assessed')
        self.assertEqual(assess_platform({'format':'Google Business Profile post','headline':'Clinic opening hours','blocks':[]})['status'],'not_assessed')
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

if __name__=='__main__':unittest.main()
