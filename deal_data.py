import sqlite3
import io
import zlib
import numpy as np  # 数据处理的库numpy

def adapt_array(arr):
    """
    函数功能：将特征列表转换为二进制数据流数据，为存入数据库做准备
    :param arr: 特征列表：feature_average
    :return: 二进制流格式数据
    """
    out = io.BytesIO()
    np.save(out, arr)
    out.seek(0)

    dataa = out.read()
    # 压缩数据流
    return sqlite3.Binary(zlib.compress(dataa, zlib.Z_BEST_COMPRESSION))


def convert_array(text):
    """
    函数：将从数据库中取出的特征二进制数据流转换为列表，为之后的应用做准备
    :param text: 特征二进制流数据
    :return: 特征列表
    """
    out = io.BytesIO(text)
    out.seek(0)

    dataa = out.read()
    # 解压缩数据流
    out = io.BytesIO(zlib.decompress(dataa))
    return np.load(out)