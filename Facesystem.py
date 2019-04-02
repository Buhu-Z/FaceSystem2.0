# coding=utf-8
import wx
import wx.grid
import sqlite3
from time import localtime, strftime
import os
from skimage import io as iio
import dlib  # 人脸识别的库dlib
import numpy as np  # 数据处理的库numpy
import cv2  # 图像处理的库OpenCv
import _thread

import Export_to_excel
import deal_data
import send_email

ID_NEW_REGISTER = 160
ID_FINISH_REGISTER = 161

ID_START_PUNCHCARD = 190
ID_END_PUNCARD = 191

ID_OPEN_LOGCAT = 283
ID_CLOSE_LOGCAT = 284

ID_EXPORT_LOGCAT = 255
ID_PERSON_INFO = 256

ID_SEND_EMAIL = 123

ID_WORKER_UNAVIABLE = -1

PATH_FACE = "data/face_img_database/"
# face recognition model, the object maps human faces into 128D vectors
facerec = dlib.face_recognition_model_v1("model/dlib_face_recognition_resnet_model_v1.dat")
# Dlib 预测器
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor('model/shape_predictor_68_face_landmarks.dat')


def return_euclidean_distance(feature_1, feature_2):
    feature_1 = np.array(feature_1)
    feature_2 = np.array(feature_2)
    dist = np.sqrt(np.sum(np.square(feature_1 - feature_2)))
    print("欧式距离: ", dist)

    if dist > 0.4:
        return "diff"
    else:
        return "same"


