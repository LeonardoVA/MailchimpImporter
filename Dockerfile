FROM python:3.7-alpine

RUN mkdir /mailchimp_importer/
RUN mkdir /mailchimp_importer/company_mail_lists/

WORKDIR /mailchimp_importer/

COPY mailchimp_importer.py  requirements.txt /mailchimp_importer/

# Right now we just copy the config file in but we would read this in from S3
COPY company_mail_lists/company_mail_list_1.json company_mail_lists/

RUN pip3 install -r requirements.txt

ENTRYPOINT ["python","-u", "mailchimp_importer.py"]

