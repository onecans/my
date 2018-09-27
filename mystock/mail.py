# Settings

SMTP_SERVER = 'locolhost'
SMTP_PORT = 25
SMTP_FROM = 'sender@example.com'
SMTP_TO = 'recipient@example.com'

TEXT_FILENAME = '/u01/mystock_all.zip'
MESSAGE = """This is the message
to be sent to the client.
"""

import email
import os
# Now construct the message
import smtplib
from email import encoders

msg = email.MIMEMultipart.MIMEMultipart()
body = email.MIMEText.MIMEText(MESSAGE)
attachment = email.MIMEBase.MIMEBase('text', 'plain')
attachment.set_payload(open(TEXT_FILENAME).read())
attachment.add_header('Content-Disposition', 'attachment', filename=os.path.basename(TEXT_FILENAME))
encoders.encode_base64(attachment)
msg.attach(body)
msg.attach(attachment)
msg.add_header('From', SMTP_FROM)
msg.add_header('To', SMTP_TO)

# Now send the message
mailer = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
# EDIT: mailer is already connected
# mailer.connect()
mailer.sendmail(SMTP_FROM, [SMTP_TO], msg.as_string())
mailer.close()