class WAS(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, parent=None, title="智能门禁系统", size=(920, 560))

        self.initMenu()
        self.initInfoText()
        self.initGallery()
        self.initDatabase()
        self.initData()

    def initData(self):
        self.name = ""
        self.id = ID_WORKER_UNAVIABLE
        self.face_feature = ""
        self.pic_num = 0
        self.flag_registed = False
        self.puncard_time = "09:00:00"
        self.loadDataBase(1)

    # 界面初始化
    def initMenu(self):

        menuBar = wx.MenuBar()  # 生成菜单栏
        menu_Font = wx.Font()  # Font(faceName="consolas",pointsize=20)
        menu_Font.SetPointSize(14)
        menu_Font.SetWeight(wx.BOLD)

        registerMenu = wx.Menu()  # 生成菜单
        self.new_register = wx.MenuItem(registerMenu, ID_NEW_REGISTER, "新建录入")
        self.new_register.SetBitmap(wx.Bitmap("drawable/new_register.png"))
        self.new_register.SetTextColour("SLATE BLUE")
        self.new_register.SetFont(menu_Font)
        registerMenu.Append(self.new_register)

        self.finish_register = wx.MenuItem(registerMenu, ID_FINISH_REGISTER, "完成录入")
        self.finish_register.SetBitmap(wx.Bitmap("drawable/finish_register.png"))
        self.finish_register.SetTextColour("SLATE BLUE")
        self.finish_register.SetFont(menu_Font)
        self.finish_register.Enable(False)
        registerMenu.Append(self.finish_register)

        puncardMenu = wx.Menu()
        self.start_punchcard = wx.MenuItem(puncardMenu, ID_START_PUNCHCARD, "开始识别")
        self.start_punchcard.SetBitmap(wx.Bitmap("drawable/start_punchcard.png"))
        self.start_punchcard.SetTextColour("SLATE BLUE")
        self.start_punchcard.SetFont(menu_Font)
        puncardMenu.Append(self.start_punchcard)

        self.end_puncard = wx.MenuItem(puncardMenu, ID_END_PUNCARD, "结束识别")
        self.end_puncard.SetBitmap(wx.Bitmap("drawable/end_puncard.png"))
        self.end_puncard.SetTextColour("SLATE BLUE")
        self.end_puncard.SetFont(menu_Font)
        self.end_puncard.Enable(False)
        puncardMenu.Append(self.end_puncard)

        logcatMenu = wx.Menu()
        self.open_logcat = wx.MenuItem(logcatMenu, ID_OPEN_LOGCAT, "打开日志")
        self.open_logcat.SetBitmap(wx.Bitmap("drawable/open_logcat.png"))
        self.open_logcat.SetFont(menu_Font)
        self.open_logcat.SetTextColour("SLATE BLUE")
        logcatMenu.Append(self.open_logcat)

        self.close_logcat = wx.MenuItem(logcatMenu, ID_CLOSE_LOGCAT, "关闭日志")
        self.close_logcat.SetBitmap(wx.Bitmap("drawable/close_logcat.png"))
        self.close_logcat.SetFont(menu_Font)
        self.close_logcat.SetTextColour("SLATE BLUE")
        self.end_puncard.Enable(False)
        logcatMenu.Append(self.close_logcat)

        exportlogMenu = wx.Menu()
        self.export_logcat = wx.MenuItem(exportlogMenu, ID_EXPORT_LOGCAT, "进出日志")
        self.export_logcat.SetBitmap(wx.Bitmap("drawable/export_logcat.png"))
        self.export_logcat.SetFont(menu_Font)
        self.export_logcat.SetTextColour("SLATE BLUE")
        exportlogMenu.Append(self.export_logcat)

        self.export_person = wx.MenuItem(exportlogMenu, ID_PERSON_INFO, "人员信息")
        self.export_person.SetBitmap(wx.Bitmap("drawable/export_person.png"))
        self.export_person.SetFont(menu_Font)
        self.export_person.SetTextColour("SLATE BLUE")
        exportlogMenu.Append(self.export_person)

        emailMenu = wx.Menu()
        self.send_email = wx.MenuItem(emailMenu, ID_SEND_EMAIL, "发送邮件")
        self.send_email.SetBitmap(wx.Bitmap("drawable/send_email.png"))
        self.send_email.SetFont(menu_Font)
        self.export_person.SetTextColour("SLATE BLUE")
        emailMenu.Append(self.send_email)

        menuBar.Append(registerMenu, "&人脸录入")
        menuBar.Append(puncardMenu, "&人脸识别")
        menuBar.Append(logcatMenu, "&日志查看")
        menuBar.Append(exportlogMenu, "资料导出")
        menuBar.Append(emailMenu, "邮件管理")
        self.SetMenuBar(menuBar)

        self.Bind(wx.EVT_MENU, self.OnNewRegisterClicked, id=ID_NEW_REGISTER)
        self.Bind(wx.EVT_MENU, self.OnFinishRegisterClicked, id=ID_FINISH_REGISTER)
        self.Bind(wx.EVT_MENU, self.OnStartPunchCardClicked, id=ID_START_PUNCHCARD)
        self.Bind(wx.EVT_MENU, self.OnEndPunchCardClicked, id=ID_END_PUNCARD)
        self.Bind(wx.EVT_MENU, self.OnOpenLogcatClicked, id=ID_OPEN_LOGCAT)
        self.Bind(wx.EVT_MENU, self.OnCloseLogcatClicked, id=ID_CLOSE_LOGCAT)
        self.Bind(wx.EVT_MENU, self.OnExportLogcatCilcked, id=ID_EXPORT_LOGCAT)
        self.Bind(wx.EVT_MENU, self.OnExportPersonCilcked, id=ID_PERSON_INFO)
        self.Bind(wx.EVT_MENU, self.OnSendEmailCilcked, id=ID_SEND_EMAIL)

    # 发送邮件 点击事件
    def OnSendEmailCilcked(self, event):
        print("已点击导出邮件")
        self.receiver = ""
        Export_to_excel.export_excel("门禁出入记录", ID_EXPORT_LOGCAT)
        file_path = os.path.abspath("data/门禁出入记录.xls")
        print(file_path)
        # 设置收件人输入框
        while self.receiver == "":
            email_addr = wx.GetTextFromUser(message="请输入收件人邮箱：",
                                            caption="收件人邮箱信息录入",
                                            default_value="", parent=self.bmp)
            if email_addr == "":
                wx.MessageBox("请输入收件人邮箱")
                break
            else:
                receiver1 = send_email.is_valid_email(email_addr)
                if receiver1:
                    while self.receiver == "":
                        email_addr = wx.GetTextFromUser(message="请再次输入收件人邮箱：",
                                                        caption="收件人邮箱信息录入",
                                                        default_value="", parent=self.bmp)
                        if email_addr == "":
                            wx.MessageBox("再次输入收件人邮箱为空或您已取消输入")
                            break
                        else:
                            receiver2 = send_email.is_valid_email(email_addr)
                            if receiver2:
                                if receiver1 == receiver2:
                                    self.receiver = receiver1
                                    print(self.receiver)
                                    try:
                                        send_email.email(file_path, self.receiver)
                                        self.infoText.AppendText(
                                            "\r\n" + self.getDateAndTime() + "\r\n" + "邮件发送成功\r\n""请告知收件人:" + self.receiver + "注意查收\r\n")
                                    except:
                                        self.infoText.AppendText(
                                            "\r\n" + self.getDateAndTime() + "\r\n" + "邮件发送失败，请尝试重新发送\r\n")

                                else:
                                    wx.MessageBox("两次邮箱不相同，请重新输入")
                                    break
                            else:
                                wx.MessageBox("再次输入邮箱地址格式不正确，请重新输入")
                                self.receiver = ""
                else:
                    wx.MessageBox("邮箱格式不正确，请重新输入")
                    self.receiver = ""
            # 内层循环中有需要的都会再次进入内层循环进行输入，如内层循环已中断，那外层循环无必要再进行一次故中断，退出两次循环
            break

    # 导出人员信息，点击事件响应
    def OnExportPersonCilcked(self, event):
        self.logname = wx.GetTextFromUser(message="请输入导出人员信息文件名",
                                          caption="温馨提示",
                                          default_value="", parent=self.bmp)
        if self.logname == "":
            wx.MessageBox("请输入导出日志文件名")
        else:
            Export_to_excel.export_excel(self.logname, ID_PERSON_INFO)
            self.infoText.AppendText(
                "\r\n" + self.getDateAndTime() + "\r\n" + "文件:" + self.logname + " 导出成功，请在当前文件夹查看\r\n")

    # 导出日志，点击事件响应
    def OnExportLogcatCilcked(self, event):
        self.logname = wx.GetTextFromUser(message="请输入导出日志文件名",
                                          caption="温馨提示",
                                          default_value="", parent=self.bmp)
        if self.logname == "":
            wx.MessageBox("请输入导出日志文件名")
        else:
            Export_to_excel.export_excel(self.logname, ID_EXPORT_LOGCAT)
            self.infoText.AppendText(
                "\r\n" + self.getDateAndTime() + "\r\n" + "日志:" + self.logname + " 导出成功，请在当前文件夹查看\r\n")

    # 打开日志 点击事件响应
    def OnOpenLogcatClicked(self, event):
        self.open_logcat.Enable(False)
        self.close_logcat.Enable(True)
        self.loadDataBase(2)
        grid = wx.grid.Grid(self, pos=(320, 0), size=(600, 500))

        # grid.CreateGrid(行数, 列数)
        grid.CreateGrid(self.num_of_logcat, 4)
        for i in range(self.num_of_logcat):
            for j in range(4):
                # grid.SetCellAlignment设置对齐方式
                grid.SetCellAlignment(i, j, wx.ALIGN_CENTER, wx.ALIGN_CENTER)
        grid.SetColLabelValue(0, "日志条数")  # 第一列标签
        grid.SetColLabelValue(1, "工号")
        grid.SetColLabelValue(2, "姓名")
        grid.SetColLabelValue(3, "打卡时间")

        grid.SetColSize(0, 100)
        grid.SetColSize(1, 100)
        grid.SetColSize(2, 100)
        grid.SetColSize(3, 150)

        grid.SetCellTextColour("NAVY")
        for i, id in enumerate(self.logcat_id):
            grid.SetCellValue(i, 0, str(self.logcat_num[i]))
            grid.SetCellValue(i, 1, str(id))
            grid.SetCellValue(i, 2, self.logcat_name[i])
            grid.SetCellValue(i, 3, self.logcat_datetime[i])

        pass

    # 关闭日志 点击事件响应
    def OnCloseLogcatClicked(self, event):
        self.open_logcat.Enable(True)
        self.close_logcat.Enable(False)
        self.initGallery()
        pass

    # 新建人脸 摄像头部分
    def register_cap(self, event):
        # 创建 cv2 摄像头对象
        self.cap = cv2.VideoCapture(0)
        # cap.set(propId, value)
        # 设置视频参数，propId设置的视频参数，value设置的参数值
        # self.cap.set(3, 600)
        # self.cap.set(4,600)
        # cap是否初始化成功
        while self.cap.isOpened():
            # cap.read()
            # 返回两个值：
            #    一个布尔值true/false，用来判断读取视频是否成功/是否到视频末尾
            #    图像对象，图像的三维矩阵
            flag, im_rd = self.cap.read()

            # 每帧数据延时1ms，延时为0读取的是静态帧
            kk = cv2.waitKey(1)
            # 人脸数 dets
            dets = detector(im_rd, 1)

            # 检测到人脸
            if len(dets) != 0:
                biggest_face = dets[0]
                # 取占比最大的脸
                maxArea = 0
                for det in dets:
                    # 计算面积，循环，找到最大的脸
                    w = det.right() - det.left()
                    h = det.top() - det.bottom()
                    if w * h > maxArea:
                        biggest_face = det
                        maxArea = w * h
                # 绘制矩形框
                cv2.rectangle(im_rd, tuple([biggest_face.left(), biggest_face.top()]),
                              tuple([biggest_face.right(), biggest_face.bottom()]),
                              (255, 0, 0), 2)
                # im_rd.shape()
                # 返回三个值：
                #    行数，列数，色彩通道数
                #    行数其实对应于坐标轴上的y,即表示的是图像的高度；列数对应于坐标轴上的x，即表示的是图像的宽度
                img_height, img_width = im_rd.shape[:2]
                # opencv的颜色空间是BGR,需要转为RGB才能用在dlib中
                image1 = cv2.cvtColor(im_rd, cv2.COLOR_BGR2RGB)
                pic = wx.Bitmap.FromBuffer(img_width, img_height, image1)
                # 显示图片在panel上
                self.bmp.SetBitmap(pic)

                # 获取当前捕获到的图像的所有人脸的特征，存储到 features_cap_arr
                shape = predictor(im_rd, biggest_face)
                # 计算人脸的128维的向量
                features_cap = facerec.compute_face_descriptor(im_rd, shape)

                # 对于某张人脸，遍历所有存储的人脸特征
                for i, knew_face_feature in enumerate(self.knew_face_feature):
                    # 将某张人脸与存储的所有人脸数据进行比对
                    compare = return_euclidean_distance(features_cap, knew_face_feature)
                    if compare == "same":  # 找到了相似脸
                        self.infoText.AppendText(
                            "\r\n" + self.getDateAndTime() + "\r\n" + "工号:" + str(self.knew_id[i])
                            + " 姓名:" + self.knew_name[i] + " 的人脸数据已存在\r\n")
                        self.flag_registed = True
                        self.OnFinishRegister()
                        _thread.exit()

                        # print(features_known_arr[i][-1])
                face_height = biggest_face.bottom() - biggest_face.top()
                face_width = biggest_face.right() - biggest_face.left()
                # numpy.zeros(shape, dtype=float, order='C')
                # 返回给定形状和类型的新数组，用零填充。
                # shape：整数的int或元组
                # dtype：数组的所需数据类型，例如numpy.int8。默认为numpy.float64。
                # order：是否在内存中以行主（C风格）或列主（Fortran风格）顺序存储多维数据。
                im_blank = np.zeros((face_height, face_width, 3), np.uint8)
                try:
                    # 这一部分要理解
                    for ii in range(face_height):
                        for jj in range(face_width):
                            im_blank[ii][jj] = im_rd[biggest_face.top() + ii][biggest_face.left() + jj]
                    self.pic_num += 1
                    # cv2.imwrite(path_make_dir+self.name + "/img_face_" + str(self.sc_number) + ".jpg", im_blank)
                    # cap = cv2.VideoCapture("***.mp4")
                    # cap.set(cv2.CAP_PROP_POS_FRAMES, 2)
                    # ret, frame = cap.read()
                    # cv2.imwrite("我//h.jpg", frame)  # 该方法不成功
                    # 解决python3下使用cv2.imwrite存储带有中文路径图片
                    if len(self.name) > 0:
                        # cv2.imencode(图片格式，图片)
                        cv2.imencode('.jpg', im_blank)[1].tofile(
                            PATH_FACE + self.name + "/img_face_" + str(self.pic_num) + ".jpg")  # 正确方法
                        print("写入本地：", str(PATH_FACE + self.name) + "/img_face_" + str(self.pic_num) + ".jpg")
                except:
                    print("保存照片异常,请对准摄像头")

                if self.new_register.IsEnabled():
                    _thread.exit()

                # 存储张数达到10，退出
                if self.pic_num == 10:
                    self.OnFinishRegister()
                    _thread.exit()

    # 新建人像 点击事件响应
    def OnNewRegisterClicked(self, event):
        self.new_register.Enable(False)
        self.finish_register.Enable(True)
        self.loadDataBase(1)
        while self.id == ID_WORKER_UNAVIABLE:
            self.id = wx.GetNumberFromUser(message="请输入您的工号(大于或等于0的整数)",
                                           prompt="工号", caption="温馨提示",
                                           value=ID_WORKER_UNAVIABLE + 1,
                                           parent=self.bmp, min=ID_WORKER_UNAVIABLE + 1)
            print(self.id)
            # 判断语句 wx.GetNumberFromUser函数点击cancel和对话框右上角×都是返回-1，因此当为-1时，break
            if self.id == -1:
                self.new_register.Enable(True)
                self.finish_register.Enable(False)
                break
            else:
                # 检查工号是否已存在，如果工号已存在，重新输入
                for knew_id in self.knew_id:
                    if knew_id == self.id:
                        wx.MessageBox(message="工号已存在，请重新输入", caption="警告")
                        # 重置self.id为ID_WORKER_UNAVIABLE，重新显示输入工号对话框
                        self.id = ID_WORKER_UNAVIABLE
                        break
                    else:
                        while self.name == '':
                            self.name = wx.GetTextFromUser(message="请输入您的的姓名,用于创建姓名文件夹",
                                                           caption="温馨提示",
                                                           default_value="", parent=self.bmp)
                            print(self.name)
                            # 判断语句 wx.GetTextFromUser函数点击cancel、对话框右上角×和值为空都是返回-1，因此当为-1时，提示用户后break,不break会一直循环弹出对话框提示用户输入
                            if self.name == "":
                                wx.MessageBox("请输入您的的姓名,完成姓名文件夹创建")
                                # 新建按钮可用，完成按钮不可用
                                self.new_register.Enable(True)
                                self.finish_register.Enable(False)
                                break
                            else:
                                # 监测是否重名
                                for exsit_name in (os.listdir(PATH_FACE)):
                                    if self.name == exsit_name:
                                        wx.MessageBox(message="姓名文件夹已存在，请重新输入", caption="警告")
                                        # 重置self.name为空，重新显示输入姓名对话框
                                        self.name = ''
                                        break
                                os.makedirs(PATH_FACE + self.name)
                                _thread.start_new_thread(self.register_cap, (event,))
                                pass

    # 完成注册 功能实现
    def OnFinishRegister(self):
        self.new_register.Enable(True)
        self.finish_register.Enable(False)
        # 释放摄像头
        self.cap.release()
        # 充值图片为pin_index
        self.bmp.SetBitmap(wx.Bitmap(self.pic_index))

        # 当录入同一人的人像数据时
        if self.flag_registed == True:
            dir = PATH_FACE + self.name
            for file in os.listdir(dir):
                os.remove(dir + "/" + file)
                print("已删除已录入人脸的图片", dir + "/" + file)
            os.rmdir(PATH_FACE + self.name)
            print("已删除已录入人脸的姓名文件夹", dir)
            self.initData()
            return

        if self.pic_num > 0:
            pics = os.listdir(PATH_FACE + self.name)
            feature_list = []
            feature_average = []
            # 分析录入分享的特征值
            for i in range(len(pics)):
                pic_path = PATH_FACE + self.name + "/" + pics[i]
                print("正在读的人脸图像：", pic_path)
                img = iio.imread(pic_path)
                img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                dets = detector(img_gray, 1)
                if len(dets) != 0:
                    shape = predictor(img_gray, dets[0])
                    face_descriptor = facerec.compute_face_descriptor(img_gray, shape)
                    feature_list.append(face_descriptor)
                else:
                    face_descriptor = 0
                    print("未在照片中识别到人脸")
            if len(feature_list) > 0:
                for j in range(128):
                    # 防止越界
                    feature_average.append(0)
                    for i in range(len(feature_list)):
                        feature_average[j] += feature_list[i][j]
                    feature_average[j] = (feature_average[j]) / len(feature_list)
                self.insertARow([self.id, self.name, feature_average], 1)
                self.infoText.AppendText("\r\n" + self.getDateAndTime() + "\r\n" + "工号:" + str(self.id)
                                         + " 姓名:" + self.name + " 的人脸数据已成功存入\r\n")
            pass

        else:
            os.rmdir(PATH_FACE + self.name)
            print("已删除空文件夹", PATH_FACE + self.name)
        self.initData()

    # 完成人脸录入 点击事件
    def OnFinishRegisterClicked(self, event):
        self.OnFinishRegister()
        pass

    # 人脸识别功能实现
    def punchcard_cap(self, event):
        self.cap = cv2.VideoCapture(0)
        # cap.set(propId, value)
        # 设置视频参数，propId设置的视频参数，value设置的参数值
        # self.cap.set(3, 600)
        # self.cap.set(4,600)
        # cap是否初始化成功
        while self.cap.isOpened():
            # cap.read()
            # 返回两个值：
            #    一个布尔值true/false，用来判断读取视频是否成功/是否到视频末尾
            #    图像对象，图像的三维矩阵
            flag, im_rd = self.cap.read()
            # 每帧数据延时1ms，延时为0读取的是静态帧
            kk = cv2.waitKey(1)
            # 人脸数 dets
            dets = detector(im_rd, 1)

            # 检测到人脸
            if len(dets) != 0:
                biggest_face = dets[0]
                # 取占比最大的脸
                maxArea = 0
                for det in dets:
                    w = det.right() - det.left()
                    h = det.top() - det.bottom()
                    if w * h > maxArea:
                        biggest_face = det
                        maxArea = w * h
                        # 绘制矩形框

                cv2.rectangle(im_rd, tuple([biggest_face.left(), biggest_face.top()]),
                              tuple([biggest_face.right(), biggest_face.bottom()]),
                              (255, 0, 255), 2)
                img_height, img_width = im_rd.shape[:2]
                image1 = cv2.cvtColor(im_rd, cv2.COLOR_BGR2RGB)
                pic = wx.Bitmap.FromBuffer(img_width, img_height, image1)
                # 显示图片在panel上
                self.bmp.SetBitmap(pic)

                # 获取当前捕获到的图像的所有人脸的特征，存储到 features_cap_arr
                shape = predictor(im_rd, biggest_face)
                features_cap = facerec.compute_face_descriptor(im_rd, shape)

                # 对于某张人脸，遍历所有存储的人脸特征
                for i, knew_face_feature in enumerate(self.knew_face_feature):
                    # 将某张人脸与存储的所有人脸数据进行比对
                    compare = return_euclidean_distance(features_cap, knew_face_feature)
                    if compare == "same":  # 找到了相似脸
                        print("same")
                        flag = 0

                        nowdt = self.getDateAndTime()
                        self.infoText.AppendText("\r\n" + nowdt + "\r\n" + "工号:" + str(self.knew_id[i])
                                                 + " 姓名:" + self.knew_name[i] + " 门已开，请进\r\n")
                        self.insertARow([self.knew_id[i], self.knew_name[i], nowdt], 2)
                        self.loadDataBase(2)
                        break

                if self.start_punchcard.IsEnabled():
                    self.bmp.SetBitmap(wx.Bitmap(self.pic_index))
                    _thread.exit()

    # 开始人脸识别 点击事件
    def OnStartPunchCardClicked(self, event):
        self.start_punchcard.Enable(False)
        self.end_puncard.Enable(True)
        self.loadDataBase(2)
        _thread.start_new_thread(self.punchcard_cap, (event,))
        pass

    # 停止人脸识别 点击事件
    def OnEndPunchCardClicked(self, event):
        self.start_punchcard.Enable(True)
        self.end_puncard.Enable(False)
        # 停止人脸识别，释放摄像头
        self.cap.release()
        pass

    # 初始化 左侧信息提示功能
    def initInfoText(self):
        # 少了这两句infoText背景颜色设置失败，莫名奇怪
        resultText = wx.StaticText(parent=self, pos=(10, 20), size=(90, 60))
        resultText.SetBackgroundColour('red')

        self.info = "\r\n" + self.getDateAndTime() + "\r\n" + "程序初始化成功\r\n"
        # 第二个参数水平混动条
        self.infoText = wx.TextCtrl(parent=self, size=(320, 500),
                                    style=(wx.TE_MULTILINE | wx.HSCROLL | wx.TE_READONLY))
        # 前景色，也就是字体颜色
        self.infoText.SetForegroundColour("ORANGE")
        self.infoText.SetLabel(self.info)
        # API:https://www.cnblogs.com/wangjian8888/p/6028777.html
        # 没有这样的重载函数造成"par is not a key word",只好Set
        font = wx.Font()
        font.SetPointSize(12)
        font.SetWeight(wx.BOLD)
        font.SetUnderlined(True)

        self.infoText.SetFont(font)
        self.infoText.SetBackgroundColour('TURQUOISE')
        pass

    # 初始化 右侧图像部分 功能
    def initGallery(self):
        self.pic_index = wx.Image("drawable/index.png", wx.BITMAP_TYPE_ANY).Scale(600, 500)
        self.bmp = wx.StaticBitmap(parent=self, pos=(320, 0), bitmap=wx.Bitmap(self.pic_index))
        pass

    # 获得当前日期和时间
    def getDateAndTime(self):
        dateandtime = strftime("%Y-%m-%d %H:%M:%S", localtime())
        return "[" + dateandtime + "]"

    # 数据库部分
    # 初始化数据库
    def initDatabase(self):
        conn = sqlite3.connect("facesystem.db")  # 建立数据库连接
        cur = conn.cursor()  # 得到游标对象
        cur.execute('''create table if not exists worker_info
            (id int not null primary key,
            name text not null,
            face_feature array not null)''')
        cur.execute('''create table if not exists logcat
             (num INTEGER primary key autoincrement,
             id int not null,
             name text not null,
             datetime text not null)''')
        cur.close()
        conn.commit()
        conn.close()

    # 实现数据库插入功能（这里是一次插入一条数据，也可以一条数据的各字段）
    def insertARow(self, Row, type):
        conn = sqlite3.connect("facesystem.db")  # 建立数据库连接
        cur = conn.cursor()  # 得到游标对象

        # 写人像数据表
        if type == 1:
            cur.execute("insert into worker_info (id,name,face_feature) values(?,?,?)",
                        (Row[0], Row[1], deal_data.adapt_array(Row[2])))
            print("写人脸数据成功")

        # 写日志数据表
        if type == 2:
            cur.execute("insert into logcat (id,name,datetime) values(?,?,?)",
                        (Row[0], Row[1], Row[2]))
            print("写日志成功")
            pass
        cur.close()
        conn.commit()
        conn.close()
        pass

    # 加载数据库
    def loadDataBase(self, type):
        conn = sqlite3.connect("facesystem.db")  # 建立数据库连接
        cur = conn.cursor()  # 得到游标对象

        # 加载人像数据表
        if type == 1:
            self.knew_id = []
            self.knew_name = []
            self.knew_face_feature = []
            cur.execute('select id,name,face_feature from worker_info')
            origin = cur.fetchall()
            for row in origin:
                print(row[0])
                self.knew_id.append(row[0])
                print(row[1])
                self.knew_name.append(row[1])
                print(deal_data.convert_array(row[2]))
                self.knew_face_feature.append(deal_data.convert_array(row[2]))

        # 加载日志表
        if type == 2:
            self.logcat_num = []
            self.logcat_id = []
            self.logcat_name = []
            self.logcat_datetime = []
            cur.execute('select num,id,name,datetime from logcat')
            origin = cur.fetchall()
            self.num_of_logcat = len(origin)
            for row in origin:
                print(row[0])
                self.logcat_num.append(row[0])
                print(row[1])
                self.logcat_id.append(row[1])
                print(row[2])
                self.logcat_name.append(row[2])
                print(row[3])
                self.logcat_datetime.append(row[3])
        pass


app = wx.App()
frame = WAS()
frame.Show()
app.MainLoop()
