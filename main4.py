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

def train_model(df, algo):
    x_train, x_test, y_train, y_test = split_df(df)
    model = algo.fit(x_train, y_train)
    return model, model.score(x_test, y_test)

def evaluate(df, model, m=100, threshold=50):
    """
    Iterate over m first rows and evaluate trades.
    Trades only if price move more than the threshold.

    """
    df = df.loc[:m]
    buy_prices = list()
    sell_prices = list()
    tot_error = int()
    for index, row in df.iterrows():
        x = row.head(df.shape[1]-1)
        y = row.tail(1).to_list()[0]
        x_decision = row.tail(2).to_list()[0]

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
        return (((average_sell_price / average_buy_price) - 1) * 100), tot_error / m
    else:
        average_buy_price = 0
        average_sell_price = 0
        return 0, tot_error / m

def train_algo(algo, k, n):
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
    m = new_df.size # evaluate with the m first rows

    tot_pnl = int() # total profit and loss
    tot_score = int()
    tot_error = int()
    # train several models
    for i in range(k):
        model, score = train_model(new_df, algo)
        tot_score += score
        pnl, error = evaluate(new_df, model, m)
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

def main(algos, k_range=(10, 40), n_range=(4, 100)):
    tries = list()
    for algo in algos:
        for k in range(k_range[0], k_range[1]):
            for n in range(n_range[0], n_range[1]):
                algo_name, pnl, score, error = train_algo(algo, k, n)
                tries.append(((algo, k, n), (algo_name, pnl, score, error)))

    max_pnl = int()
    max_pnl_config = None
    min_error = math.inf
    min_error_config = None
    for result in tries:
        if DEBUG:
            print(result)
        if max_pnl < result[1][1]:
            max_pnl = result[1][1]
            max_pnl_config = result
        if min_error > result[1][3]:
            min_error = result[1][3]
            min_error_config = result
    return min_error_config, max_pnl_config

if __name__ == '__main__':
    b = time.time()
    # k: number of repetition
    # n: number of days in each row
    algos = list()
    algos.append(linear_model.LinearRegression())
    k_ = 200
    min_error_config, max_pnl_config = main(algos, k_range=(k_, k_+1), n_range=(237, 273))
    print()
    print(min_error_config)
    print(max_pnl_config)
    print(time.time() - b)
    """
((LinearRegression(copy_X=True, fit_intercept=True, n_jobs=None, normalize=False), 200, 250), ('LinearRegression', 54.169102067963614, -26.177404755210638, 0.00021548993044429528))
((LinearRegression(copy_X=True, fit_intercept=True, n_jobs=None, normalize=False), 200, 267), ('LinearRegression', 811.2526366303829, -3.079701960845952, 0.01576299268038821))
54.55777025222778
    """
