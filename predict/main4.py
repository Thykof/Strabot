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

def split_df(df, p, test_size=0.2):
    x = df.iloc[:,:p]
    y = df.iloc[:,df.shape[1]-1]
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
                if y > prediction:
                    # buy
                    buy_prices.append(x_decision)
                    sell_prices.append(prediction)
            else:
                if y < prediction:
                    # sell
                    sell_prices.append(x_decision)
                    buy_prices.append(prediction)

        # calculate error
        tot_error += error

    # end of for loop
    if len(buy_prices) and len(sell_prices):
        average_buy_price = statistics.mean(buy_prices)
        average_sell_price = statistics.mean(sell_prices)
        return (((average_sell_price / average_buy_price) - 1) * 100), tot_error / n
    else:
        return 0, tot_error / n

def train_algo(df, algo, k, n, p, threshold):
    """
    Create row of n days.
    Train and test k models.
    """
    df_list = list()
    # create rows with n close price, i.e. n days
    for label, content in df.items():
        row = list()
        i = 0
        for item in content:
            row.append(item)
            i += 1
            if i >= n:
                df_list.append(row)
                # plt.plot(row); plt.show(); input()
                row = list()
                i = 0
    df = pandas.DataFrame(df_list)

    tot_pnl = int() # total profit and loss
    tot_score = int()
    tot_error = int()
    # train several models
    for i in range(k):
        x_train, x_test, y_train, y_test = split_df(df, p)
        model = algo.fit(x_train, y_train)
        tot_score += model.score(x_test, y_test)
        pnl, error = evaluate((x_test, y_test), model, threshold)
        tot_pnl += pnl
        tot_error = error
    pnl = tot_pnl / k
    score = tot_score / k
    error = tot_error / k
    return pnl, score, error

def main(algos, k_range=(10, 40), n_range=(4, 100), p_min_max=None, threshold=3):
    tries = list()
    df = pandas.read_csv("bitcoin-price-all.csv", sep=';')
    df = df[['Close**']]
    df = df.applymap(raw_data_to_numeric)
    for algo in algos:
        for k in range(k_range[0], k_range[1]):
            for n in range(n_range[0], n_range[1]):
                for p in range(1, n+1):
                    if p_min_max is not None and not (p_min_max[0] <= p and p <= p_min_max[1]):
                        continue
                    pnl, score, error = train_algo(df, algo, k, n, p, threshold)
                    if DEBUG: print(((algo, k, n, p), (pnl, score, error)))
                    tries.append(((algo, k, n, p), (pnl, score, error)))

    max_pnl = 0
    max_pnl_config = None
    min_error = math.inf
    min_error_config = None
    max_score = 0
    max_score_config = None
    for result in tries:
        if max_pnl < result[1][0]:
            max_pnl = result[1][0]
            max_pnl_config = result
        if max_score < result[1][1]:
            max_score = result[1][1]
            max_score_config = result
        if min_error > result[1][2]:
            min_error = result[1][2]
            min_error_config = result
    return min_error_config, max_pnl_config, max_score_config

if __name__ == '__main__':
    b = time.time()
    # k: number of repetition
    # n: number of days in each row
    algos = list()
    algos.append(linear_model.LinearRegression())
    # algos.append(linear_model.LinearRegression())
    k_ = 100
    threshold = 50 # %
    min_error_config, max_pnl_config, max_score_config = main(
        algos,
        k_range=(k_, k_+1),
        n_range=(15, 101),
        p_min_max=None,
        threshold=threshold
    )
    print()
    print(min_error_config)
    print(max_pnl_config)
    print(max_score_config)
    print(time.time() - b)
    """
    """
