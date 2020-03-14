import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from tukey_test import csv_file_to_df
from collections import defaultdict

# 背景说明：在ceph存储场景下，动态Ecn2.0的调优效果不如纯AI，利用此代码绘制Kmax时序图，拥塞端口吞吐率时序图，Kmax与拥塞端口混合时序图。
# 借以分析
# 用于绘制某个端口的某一项指标数据
def subplot_port_stats(sorted_df, port_name, scene_name, stats_name):
    # 画出子图的throughput变化折线图
    x = list(range(len(sorted_df)))
    # y = list(np.array(sorted_df[stats_name]) / (25 * 1000000000.0))
    if stats_name == "throughput":
        y = list(np.array(sorted_df[stats_name]) / (25 * 1000000000.0))
    else:
        y = list(sorted_df[stats_name])
    plt.plot(x, y, color='b', label=stats_name)  # o-:圆形
    plt.xlabel("time series/s")  # 横坐标名字
    plt.ylabel(stats_name)  # 纵坐标名字
    # plt.ylim(0, 1.2)
    plt.title(port_name + ' ' + stats_name + ' ' + scene_name)
    plt.legend(loc="best")  # 图例


def save_port_figure_and_excel(num_subplot, sorted_df_list, name_list, scene_name, excel_name, stats_name):
    # 保存场景折线图与场景-端口号excel
    # 调整图片大小以获得最大化效果
    plt.figure(figsize=(20, 10))
    # 写一张新的excel表格，表格中根据拥塞端口数分为相应的sheet
    writer = pd.ExcelWriter(excel_name)
    for num, sorted_df, name in zip(num_subplot, sorted_df_list, name_list):
        plt.subplot(2, 3, num)
        subplot_port_stats(sorted_df, name, scene_name, stats_name)
        # 'output.xlsx'
        sheet_name = name.replace('/', '-')

        sorted_df.to_excel(writer, sheet_name)
    writer.save()
    plt.savefig(r"D:/FTPD/analyze/figures/" + scene_name + "_" + stats_name + ".png")


def get_port_df(csv_df, port_name):
    #     直接获取对应的单个端口的吞吐率
    df_port = csv_df.loc[csv_df["port"] == port_name]
    df_port.index = list(range(len(df_port)))
    lyst = list(df_port['throughput'])
    for i in range(len(lyst) - 2):
        lyst[i] = lyst[i + 1]
    lyst[len(lyst) - 1] = lyst[len(lyst) - 2]
    df_port['throughput'] = pd.Series(lyst)
    return df_port


def get_down_triple(csv_df, triple: list):
    length = len(csv_df)
    for i in range(1, length):
        # if csv_df["Kmax"][i] < csv_df["Kmax"][i - 1]:
        if csv_df["Kmin"][i] < csv_df["Kmin"][i - 1]:
            triple.append((int(csv_df["preStates"][i]), int(csv_df["curStates"][i]), int(csv_df["event"][i])))


def tuple_count(lyst):
    count_dict = defaultdict(lambda: 0)
    count_dict_float = defaultdict(lambda: 0)
    for item in lyst:
        count_dict[item] += 1
    count_dict = dict(sorted(count_dict.items(), key=lambda x: x[1], reverse=True))
    sum1 = sum(count_dict.values())
    for k, v in count_dict.items():
        count_dict_float[k] = float('%.2f' % (v / sum1))
    return count_dict, dict(count_dict_float)


def subplot_port_stats_double(sorted_df, port_name, scene_name, ax):
    # 画出子图的throughput变化折线图
    # x = list(range(len(sorted_df)))[120:141]
    x = list(range(len(sorted_df)))[200:251]
    th = list(np.array(sorted_df["throughput"]) / (25 * 1000000000.0))[200:251]
    kmax = list(sorted_df["DropProb"])[200:251]
    if len(x) <= 60:
        ax.plot(x, th, color='b', marker='o', label="th")  # o-:圆形
    else:
        ax.plot(x, th, color='b', label="th")  # o-:圆形
    ax.set_ylabel("port throughput")  # 纵坐标名字
    ax.set_title(port_name + " th_DropProb " + scene_name)

    ax_twin = ax.twinx()
    if len(x) <= 60:
        ax_twin.plot(x, kmax, color='r', marker='o', label="DropProb")
    else:
        ax_twin.plot(x, kmax, color='r', label="DropProb")
    ax_twin.set_ylabel("DropProb")
    ax_twin.set_xlabel("time series for th and DropProb/s")
    plt.legend(loc="best")  # 图例


