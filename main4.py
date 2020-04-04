from sklearn import tree, svm, gaussian_process
from sklearn.model_selection import train_test_split
from sklearn import linear_model
from sklearn import preprocessing
import pandas
import numpy
import math
import random
import statistics

def raw_data_to_numeric(raw_data):
    data = raw_data.replace(' ', '')
    data = data.replace(',', '.')
    return float(data)

def split_df(df, test_size=0.2):
    n = df.shape[1]
    x = df.iloc[:,:n-1]
    y = df.iloc[:,n-1]
    return train_test_split(x, y, test_size=test_size)


def train_model(df, algo, n):
    x_train, x_test, y_train, y_test = split_df(df)
    model = algo.fit(x_train, y_train)
    return model, model.score(x_test, y_test)



def evaluate(df, model, m=100, threshold=100):
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
                sell_prices.append(prediction)
            else:
                buy_prices.append(prediction)
                sell_prices.append(x_decision)

        # calculate error
        tot_error += error

    # end of for loop
    if len(buy_prices) and len(sell_prices):
        prix_achat_moy = statistics.mean(buy_prices)
        prix_vente_moy = statistics.mean(sell_prices)
        # print(prix_achat_moy)
        # print(prix_vente_moy)
    else:
        prix_achat_moy = 0
        prix_vente_moy = 0
    return (((prix_vente_moy / prix_achat_moy) - 1) * 100), tot_error / m

def main(algo, n=14, k=50):
    """
    Create row of n days.
    Train and test k models.
    """
    print(str(algo)[:str(algo).find('(')])
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
                row = list()
                i = 0
    new_df = pandas.DataFrame(new_df_list)

    tot_pnl = int() # total profit and loss
    tot_score = int()
    tot_error = int()
    # train several models
    for i in range(k):
        model, score = train_model(new_df, algo, n)
        tot_score += score
        pnl, error = evaluate(new_df, model, n)
        tot_pnl += pnl
        tot_error = error
    print('pnl:   ' + str(tot_pnl / k))
    print('score: ' + str(tot_score / k))
    print('error: ' + str(tot_error / k))
    print()

if __name__ == '__main__':
    n = 15
    k = 100
    main(svm.SVR(), n, k)
    main(linear_model.SGDRegressor(), n, k)
    main(linear_model.LinearRegression(), n, k)
    main(gaussian_process.GaussianProcessRegressor(), n, k)
    """
    SVR
    pnl:   920.0377622338833
    score: -0.40757203601020864
    error: 84.06736743459896

    SGDRegressor
    pnl:   3326314273912839.0
    score: -8.365597114192531e+27
    error: 265865377123154.0

    LinearRegression
    pnl:   3.9391180976549163
    score: 0.981791386758865
    error: 3.493815099979772

    GaussianProcessRegressor
    pnl:   62.6189457666077
    score: -0.7321396045392251
    error: 17.448546674346023
    """
