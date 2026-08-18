import smtplib

server = smtplib.SMTP("smtp.gmail.com", 587)

server.set_debuglevel(1)

server.ehlo()

server.starttls()

server.ehlo()

print("Connected Successfully")

server.quit()