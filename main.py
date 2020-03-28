from sklearn import tree
from sklearn.model_selection import train_test_split
from sklearn import linear_model
from sklearn import preprocessing
import pandas
import math

X_columns = ['Open*', 'High', 'Low', 'Market Cap']

def raw_data_to_numeric(raw_data):
    data = raw_data.replace(' ', '')
    data = data.replace(',', '.')
    return float(data)

def get_X(df):
    return df[X_columns]

def get_Y(df):
    return df['Close**']

def train(df):
    X = get_X(df)
    Y = get_Y(df)
    X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=0.2)
    # algo = tree.DecisionTreeRegressor()
    algo = linear_model.LinearRegression()
    model = algo.fit(X_train, y_train)

    # Evaluation
    errors = int()
    for index, row in df.iterrows():
        e = get_Y(row) - model.predict([row[X_columns]])
        errors += abs(e)

    return model, model.score(X_test, y_test), errors / len(df)

def predict(model, X):
    print(X)
    print(model.predict(X))

def main(n=500):
    df = pandas.read_csv("bitcoin-price-all.csv", sep=';')
    df = df[['Open*', 'High', 'Low', 'Close**', 'Volume', 'Market Cap']]
    df = df.applymap(raw_data_to_numeric)


    # Ready
    # df.sample(frac=1)
    df = df.sample(frac=1).reset_index(drop=True)
    score_total_learn = int()
    score_total_test = int()
    score_total_all = int()
    error = float()
    for i in range(n):
        df_train = df.loc[:100]
        df_test = df.loc[101:]
        X_train, X_test, y_train, y_test = train_test_split(get_X(df), get_Y(df), test_size=0.2)
        m, s, e = train(df_train)
        score_total_learn += s
        # sg = m.score(X_test, y_test)
        sg = m.score(get_X(df_test), get_Y(df_test))
        score_total_test += sg
        score_total_all += m.score(get_X(df), get_Y(df))
        error += float(e)
    print(score_total_learn / n) # apprentissage
    print(score_total_test / n) # test
    print(score_total_all / n)
    print(error / n)

    # manual testing:
    test = {
        'Open*': [6161.9, 6127.9, 6675.17],
        'High': [6245, 6228.1, 6735.46],
        'Low': [5963.8, 5974.7, 6590.96],
        'Volume': [16580, 14600, 35319797642],
        'Market Cap': [122088327519, 122088327519, 122834375216],
    } # 26/03 and 27/03
    # close[]:  6127.9   5748.8   6716.44
    predict(m, pandas.DataFrame(test, columns=X_columns))

def train_simple():
    df = pandas.DataFrame({
        'A': [1, 1, 1, 1, 0, 0, 0, 0],
        'B': [4, 4, 4, 4, 10, 10, 10, 10],
    }, columns=['A', 'B'])
    X_train, X_test, y_train, y_test = train_test_split(df[['A']], df['B'], test_size=0.2)
    print(X_train, X_test, y_train, y_test)
    algo = tree.DecisionTreeRegressor()
    model = algo.fit(X_train, y_train)
    print(model.score(X_test, y_test))
    print(model.predict(pandas.DataFrame({
        'A': [1]
    }, columns=['A'])))
    # This is just to see if it's work fine: it does!

if __name__ == '__main__':
    main()
    """
    0.9986416221252974
    0.999511199029026
    0.9994966193583056
    65.36635991706949
         Open*     High      Low    Market Cap
    0  6161.90  6245.00  5963.80  122088327519
    1  6127.90  6228.10  5974.70  122088327519
    2  6675.17  6735.46  6590.96  122834375216
    [6431.25224779 6434.0538859  6772.01936488]
    """
    # train_simple()
