import pyttsx3


def VoiceBroadcast(flag, num=None, name=None, logname=None, receiver=None):
    engine = pyttsx3.init()

    if flag == 1:
        engine.say("智能门禁系统已启动")

    elif flag == 2:
        engine.say("工号:" + num + " 姓名:" + name + " 的人脸数据已存在数据库")

    elif flag == 3:
        engine.say("工号:" + num + " 姓名:" + name + " 的人脸数据已成功存入数据库")

    elif flag == 4:
        engine.say("工号:" + num + " 姓名:" + name + " ，门已开，请进")

    elif flag == 5:
        engine.say("进出日志:" + logname + " ，导出成功，请在当前文件夹查看")

    elif flag == 6:
        engine.say("人员信息文件:" + logname + " ，导出成功，请在当前文件夹查看")

    elif flag == 7:
        engine.say("邮件发送成功,请告知收件人:" + receiver + ",注意查收")

    elif flag == 8:
        engine.say("邮件发送失败，请尝试重新发送")

    else:
        pass

    engine.runAndWait()
