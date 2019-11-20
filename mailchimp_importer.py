"""Contains MailchimpImporter class"""
import pprint
import json
import requests

class MailchimpImporter:
    """class handles making requests to retreive mailchimp data for multiple
    companies possibly with multiple lists (as defined in the config file passed in)"""

    def __init__(self, config_file_path):
        self.config_file_path = config_file_path

    def check_and_process_response(self, response, api_key):
        if response.status_code == 200:
            self.process_request_data(response)
            return True

        print(f"Error making response to url: {response.url} with api key: {api_key}.\n"
              f"See response: {response.status_code} {response.text}")
        return False


    def process_request_data(self, request_response):
        for x, member in enumerate(request_response.json()['members']):
            # Do processing for now just print
            print(f"\nMember number {x}\n")
            pprint.pprint(member)

    def make_request(self, list_id, api_key):
        count = 1000
        mailchimp_partial_response_url = "?"\
                                         "fields=members.email_address,members.id,members.status,members.merge_fields," \
                                         f"total_items&count={count}"
        mailchimp_url = f"https://us9.api.mailchimp.com/3.0/lists/{list_id}/members{mailchimp_partial_response_url}"
        auth_tuple = ("", api_key)

        response = requests.get(mailchimp_url, auth=auth_tuple)

        response_success = self.check_and_process_response(response, api_key)

        # Check if we got all the list entries or there is more to do
        if response_success:

            pprint.pprint(response.json())
            total_items = response.json()['total_items']
            # We just got the first 1000, count will still be 1000
            while count < total_items:
                offset_url = f"&offset={count}"
                response = requests.get(mailchimp_url+offset_url, auth=auth_tuple)
                self.check_and_process_response(response, api_key)
                count += 1000






    def read_company_mail_lists(self):
        """Be wary this method will load the contents of the files in
        the mail list directory into memory"""

        with open(self.config_file_path) as mail_list_json_file:
            mail_list_data = json.load(mail_list_json_file)

        return mail_list_data

    def retreive_contact_data(self, mail_list_data):
        print(mail_list_data)
        for company in mail_list_data['Companys']:
            print(f"Processing lists for company: {company['Name']}")
            for mail_list in company['Mail_Lists']:
                self.make_request(mail_list['list_id'], mail_list['api_key'])


    def start_import(self):
        """"""
        mail_list_data = self.read_company_mail_lists()
        self.retreive_contact_data(mail_list_data)






if __name__ == "__main__":
    default_config_file = "company_mail_lists/company_mail_list_1.json"
    mailchimp_importer = MailchimpImporter(default_config_file)
    mailchimp_importer.start_import()
