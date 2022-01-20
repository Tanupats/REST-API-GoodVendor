# ใช้งานโมดูล
import smtplib
from models.login import genotp
def senEmail(email):
    # กำหนดตัวแปรชื่อผู้ใช้ และ รหัสผ่าน ตามบัญชีผู้ใช้
    username = 'postmaster@sandbox05ab5292006549dcbd4ffdc43d616466.mailgun.org'
    password = '440e28dfdfa49bbbb205fab3d28b5c44-ef80054a-1d794425'
    # กำหนดตัวแปรอีเมลผู้ส่ง และ ผู้รับ
    sender = 'goodvendor2022@gmail.com'
    recipient = str(email)
    
    # เนื้อหาของอีเมล
    body = """
    verify code is 
    """
   
  
    header = f'To: { recipient }\n'

    mail =  header + body + genotp()

    # ตั้งค่าเซิร์ฟเวอร์ด้วยชื่อโฮส และ พอร์ท
    server = smtplib.SMTP('smtp.mailgun.org',587)
    server.login(username, password)
    server.sendmail(sender, recipient, mail)
    server.quit()
