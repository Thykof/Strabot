from sklearn import tree, svm, gaussian_process, linear_model, isotonic
from sklearn.model_selection import train_test_split
import pandas
import math
import statistics
import matplotlib.pyplot as plt
import time

DEBUG = True

def raw_data_to_numeric(raw_data):
    data = raw_data.replace(' ', '')
    data = data.replace(',', '.')
    return float(data)

def split_df(df, test_size=0.2):
    n = df.shape[1]
    x = df.iloc[:,:n-1]
    y = df.iloc[:,n-1]
    return train_test_split(x, y, test_size=test_size)

def evaluate(df_tuple, model, threshold):
    """Trades only if price move more than the threshold."""
    x_test, y_test = df_tuple
    buy_prices = list()
    sell_prices = list()
    tot_error = int()
    n = df_tuple[0].shape[0]
    for i in range(n):
        x = x_test.iloc[i]
        y = y_test.iloc[i]
        x_decision = x.iloc[-1]

        prediction = model.predict([x])[0]
        error = abs(prediction - y)
        # evaluate trade
        if abs(x_decision - prediction) > threshold:
            if prediction > x_decision:
                # buy
                buy_prices.append(x_decision)
                if y > prediction:
                    sell_prices.append(prediction)
            else:
                # sell
                sell_prices.append(x_decision)
                if y < prediction:
                    buy_prices.append(prediction)

        # calculate error
        tot_error += error

    # end of for loop
    if len(buy_prices) and len(sell_prices):
        average_buy_price = statistics.mean(buy_prices)
        average_sell_price = statistics.mean(sell_prices)
        return (((average_sell_price / average_buy_price) - 1) * 100), tot_error / n
    else:
        average_buy_price = 0
        average_sell_price = 0
        return 0, tot_error / n

def train_algo(algo, k, n, threshold):
    """
    Create row of n days.
    Train and test k models.
    """
    algo_name = str(algo)[:str(algo).find('(')]
    df = pandas.read_csv("bitcoin-price-all.csv", sep=';')
    # df = df.loc[:99]
    df = df[['Close**']]
    df = df.applymap(raw_data_to_numeric)
    new_df_list = list()
    # create rows with n close price, i.e. n days
    for label, content in df.items():
        row = list()
        i = 0
        for item in content:
            row.append(item)
            i += 1
            if i >= n:
                new_df_list.append(row)
                # plt.plot(row)
                # plt.show()
                # input()
                row = list()
                i = 0
    new_df = pandas.DataFrame(new_df_list)

    tot_pnl = int() # total profit and loss
    tot_score = int()
    tot_error = int()
    # train several models
    for i in range(k):
        x_train, x_test, y_train, y_test = split_df(new_df)
        model = algo.fit(x_train, y_train)
        tot_score += model.score(x_test, y_test)
        # pnl, error = evaluate(new_df, model)
        pnl, error = evaluate((x_test, y_test), model, threshold)
        tot_pnl += pnl
        tot_error = error
    pnl = tot_pnl / k
    score = tot_score / k
    error = tot_error / k
    # if DEBUG:
    #     print(algo_name)
    #     print('pnl:   ' + str(pnl))
    #     print('score: ' + str(score))
    #     print('error: ' + str(error))
    #     print()
    return algo_name, pnl, score, error

def main(algos, k_range=(10, 40), n_range=(4, 100), threshold=50):
    tries = list()
    for algo in algos:
        for k in range(k_range[0], k_range[1]):
            for n in range(n_range[0], n_range[1]):
                algo_name, pnl, score, error = train_algo(algo, k, n, threshold)
                tries.append(((algo, k, n), (algo_name, pnl, score, error)))

    max_pnl = 0
    max_pnl_config = None
    min_error = math.inf
    min_error_config = None
    max_score = 0
    max_score_config = None
    for result in tries:
        if DEBUG:
            print(result)
        if max_pnl < result[1][1]:
            max_pnl = result[1][1]
            max_pnl_config = result
        if min_error > result[1][3]:
            min_error = result[1][3]
            min_error_config = result
        if max_score < result[1][2]:
            max_score = result[1][2]
            max_score_config = result
    return min_error_config, max_pnl_config, max_score_config

if __name__ == '__main__':
    b = time.time()
    # k: number of repetition
    # n: number of days in each row
    algos = list()
    algos.append(linear_model.LinearRegression())
    k_ = 50
    threshold = 20
    min_error_config, max_pnl_config, max_score_config = main(algos, k_range=(k_, k_+1), n_range=(5, 25), threshold=threshold)
    print()
    print(min_error_config)
    print(max_pnl_config)
    print(max_score_config)
    print(time.time() - b)
    """
((LinearRegression(copy_X=True, fit_intercept=True, n_jobs=None, normalize=False), 50, 24), ('LinearRegression', 72.89835528418281, 0.9864903910464595, 1.431114771854653))
((LinearRegression(copy_X=True, fit_intercept=True, n_jobs=None, normalize=False), 50, 8), ('LinearRegression', 170.68796262633748, 0.9897190268544935, 3.7451735321168513))
((LinearRegression(copy_X=True, fit_intercept=True, n_jobs=None, normalize=False), 50, 9), ('LinearRegression', 29.91841178805823, 0.9953372053890338, 2.282855057393496))
13.589125871658325
    """
