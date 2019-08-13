import pandas as pd
from parseSnapAnomaly.anomalyDataParseAndContrast import *


def parse_values(values, q1, q3, factor):
    fence1 = q1 - factor * (q3 - q1)
    fence2 = q3 + factor * (q3 - q1)
    # print("fence1: ", fence1, "fence2: ", fence2)
    assert fence1 <= fence2
    outliers = []
    value = []
    for (i, v) in enumerate(values):
        # if (v < fence1 or v > fence2) and v < 0.64:
        if v < fence1 or v > fence2:
            value.append(v)
            outliers.append(i)
    if len(outliers) != 0:
        return value, outliers

    return value, outliers


def get_outliers(values, factor, sort_index):
    length = len(values)
    l = sort_index
    if length % 2 == 0:
        # print("q1 index:{} q3 index:{}".format(l[length // 4], l[3 * length // 4]))
        q1 = values[l[length // 4]]
        q3 = values[l[3 * length // 4]]
        # print("q1: " + str(q1) + " q3: " + str(q3))
        assert q1 <= q3
        return parse_values(values, q1, q3, factor)
    i = values[l[length // 4]]
    j = values[l[length // 4 + 1]]
    q1 = i + (j - i) * 0.25
    i = values[l[3 * length // 4 - 1]]
    j = values[l[3 * length // 4]]
    q3 = i + (j - i) * 0.75
    # print("q1 index:{} q3 index:{}".format(l[length // 4], l[3 * length // 4]))
    assert q1 <= q3
    return parse_values(values, q1, q3, factor)


def anomaly_detection(values, factor, bufLength, sort_index):
    if len(values) != bufLength:
        raise RuntimeError("the length of values is not bufLength!")

    _, anomaly = get_outliers(values, factor, sort_index)
    # print("anomaly_index:{}".format(anomaly))
    return anomaly


def csv_file_to_df(csv_path):
    csv_file = csv_path
    csv_data = pd.read_csv(csv_file, low_memory=False)
    csv_df = pd.DataFrame(csv_data)
    return csv_df


# 如果数据读到末尾，数据的条目达不到bufLength的长度，那么剩下的长度的数据用之前数据的均值来填充
def fill_data(raw_data, bufLength):
    mod = len(raw_data) % bufLength
    if mod != 0:
        fill_length = bufLength - mod
        mean = np.mean(raw_data)
        for i in range(fill_length):
            raw_data.append(mean)
        return raw_data
    else:
        return raw_data


# 获取异常值元素在切片中的索引时，根据sort_flag来决定是否需要对传入的数据列表进行排序
def calc_tukey_get_anomaly_data(raw_total_value, buf_length, sort_flag=True, factor=1.5):
    i = 0
    anomaly_values = []
    raw_total_value = list(map(float, raw_total_value))
    # 将异常数组初始化为全0元素
    # anomaly_values = [0 for l in range(len(raw_total_value))]
    # while循环10个一组检测异常值
    while i < len(raw_total_value):
        values = fill_data(raw_total_value[i:i + buf_length], buf_length)
        if sort_flag:
            # 根据数值大小将索引进行排序
            sort_index = sorted(range(len(values)), key=lambda k: values[k])
        else:
            sort_index = [x for x in range(len(values))]
        # print("sort_index:{}".format(sort_index))
        # print("sorted values:{}".format(sorted(values)))
        # values = sorted(values)
        length = len(values)
        anomaly_index = anomaly_detection(values, bufLength=length, factor=factor, sort_index=sort_index)

        for n in anomaly_index:
            # anomaly_values是和原本的输入数组相同长度的数组，value是中间过程中以10为长度的数组
            anomaly_values.append(values[n])
        i += buf_length
    print("anomaly_values:{}".format(anomaly_values))
    print("value's len:{}".format(len(anomaly_values)))
    return anomaly_values


if __name__ == '__main__':
    # tukeyTest 异常检测算法的测试程序
    cpu_wave_df = csv_file_to_df(
        r'C:\Users\w00475279\AppData\Roaming\eSpace_Desktop\UserData\w00475279\ReceiveFile\osamoafwhw05(10.125.141.197) - Traffic - GigabitEthernet3_0_8.csv')
    cpu_value = list(cpu_wave_df['In'])
    # 随机试验
    # print(cpu_value[90:100])
    # import random
    # cpu_value = [random.randint(1, 95) for i in range(1000)]

    bins1 = bins2 = [i for i in range(len(cpu_value))]
    anomaly_data = calc_tukey_get_anomaly_data(cpu_value, 10, sort_flag=True, factor=1.5)

    plot_contrast_bar(bins1, cpu_value, bins2, anomaly_data, "A FWHW 05 TrafficIn", "Sorted")
    calc_compression(cpu_value, anomaly_data)