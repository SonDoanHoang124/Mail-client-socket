import os

import pop3
import base64

import csv
from bs4 import BeautifulSoup

class Read_dtb:
    def __init__(self):
        pass
    
    def load_config(self):
        with open('config.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        soup = BeautifulSoup(html_content, 'html.parser')

        general_info = {}
        filter_info = {}

        general_section = soup.find('h2', string='General:').find_next('ul')
        for li in general_section.find_all('li'):
            key, value = li.text.split(': ')
            general_info[key.strip()] = value.strip()

        filter_section = soup.find('h2', string='Filter:').find_next('ul')
        for li in filter_section.find_all('li'):
            parts = li.text.split(' - ')
            filter, criteria = parts[0].split(': ')  # Corrected line
            filter_info[filter.strip()] = criteria.strip()
            
        return general_info, filter_info

    def get_mailbox_status(self):
        with open('mail_status.csv', 'r') as f:
            reader = csv.reader(f, delimiter='\t')
            row_cnt = sum(1 for row in reader)
        return reader, row_cnt
    
    #def update_mailbox(self, mail)

class Download_mail:
    def __init__(self, server, port, username, password):
        self.pop3_client = pop3.POP3Client(server, port)
        self.pop3_client.login(username, password)

    def get_1_mail(self, mail_No):
        list = self.pop3_client.list_emails()
        mail = self.pop3_client.retrieve_email(mail_No)
        
        return mail, list

    def get_sender(self, mail):
        line = mail.splitlines()[2]
        if 'From:' not in line:
            print('Mail not in correct format')
            return ''
        start_idx = line.find('<') + 1
        end_idx = line.find('>', start_idx)
        sender = line[start_idx:end_idx].strip()
        return sender

    def get_to(self, mail):
        line = mail.splitlines()[3]
        if 'To:' not in line:
            print('Mail not in correct format')
            return ''
        if '<' in line:
            emails = line.split('<')
            valid_emails = [part.strip('>') for part in emails if '@' in part]
            cleaned_emails = [email.replace('> ', '') for email in valid_emails]
            return cleaned_emails
        return []
    
    def get_cc(self, mail):
        line = mail.splitlines()[4]
        if 'Cc:' not in line:
            print('Mail not in correct format')
            return ''
        if '<' in line:
            emails = line.split('<')
            valid_emails = [part.strip('>') for part in emails if '@' in part]
            cleaned_emails = [email.replace('> ', '') for email in valid_emails]
            return cleaned_emails
        return []

    def get_bcc(self, mail):
        line = mail.splitlines()[5]
        if 'Bcc:' not in line:
            print('Mail not in correct format')
            return ''
        if '<' in line:
            emails = line.split('<')
            valid_emails = [part.strip('>') for part in emails if '@' in part]
            cleaned_emails = [email.replace('> ', '') for email in valid_emails]
            return cleaned_emails
        return []
    
    def get_subject(self, mail):
        line = mail.splitlines()[6]
        if 'Subject:' not in line:
            print('Mail not in correct format')
            return ''
        parts = line.split(':')
        subject = parts[1].strip()
        return subject
    
    def get_msg_id(self, mail):
        line = mail.splitlines()[7]
        if 'Message ID:' not in line:
            print('Mail not in correct format')
            return ''
        return line

    def get_send_time(self, mail):
        line = mail.splitlines()[8]
        # check format
        week_day = line[6:9]
        if week_day not in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']:
            print('Mail not in correct format')
            return ''
        parts = line.split(':')
        time_part = parts[1:]
        time = ':'.join(str(part) for part in time_part)
        return time.replace(' ', '', 1)
    
    def get_boundary(self, mail):
        line = mail.splitlines()[10]
        if 'boundary' not in line:
            print('Mail not in correct format')
            return ''
        return f"--{line[-34:-1]}"
    
    def has_attachments(self, mail):
        content_parts = mail.split(self.get_boundary(mail))
        if len(content_parts) > 2:
            return True
        return False
    
    def get_content(self, mail):
        content_parts = mail.split(self.get_boundary(mail))
        content_part = content_parts[1]
        
        content = content_part.splitlines()[3:]
        content = '\n'.join(str(line) for line in content)
        return content
    
    def compose_mail(self, username, mail):
        msg = f"""
From: {self.get_sender(mail)}
"""
        TO = self.get_to(mail)
        CC = self.get_cc(mail)
        BCC = self.get_bcc(mail)
        
        if BCC and username in BCC:
            msg += f"To: <{username}>"
        elif CC:
            msg += "Cc: "
            for cc in CC:
                msg += f"<{cc}> "
        elif TO:
            msg += "To: "
            for to in TO:
                msg += f"<{to}> "
        
        msg +=f"""
Subject: {self.get_subject(mail)}

{self.get_content(mail)}
"""
        return msg
    
    def filter_mail(self, mail, filter_info):
        From = self.get_sender(mail)
        Subject = self.get_subject(mail)
        Content = self.get_content(mail)
        for filter, criteria in filter_info.items():
            if filter == 'From' and any(word.lower() == From.strip().lower() for word in criteria):
                return 'Project'
            elif filter == 'Subject' and any(word.lower() == Subject.strip().lower() for word in criteria):
                return 'Important'
            elif filter == 'Content' and any(word.lower() == Content.strip().lower() for word in criteria):
                return filter
            elif filter == 'Spam' and any(word.lower() == Subject.strip().lower() or word.lower() == Content.strip().lower() for word in criteria):
                return filter
        return "Inbox"
    
    def save_mail(self, username, mail, filter_info, mail_No):
        saved_mail = self.compose_mail(username, mail)
        filter_folder = self.filter_mail(mail, filter_info)
        mail_name = f"{mail_No}_{username}.txt"
        
        with open(f'{filter_folder}/{mail_name}', 'w') as f:
            f.write(saved_mail)
        with open('mail_status.csv', 'a', newline='') as f:
            if self.has_attachments(mail):
                has_attach = 'true'
            else:
                has_attach = 'false'
            new_row = [mail_No,username,self.get_subject(mail),'unread',has_attach]
            add_row = csv.writer(f)
            add_row.writerow(new_row)
            f.close()

    def get_attachments(self, mail, filter_info):
        attachments = mail.split(self.get_boundary(mail))
        attachments = attachments[2:]

        for attach in attachments[:-1]:
            filename_line = attach.splitlines()[2]
            filename_parts = filename_line.split('=')
            filename = filename_parts[1][1:-1]
            
            raw_data = attach.splitlines()[5]
            raw_data = ''.join(str(ele) for ele in raw_data)
            
            path = f'{self.filter_mail(mail,filter_info)}\attachments\{filename}'
            with open(path, 'wb') as f:
                f.write(base64.b64decode(raw_data))

    def __del__(self):
        self.pop3_client.close()        

a = Read_dtb()

general_info, filter_info = a.load_config()
# Print the extracted information
"""print("General Information:\n")
for key, value in general_info.items():
    print(f"{key}: {value}")

print("\nFilter Information:\n")
for filter, criteria in filter_info.items():
    print(f"{filter}: {criteria}")"""

mail_dtb, row = a.get_mailbox_status()

username = "your_email@example.com"
password = "your_password"
mail_downloader = Download_mail("127.0.0.1", 1100, username, password)      
#for i in range(14,16):
test, list = mail_downloader.get_1_mail(8)
mail_downloader.save_mail(username, test, filter_info, 8)
#print(mail_downloader.has_attachments(test))
#print("Mail is filtered into: ",mail_downloader.filter_mail(test, filter_info), " folder")
#print(mail_downloader.compose_mail(username,test))
#mail_downloader.get_attachments(test)