def save_port_figure_double(num_subplot, sorted_df_list, name_list, scene_name):
    fig = plt.figure(figsize=(24, 10))
    for num, sorted_df, name in zip(num_subplot, sorted_df_list, name_list):
        axis = fig.add_subplot(2, 3, num)
        subplot_port_stats_double(sorted_df, name, scene_name, axis)
    plt.savefig(r"D:/FTPD/analyze/figures/" + scene_name + " th_drop(200-250) " + ".png")


def plot_independent_figures():
    file_list = [3080, 3081]

    for file in file_list:
        csv_df = csv_file_to_df(r"D:/FTPD/analyze/initialLog/aiecn_" + str(file) + "_1.csv")
        port_suffix = [1, 3, 4, 5, 7, 8]
        loc = locals()
        for suffix in port_suffix:
            # 通过执行字符串代码来避免反复执行相同语句
            exec("sorted_df_%s =  get_port_df(csv_df, 'dynEcn: 25GE1/0/%s')" % (str(suffix), str(suffix)))
        # sorted_df_1 = get_port_df(csv_df, 'dynEcn: 25GE1/0/1')
        df_1, df_3, df_4 = loc["sorted_df_1"], loc["sorted_df_3"], loc["sorted_df_4"]
        df_5, df_7, df_8 = loc["sorted_df_5"], loc["sorted_df_7"], loc["sorted_df_8"]
        sorted_df_list = [df_1, df_3, df_4, df_5, df_7, df_8]
        name_list = ["25GE1/0/1", "25GE1/0/3", "25GE1/0/4", "25GE1/0/5", "25GE1/0/7", "25GE1/0/8"]
        stats = ["throughput", "Kmin", "Kmax"]
        for stat in stats:
            save_port_figure_and_excel(range(1, 7), sorted_df_list, name_list, str(file),
                                       'D:/FTPD/analyze/port_csv/' + str(file) + '.xlsx', stat)


def plot_double_y_axis_figurs():
    file_list = [3080, 3081]

    triple = []
    for file in file_list:
        csv_df = csv_file_to_df(r"D:/FTPD/analyze/initialLog/aiecn_" + str(file) + "_1.csv")
        port_suffix = [1, 3, 4, 5, 7, 8]
        loc = locals()
        for suffix in port_suffix:
            # 通过执行字符串代码来避免反复执行相同语句
            exec("sorted_df_%s =  get_port_df(csv_df, 'dynEcn: 25GE1/0/%s')" % (str(suffix), str(suffix)))
        # sorted_df_1 = get_port_df(csv_df, 'dynEcn: 25GE1/0/1')
        df_1, df_3, df_4 = loc["sorted_df_1"], loc["sorted_df_3"], loc["sorted_df_4"]
        df_5, df_7, df_8 = loc["sorted_df_5"], loc["sorted_df_7"], loc["sorted_df_8"]
        sorted_df_list = [df_1, df_3, df_4, df_5, df_7, df_8]
        name_list = ["25GE1/0/1", "25GE1/0/3", "25GE1/0/4", "25GE1/0/5", "25GE1/0/7", "25GE1/0/8"]
        # stats = ["throughput", "Kmin", "Kmax"]
        stats = ["th_kmin"]
        save_port_figure_double(range(1, 7), sorted_df_list, name_list, str(file))
    #     for df in sorted_df_list:
    #         get_down_triple(df, triple)
    # count1, count2 = tuple_count(triple)
    # # print(triple)
    # print("Kmin down triplets:")
    # print(count1)
    # print(count2)


if __name__ == '__main__':
    # plot_independent_figures()
    plot_double_y_axis_figurs()