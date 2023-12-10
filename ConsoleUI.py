import utility
import smtp
import threading

def send_actions():
    input_mail = utility.Input_mail()
    general = input_mail.general_info
    From = general.get('Username').split('<')[-1].replace('>', '')
    To = []
    Cc = []
    Bcc = []
    Attachments = []
    
    while True:
        choice = int(input("Press 1 to choose To\nPress 2 to choose Cc\nPress 3 to choose Bcc\nYour choice: "))
        if choice == 1:
            to_input = input("Input To receiver(s): ")
            input_mail.input_to(To, to_input)
            break
        elif choice == 2:
            cc_input = input("Input Cc receiver(s): ")
            input_mail.input_cc(Cc, cc_input)
            break
        elif choice == 3:
            bcc_input = input("Input Bcc receiver(s): ")
            input_mail.input_bcc(Bcc, bcc_input)
            break
        else:
            print('Choose again!!!')
        
    Subject = input("Input mail subject: ")
    Body = input('Input mail body:\n')
    
    while True:
        choice = int(input("Press 1 to add attachment\nPress 2 to skip\n"))
        if choice == 1:
            attachment_input = input("Input attachment(s)' path: ")
            paths = input_mail.input_attachment(Attachments, attachment_input)
            break
        elif choice == 2:
            break
        else:
            print('Choose again!!!')
            
    SMTP = smtp.SMTPClient(general.get('MailServer'), int(general.get('SMTP')))
    SMTP.login()
    SMTP.send_mail(From, To, Cc, Bcc, Subject, Body, Attachments)
    SMTP.close()
    
def receive_actions():
    while True:
        dtb = utility.Read_dtb()
        csv_lines, csv_rows = dtb.get_mailbox_status()
        
        general, filter = dtb.load_config()
        username = general.get('Username').split('<')[-1].replace('>', '')
        password = general.get('Password')
        autoload_str = general.get('Autoload').split()
        if autoload_str[-1] == 'sec':
            autoload = int(autoload_str[0])
        elif autoload_str[-1] == 'min':
            autoload = int(autoload_str[0]) * 60
        elif autoload_str[-1] == 'hour':
            autoload = int(autoload_str[0]) * 3600    
        
        get_mail = utility.Download_mail(general.get('MailServer'), int(general.get('POP3')), username, password)
        
        num_server_mail = get_mail.get_num_mails()
        num_server_mail = int(num_server_mail.split(' ')[1])
        
        undownloaded_list = dtb.get_undownload_mail_id(username, num_server_mail)
        for id in undownloaded_list:
            email = get_mail.get_1_mail(id)
            get_mail.save_mail(username, email, filter, id)
            if get_mail.has_attachments(email):
                get_mail.get_attachments(username, email, filter, id)
            
        smtp.time.sleep(autoload)

def show_mail():
    dtb = utility.Read_dtb()
    csv_lines, csv_rows = dtb.get_mailbox_status()
    
    general, filter = dtb.load_config()
    username = general.get('Username').split('<')[-1].replace('>', '')
    
    for line in csv_lines:
        print(line[0])
    row_input = int(input("\nChoose the row of the mail you wanna read: "))
    print(dtb.read_file_from_row(row_input))
    
def menu():
    daemon_thread = threading.Thread(target=receive_actions)
    daemon_thread.start()
    
    while True:
        action_choice = int(input("Press 1 to send email\nPress 2 to read email\nPress others to end program\n\nYour choice: "))
        if action_choice == 1:
            send_actions()
        elif action_choice == 2:
            show_mail()
        else:
            utility.Download_mail.close()
            break
    
    daemon_thread.join()

if __name__ == '__main__':
    menu()