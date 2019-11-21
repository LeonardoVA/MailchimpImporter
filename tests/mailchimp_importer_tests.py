import unittest
from unittest import mock
from mailchimp_importer import MailchimpImporter

class MailchimpImporterTests(unittest.TestCase):
    """Test class for MailchimImporter"""

    @mock.patch("mailchimp_importer.MailchimpImporter.get_mail_list")
    def test_one_equlas_2(self, patched_get_mail_list):
        # In this exmaple we have 8 lists we want to assert a call is made for each
        # showing that it can deal with multiple companies with a total of 8 lists
        mci = MailchimpImporter("tests/test_company_mail_list_1.json")
        mci.start_import()
        self.assertEqual(patched_get_mail_list.call_count, 8)



if __name__ == "__main__":
    unittest.main()