import smtplib
from email.message import EmailMessage
import datetime

EMAIL_APP_PSWRD = "lcyb kjcl uksd ltkg"

#Set the sender email and password and recipient emaiç
from_email_addr ="raspberry44hugh@gmail.com"
from_email_pass = EMAIL_APP_PSWRD
to_email_addr ="watson.bm4@gmail.com"

events = [{
    'summary': 'Chewblockas Volleyball',
    'description': 'Gym: TCC, Pool: C POOL',
    'start': datetime.datetime(2025, 11, 26, 19, 30),
    'end': datetime.datetime(2025, 11, 26, 21, 0)
}]

def send_email(events, **kwargs):
    # Create a message object
    msg = EmailMessage()
    event = events[0]

    summary = event['summary']
    description = event['description']
    start_time = event['start'].strftime("%Y-%m-%d %H:%M")
    end_time = event['end'].strftime("%Y-%m-%d %H:%M")

    # Set the email body
    body = f"""
        Event Summary: {summary}
        Details: {description}

        Start: {start_time}
        End:   {end_time}
    """
    msg.set_content(body)

    # Set sender and recipient
    msg['From'] = from_email_addr
    msg['To'] = to_email_addr

    # Set your email subject
    msg['Subject'] = 'KVA Schedule Updated'

    # Connecting to server and sending email
    # Edit the following line with your provider's SMTP server details
    server = smtplib.SMTP('smtp.gmail.com', 587)

    # Comment out the next line if your email provider doesn't use TLS
    server.starttls()
    # Login to the SMTP server
    server.login(from_email_addr, from_email_pass)

    # Send the message
    server.send_message(msg)

    print('Email sent')

    #Disconnect from the Server
    server.quit()

def main():
    send_email(events)

if __name__ == "__main__":
    main()