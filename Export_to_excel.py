import xlwt
import sqlite3

def export_excel(table_name,type):
    conn = sqlite3.connect("facesystem.db")
    cur = conn.cursor()

    book = xlwt.Workbook()  # 先创建一个book

    #根据传参决定导出资料
    if type == 255:
        sql = 'select * from logcat'
        sheet = book.add_sheet('进出日志')  # 创建一个进出日志sheet表
    if type == 256:
        sql = 'select * from worker_info'
        sheet = book.add_sheet('人员信息')  # 创建一个人员信息sheet表

    cur.execute(sql)
    fileds = [filed[0] for filed in cur.description]  # 列表生成式，所有字段
    all_data = cur.fetchall()  # 所有数据

    # 写excel
    # enumerate自动计算下标
    for col, field in enumerate(fileds):
        sheet.write(0, col, field)

    # 从第一行开始写
    row = 1  # 行数
    for data in all_data:  # 二维数据，有多少条数据，控制行数
        for col, field in enumerate(data):  # 控制列数
            sheet.write(row,col,field)
        row += 1 #每次写完一行，行数加1
    book.save('data/%s.xls' % table_name)  # 保存excel文件

#export_excel('进出历史')