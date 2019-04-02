# coding:utf-8

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
import re

#邮箱正则表达式
re_email = re.compile(r'^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$')
def is_valid_email(addr):
    if re_email.match(addr):
        print("邮箱格式合格")
        return addr
    else :
        print('邮箱格式不合格')
        return False


def email(file_path,receiver):
    # 设置smtplib所需的参数
    # 下面的发件人，收件人是用于邮件传输的。
    smtpserver = 'smtp.qq.com'
    username = '455218836@qq.com'
    password = 'lmivwzxsghtybhdc'
    sender = '455218836@qq.com'
    receiver = receiver
    # 收件人为多个收件人
    # receiver = ['XXX@126.com', 'XXX@126.com']

    subject = '门禁出入记录'
    # 通过Header对象编码的文本，包含utf-8编码信息和Base64编码信息。以下中文名测试ok
    # subject = '中文标题'
    # subject=Header(subject, 'utf-8')

    # 构造邮件对象MIMEMultipart对象
    # 下面的主题，发件人，收件人，日期是显示在邮件页面上的。最好通过header重新编码，免得出现编码问题
    msg = MIMEMultipart('mixed')
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = Header('门禁系统管理员 <455218836@qq.com>', 'utf-8')
    msg['To'] = Header(receiver, 'utf-8')
    # 收件人为多个收件人,通过join将列表转换为以;为间隔的字符串
    # msg['To'] = ";".join(receiver)
    # msg['Date']='2012-3-16'

    # 构造文字内容
    text = "您好!\n此附件为门禁系统出入记录。\n请注意查收！"
    text_plain = MIMEText(text, 'plain', 'utf-8')
    msg.attach(text_plain)

    # 构造附件
    sendfile = open(file_path, 'rb').read()
    text_att = MIMEText(sendfile, 'base64', 'utf-8')
    text_att["Content-Type"] = 'application/octet-stream'
    # 要将文件通过以下两种方式重命名，不然发送的附件就是.bin文件
    # 以下附件可以重命名成aaa.txt
    # text_att["Content-Disposition"] = 'attachment; filename="aaa.txt"'
    # 另一种实现方式
    text_att.add_header('Content-Disposition', 'attachment', filename='门禁出入记录.xls')
    msg.attach(text_att)

    try:
        # 发送邮件
        smtp = smtplib.SMTP_SSL(smtpserver, port=465)
        # 我们用set_debuglevel(1)就可以打印出和SMTP服务器交互的所有信息。
        # smtp.set_debuglevel(1)
        smtp.login(username, password)
        smtp.sendmail(sender, receiver, msg.as_string())
        smtp.quit()
        print("邮件已发送")
    except Exception:
        print("发送邮件失败" + Exception)
