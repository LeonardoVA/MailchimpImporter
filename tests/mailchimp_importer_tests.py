"""Module for testing the mailchimp importer"""
import unittest
from unittest import mock
from mailchimp_importer import MailchimpImporter


class MailchimpImporterTests(unittest.TestCase):
    """Test class for MailchimpImporter"""
    # def __init__(self):
    #
    #     super(unittest.TestCase, self).__init__(*args, **kwargs)
    #
    #     self.mci = None

    def setUp(self):
        self.mci = MailchimpImporter("tests/test_company_mail_list_1.json")

    @mock.patch("mailchimp_importer.MailchimpImporter.get_mail_list")
    def test_correct_amounts_of_calls_to_get_list(self, patched_get_mail_list):
        """In this exmaple we have 8 lists we want to assert a call is made for each
        showing that it can deal with multiple companies with a total of 8 lists"""
        self.mci.start_import()
        self.assertEqual(patched_get_mail_list.call_count, 8)

    def test_transform_data_working(self):
        """We want to test we get the expected output from input when transforming"""
        json_test_data = {"members":
                              [{"id": "4",
                               "merge_fields": {"FNAME": "bob",
                                                "LNAME": "smith"},
                               "email_address": "big.bob@mail.com",
                               "status": "subscribed"}]
                          }

        json_expected_output = [{"id": "4",
                                "firstname": "bob",
                                "lastname": "smith",
                                "email": "big.bob@mail.com",
                                "status": "subscribed"}]

        mock_response_to_transform = mock.MagicMock()
        mock_response_to_transform.json.return_value = json_test_data

        return_value = self.mci.process_request_data(mock_response_to_transform)
        self.assertEqual(return_value, json_expected_output)




if __name__ == "__main__":
    unittest.main()
