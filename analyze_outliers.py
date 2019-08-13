import pandas as pd
import matplotlib.pyplot as plt
import os
from tukey_test import *
from collections import defaultdict
import logging


class Outliers:
    # 离群点类，存放离群点异常值，离群点索引值与离群点相关的统计列表
    def __init__(self):
        self.outliers_indexs = []
        self.outliers_values = []
        self.ts = []
        self.ids = []
        self.ts_count = defaultdict(lambda: 0)
        self.ts_count_float = defaultdict(lambda: 0)
        self.ids_count = defaultdict(lambda: 0)
        self.ids_count_float = defaultdict(lambda: 0)

    def get_outliers_values(self, data):
        # 获取异常值，送到tukeyTest接口
        self.outliers_values.extend(calc_tukey_get_anomaly_data(data, 10, sort_flag=True, factor=3))

    def get_outliers_port_index(self, csv_df, outlier_values):
        # 根据最初的csv_df，与获取到的异常值，获取异常索引
        for value in outlier_values:
            index = csv_df[csv_df['thrput_ratio'] == value].index.values
            self.outliers_indexs.append(index)

    def get_outliers_dance_ids(self, csv_df):
        # 获取异常的action切换元组
        for i in self.outliers_indexs:
            if not i:
                continue
            # print(csv_df['ts'][i[0]])
            self.ts.append(int(csv_df['ts'][i]))
            if i - 2 >= 0:
                self.ids.append((int(csv_df['action_id'][i - 2]), int(csv_df['action_id'][i - 1])))
            else:
                continue
        return self.ids

    def get_anomaly_ids_count(self):
        # 获取异常数据的action切换元组的统计信息
        for id_pair in self.ids:
            self.ids_count[id_pair] += 1
        self.ids_count = dict(sorted(self.ids_count.items(), key=lambda x: x[1], reverse=True))
        for k, v in self.ids_count.items():
            self.ids_count_float[k] = float('%.2f' % (v / len(self.ids)))
        return self.ids_count, dict(self.ids_count_float)

    def get_anomaly_ts_count(self):
        # 获取异常数据的ts统计信息
        for ts in self.ts:
            self.ts_count[ts // 1000] += 1

        self.ts_count = dict(sorted(self.ts_count.items(), key=lambda x: x[1], reverse=True))
        for k, v in self.ts_count.items():
            self.ts_count_float[k] = float('%.2f' % (v / len(self.ids)))
        return self.ts_count, dict(self.ts_count_float)


def csv_file_to_df(csv_path):
    # 读取csv文件并转化为Python中的数据框即DataFrame类型
    csv_file = csv_path
    csv_data = pd.read_csv(csv_file, low_memory=False)
    csv_df = pd.DataFrame(csv_data)
    return csv_df


def get_sorted_port_df(csv_df, port_name):
    # 获取通过端口号筛选且根据action_id进行合并排序（稳定排序）的df
    df_port = csv_df.loc[csv_df["port"] == port_name]
    # ini_port_df = deepcopy(df_port)
    df_port.index = list(range(len(df_port)))
    lyst = list(df_port['action_id'])
    for i in range(len(lyst) - 1, 0, -1):
        lyst[i] = lyst[i - 1]
    lyst[0] = 0
    df_port['action_id'] = pd.Series(lyst)
    sorted_df = df_port.sort_values(by='action_id', kind='mergesort')
    # return ini_port_df, sorted_df
    return sorted_df


def subplot_port_throughput(sorted_df, port_name, scene_name):
    # 画出子图的throughput变化折线图
    x = list(range(len(sorted_df)))
    y = list(sorted_df['thrput_ratio'])
    plt.plot(x, y, color='b', label="thrput_ratio")  # o-:圆形
    plt.xlabel("action_id")  # 横坐标名字
    plt.ylabel("thrput_ratio")  # 纵坐标名字
    plt.ylim(0, 1.2)
    plt.title(port_name + " thrput_ratio " + scene_name)
    plt.legend(loc="best")  # 图例


def save_port_figure_and_excel(num_subplot, sorted_df_list, name_list, scene_name, excel_name):
    # 保存场景折线图与场景-端口号excel
    # 调整图片大小以获得最大化效果
    plt.figure(figsize=(20, 10))
    # 写一张新的excel表格，表格中根据拥塞端口数分为相应的sheet
    writer = pd.ExcelWriter(excel_name)
    for num, sorted_df, name in zip(num_subplot, sorted_df_list, name_list):
        plt.subplot(2, 3, num)
        subplot_port_throughput(sorted_df, name, scene_name)
        # 'output.xlsx'
        sheet_name = name.replace('/', '-')

        sorted_df.to_excel(writer, sheet_name)
    writer.save()
    plt.savefig("figures/" + scene_name + ".png")


def generate_outliers_analysis_log(file_list, log_path):
    '''
    :param file_list: 待输入的csv文件列表
    :param log_path:  指定异常分析日志的输出路径
    :return:
    '''
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(filename=log_path, level=logging.DEBUG, format=LOG_FORMAT)
    for file in file_list:
        out = Outliers()
        csv_df = csv_file_to_df(r"D:/FTPD/newEnv/" + str(file) + ".csv")
        port_suffix = [33, 35, 36, 37, 39, 40]
        for suffix in port_suffix:
            # 通过执行字符串代码来避免反复执行相同语句
            exec("sorted_df_%s =  get_sorted_port_df(csv_df, '25GE1/0/%s')" % (str(suffix), str(suffix)))
            exec("out.get_outliers_values(sorted_df_%s['thrput_ratio'])" % str(suffix))

        out.get_outliers_port_index(csv_df, out.outliers_values)
        dance_ids = out.get_outliers_dance_ids(csv_df)
        print(len(dance_ids))
        # 在日志中记录对应场景的ActionID跳转情况，以检测是否由于ECN水线调整引发的问题
        ids_count, ids_count_float = out.get_anomaly_ids_count()
        logging.info(str(file) + " ids_count       {}".format(ids_count))
        logging.info(str(file) + " ids_count_float {}".format(ids_count_float))
        # 在日志中记录对应场景不同拥塞端口的异常值的ts，以检测是否在同一时刻发生，即是否是网络波动引起的异常值。
        ts_count, ts_count_float = out.get_anomaly_ts_count()
        logging.info(str(file) + " ts_count        {}".format(ts_count))
        logging.info(str(file) + " ts_count_float  {}".format(ts_count_float))


def generate_csvfile(df, file_name):
    if os.path.exists(file_name):
        print("The file {} exists.Will remove it first...".format(file_name))
        os.remove(file_name)
    if not df.to_csv(file_name, index=0):
        print("Output the csv.")
        num_of_lines = len(["" for line in open(file_name, "r")])
        print("The number of {} Lines is:{}".format(file_name, num_of_lines))
        return num_of_lines


if __name__ == '__main__':
    file_list = [2014, 2045, 2065, 2070, 2080, 2110, 2123, 2133]
    generate_outliers_analysis_log(file_list, "log/outliers.log")

    for file in file_list:
        csv_df = csv_file_to_df(r"D:/FTPD/newEnv/" + str(file) + ".csv")
        port_suffix = [33, 35, 36, 37, 39, 40]
        for suffix in port_suffix:
            # 通过执行字符串代码来避免反复执行相同语句
            exec("sorted_df_%s =  get_sorted_port_df(csv_df, '25GE1/0/%s')" % (str(suffix), str(suffix)))
        sorted_df_list = [sorted_df_33, sorted_df_35, sorted_df_36, sorted_df_37, sorted_df_39, sorted_df_40]
        name_list = ["25GE1/0/33", "25GE1/0/35", "25GE1/0/36", "25GE1/0/37", "25GE1/0/39", "25GE1/0/40"]
        save_port_figure_and_excel(range(1, 7), sorted_df_list, name_list, str(file), 'port_csv/' + str(file) + '.xlsx')