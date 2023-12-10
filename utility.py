import os

import pop3
import base64

import csv
from bs4 import BeautifulSoup

MAX_FILE_SIZE = 3 * 1024 * 1024

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
            filter, criteria = parts[0].split(': ')
            filter_info[filter.strip()] = criteria.strip()
            
        return general_info, filter_info

    def get_mailbox_status(self):
        with open('mail_status.csv', 'r') as f:
            reader = csv.reader(f, delimiter='\t')
            rows = list(reader)
            row_cnt = len(rows)
        return rows, row_cnt - 1
    
    def get_undownload_mail_id(self, username, STAT):
        with open('mail_status.csv', 'r') as f:
            reader = csv.DictReader(f)
            missing_ids = set(range(1, STAT + 1)) # = {1 : STAT + 1}
            for row in reader:
                # check username col and get server_id as number
                if row['username'] == username and row['server_id'].isdigit():
                    server_id = int(row['server_id'])
                    if server_id in missing_ids:
                        missing_ids.remove(server_id)
            f.close()
        return list(missing_ids)
    
    # This func is for manual download :))
    def check_download_mail(self, username, mail_No):
        with open('mail_status.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['username'] == username and int(row['server_id']) == mail_No:
                    f.close()
                    return True
            f.close()
        return False
    
    def read_file_from_row(self, row_num):
        with open('mail_status.csv', 'r') as f:
            reader = csv.reader(f, delimiter=',')
            next(reader)  # Skip header row
            for i, row in enumerate(reader, start=1):
                if i == row_num:
                    server_id, username, subject, status, folder, attachments = row
                    file_path = os.path.join(folder, f'{server_id}_{username}.txt')
                    
                    try:
                        with open(file_path, 'r') as file:
                            content = file.read()
                            return content
                    except FileNotFoundError:
                        return f"File not found: {file_path}"

class Input_mail:
    def __init__(self):
        self.general_info, self.filter_info = Read_dtb().load_config()
    
    def input_to(self, to_list, to_str):
        if to_str:
            to_str = to_str.split(',')
            to_mails = [mail.strip() for mail in to_str]
            to_list.extend(to_mails)
    
    def input_cc(self, cc_list, cc_str):
        if cc_str:
            cc_str = cc_str.split(',')
            cc_mails = [mail.strip() for mail in cc_str]
            cc_list.extend(cc_mails)
    
    def input_bcc(self, bcc_list, bcc_str):
        if bcc_str:
            bcc_str = bcc_str.split(',')
            bcc_mails = [mail.strip() for mail in bcc_str]
            bcc_list.extend(bcc_mails)
    
    def input_attachment(self, attachments_list, attachments_str):
        if attachments_list:
            attachments_str = attachments_str.split(',')
            attachments = [attach.strip() for attach in attachments_str]
            attachments = self.valid_attachment_1(attachments)
            for attach in attachments:
                attachments_list.extend({'filename': os.path.basename(attach), 'file_path': attach})
    
    # ver 1.0: each file <= 3 MB
    def valid_attachment_1(self, attach_paths):
        valid_paths = []
        for path in attach_paths:
            if os.path.getsize(path) <= MAX_FILE_SIZE:
                valid_paths.append(path)
            else:
                print(f'{os.path.basename(path)} is larger than 3 MB')
                print(f'Excluding {os.path.basename(path)} out of attachment list')
        return valid_paths

    # ver 2.0: sum file size = 3 MB
    def valid_attachment_2(self, attach_paths):
        valid_paths = []
        sum_size = 0
        for path in attach_paths:
            sum_size += os.path.getsize(path)
            if sum_size <= MAX_FILE_SIZE:
                valid_paths.append(path)
            else:
                print(f'Excluding the last {len(attach_paths) - len(valid_paths)} files')
                print('Due to the total is already reach 3MB')
        return valid_paths

class Download_mail:
    def __init__(self, server, port, username, password):
        self.pop3_client = pop3.POP3Client(server, port)
        self.pop3_client.login(username, password)
        
    def get_num_mails(self):
        num = self.pop3_client.num_emails()
        return num
    
    def get_1_mail(self, mail_No):
        mail = self.pop3_client.retrieve_email(mail_No)
        return mail

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
        lines = mail.splitlines()
        for line in lines:
            if line.startswith('Content-Type: multipart/mixed;'):
                return True
        return False
    
    def get_content(self, mail):
        if self.has_attachments(mail):
            content_parts = mail.split(self.get_boundary(mail))
            content_part = content_parts[1]
            
            content = content_part.splitlines()[3:]
            content = '\n'.join(str(line) for line in content)
        else:
            content = mail[15:]
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
            if filter == 'From' and any(email.strip().lower() in From.strip().lower() for email in criteria.split(', ')):
                if not os.path.exists("Project"): 
                    os.makedirs("Project") 
                return 'Project'
            elif filter == 'Subject' and any(word.lower() in Subject.strip().lower() for word in criteria.split(', ')):
                if not os.path.exists("Important"): 
                    os.makedirs("Important") 
                return 'Important'
            elif filter == 'Content' and any(word.lower() in Content.strip().lower() for word in criteria.split(', ')):
                if not os.path.exists("Work"): 
                    os.makedirs("Work") 
                return 'Work'
            elif filter == 'Spam' and any(word.lower() in Subject.strip().lower() or word.lower() in Content.strip().lower() for word in criteria.split(', ')):
                if not os.path.exists("Spam"): 
                    os.makedirs("Spam") 
                return "Spam"
        if not os.path.exists("Inbox"): 
            os.makedirs("Inbox") 
        return "Inbox"
    
    def save_mail(self, username, mail, filter_info, mail_No):
        saved_mail = self.compose_mail(username, mail)
        filter_folder = self.filter_mail(mail, filter_info)
        mail_name = f"{mail_No}_{username}.txt"
        csv_lines, csv_rows = Read_dtb().get_mailbox_status()
        csv_lines = csv_lines[1:]
        
        with open(f'{filter_folder}/{mail_name}', 'w') as f:
            f.write(saved_mail)
            f.close()
        with open('mail_status.csv', 'a', newline='') as f:
            if self.has_attachments(mail):
                has_attach = 'true'
            else:
                has_attach = 'false'
            
            new_row = [mail_No,username,self.get_subject(mail),'unread',filter_folder,has_attach]
            if new_row not in csv_lines:
                add_row = csv.writer(f)
                add_row.writerow(new_row)
            f.close()

    def get_attachments(self, username, mail, filter_info, mail_No):
        attachments = mail.split(self.get_boundary(mail))
        attachments = attachments[2:-1]

        for attach in attachments:
            filename_line = attach.splitlines()[2]
            filename_parts = filename_line.split('=')
            filename = filename_parts[1][1:-1]
            
            raw_data = attach.splitlines()[4]
            raw_data = ''.join(str(ele) for ele in raw_data)
            
            attachment_folder = f"{mail_No}_{username}"
            attachment_path = f'{self.filter_mail(mail,filter_info)}/{attachment_folder}'
            if not os.path.exists(attachment_path):
                os.makedirs(attachment_path)
            
            save_path = f'{attachment_path}\{filename}'
            with open(save_path, 'wb') as f:
                f.write(base64.b64decode(raw_data))

    def __del__(self):
        self.pop3_client.close()   
"""
a = Read_dtb()

general_info, filter_info = a.load_config()
# Print the extracted information
print("General Information:\n")
for key, value in general_info.items():
    print(f"{key}: {value}")

print("\nFilter Information:\n")
for filter, criteria in filter_info.items():
    print(f"{filter}: {criteria}")

mail_dtb, row = a.get_mailbox_status()
print("Row =",row)

username = "your_email@example.com"
password = "your_password"
mail_downloader = Download_mail("127.0.0.1", 1100, username, password)      
#for i in range(14,16):
test = mail_downloader.get_1_mail(4)
#print(mail_downloader.get_bcc(test))
mail_downloader.save_mail(username, test, filter_info, 4)
#print(mail_downloader.has_attachments(test))
#print("Mail is filtered into: ",mail_downloader.filter_mail(test, filter_info), " folder")
#print(mail_downloader.compose_mail(username,test))
#mail_downloader.get_attachments(username, test, filter_info, 4)"""