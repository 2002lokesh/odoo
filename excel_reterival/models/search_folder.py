from odoo import models, fields, api
import requests
from io import BytesIO
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from odoo.exceptions import UserError

class CustomSearchFolder(models.Model):
    _name = 'custom.search.folder'
    _description = 'Custom Search Folder'

    folder_name = fields.Char('Folder Name', required=True)
    file_name = fields.Char('File Name', required=True)
    lead_id = fields.Char('Lead ID')  # Assuming this field is needed
    contact_name = fields.Char('Contact Name')  # Add other fields as needed
    company_ids = fields.Char('Company IDs')  # Adjust field types as needed
    title = fields.Char('Title')  # Change to Integer if required
    mobile = fields.Char('Mobile')
    email = fields.Char('Email')
    street = fields.Char('Street')
    street2 = fields.Char('Street 2')
    zip = fields.Char('ZIP')
    state_id = fields.Integer('State ID')  # Update types as necessary
    country_id = fields.Integer('Country ID')
    campaign_id = fields.Integer('Campaign ID')
    source_id = fields.Integer('Source ID')
    city = fields.Char('City')

    @api.model
    def search_folder(self):
        # Authentication and token retrieval
        client_id = '836392f3-067e-4b9a-a30a-8ce01cdb6b3e'
        client_secret = 'RuM8Q~wivKYVfCD-Fnm.4FMP4D7Zm8DIOV_8sah-'
        tenant_id = '1741dc9c-7588-4dd2-a053-570e5674f3b8'
        username = 'lokesh.k@gain-hub.com'
        password = 'Gainloki14@2003'

        # Token endpoint
        token_url = f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token'

        # Parameters for the token request
        data = {
            'grant_type': 'password',
            'client_id': client_id,
            'client_secret': client_secret,
            'scope': 'https://graph.microsoft.com/.default offline_access',
            'username': username,
            'password': password,
        }

        # Make the request to obtain the access token
        token_response = requests.post(token_url, data=data)

        if token_response.status_code == 200:
            tokens = token_response.json()
            access_token = tokens.get('access_token')
        else:
            raise UserError('Error fetching access token.')

        # Search shared folder
        url = "https://graph.microsoft.com/v1.0/me/drive/sharedWithMe"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            found_folders = []
            for item in data.get("value", []):
                if item.get("folder") and item.get("name") == self.folder_name:
                    found_folders.append(item)

            if found_folders:
                for folder in found_folders:
                    site_id = folder.get("remoteItem", {}).get("parentReference", {}).get("siteId")
                    item_id = folder.get("remoteItem", {}).get("id")

                    children_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/items/{item_id}/children"
                    children_response = requests.get(children_url, headers=headers)

                    if children_response.status_code == 200:
                        children_data = children_response.json()

                        for child in children_data.get("value", []):
                            if child['name'] == self.file_name:
                                if child['name'].endswith('.xlsx'):
                                    file_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/items/{child['id']}/content"
                                    excel_response = requests.get(file_url, headers=headers)

                                    if excel_response.status_code == 200:
                                        excel_content = BytesIO(excel_response.content)
                                        self.process_excel_content(excel_content)
                                        return
                                    else:
                                        raise UserError(f"Error accessing file: {excel_response.status_code} - {excel_response.text}")
                                else:
                                    raise UserError("The file is not an Excel file.")
                        else:
                            raise UserError("File not found in the folder.")
                    else:
                        raise UserError(f"Error retrieving children: {children_response.status_code} - {children_response.text}")
            else:
                raise UserError("No folders found with the specified name.")
        else:
            raise UserError(f"Error: {response.status_code} - {response.text}")

    def process_excel_content(self, excel_content):
        df = pd.read_excel(excel_content)
        df = df.apply(lambda x: x.map(lambda y: None if isinstance(y, float) and (pd.isinf(y) or pd.isna(y)) else y))

        db_url = 'postgresql://odoo:odoo@172.188.42.27:9832/dev'
        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)

        with Session() as session:
            for index, row in df.iterrows():
                lead_id = row.get('lead_id')
                existing_lead = session.query(CustomSearchFolder).filter(CustomSearchFolder.lead_id == lead_id).first()
                if not existing_lead:
                    # Create a new lead record
                    new_lead = CustomSearchFolder(
                        lead_id=lead_id,
                        contact_name=row.get('contact_name'),
                        company_ids=row.get('company_ids'),
                        title=row.get('title_name'),
                        mobile=row.get('mobile'),
                        email=row.get('email'),
                        street=row.get('street'),
                        street2=row.get('street2'),
                        zip=row.get('zip'),
                        state_id=row.get('state_name'),  # Adjust as necessary
                        country_id=row.get('country_name'),  # Adjust as necessary
                        campaign_id=row.get('campaign_name'),  # Adjust as necessary
                        source_id=row.get('source_name'),  # Adjust as necessary
                        city=row.get('city'),
                    )
                    session.add(new_lead)

            # Commit the changes after adding all new leads
            session.commit()
