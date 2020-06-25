import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

plt.rcParams['figure.figsize'] = (12.0, 8.0)


# Code could have been further simplified, adding functions for repeating code

class Contract:
    def __init__(self, date, strike, volume, ticker, lastPrice, type, openInterest):
        self.openInterest = openInterest
        self.type = type
        self.ticker = ticker
        self.volume = volume
        self.strike = strike
        self.date = date
        self.lastPrice = lastPrice


def print_chart(list_of_contracts_calls, list_of_contracts_puts, current_asset_value, date, ticker,
                normalize_volumes=True, normalize_together=False):
    x_axis_strikes_calls = [contract.strike for contract in list_of_contracts_calls]
    x_axis_strikes_puts = [contract.strike for contract in list_of_contracts_puts]
    x_axis = list(dict.fromkeys(sorted(x_axis_strikes_puts + x_axis_strikes_calls)))
    last_prices_calls = [contract.lastPrice for contract in list_of_contracts_calls]
    last_prices_puts = [contract.lastPrice for contract in list_of_contracts_puts]
    call_volumes = [contract.volume for contract in list_of_contracts_calls]
    put_volumes = [contract.volume for contract in list_of_contracts_puts]

    y_axis_puts = []
    y_axis_size_puts = []
    y_axis_calls = []
    y_axis_size_calls = []

    counter = 0

    if len(last_prices_calls) != len(call_volumes):
        raise IndexError("Major error, len of volumes and strikes doesn't match up!")
    if len(last_prices_puts) != len(put_volumes):
        raise IndexError("Major error, len of volumes and strikes doesn't match up!")

    # accounting for the fact that calls and puts have different number of strike prices
    # this should be in a function
    for strike in x_axis:
        try:
            if len(last_prices_calls) > counter:
                if strike in x_axis_strikes_calls:
                    y_axis_calls.append(last_prices_calls[counter])
                    y_axis_size_calls.append(call_volumes[counter])
                    counter += 1
                else:
                    y_axis_calls.append(0)
                    y_axis_size_calls.append(0)
                    # counter += 1
            else:
                y_axis_calls.append(0)
                y_axis_size_calls.append(0)
        except IndexError:
            y_axis_calls.append(0)
            y_axis_size_calls.append(0)

    # accounting for the fact that calls and puts have different number of strike prices
    # this should be in a function
    counter = 0
    for strike in x_axis:
        try:
            if len(last_prices_puts) > counter:
                if strike in x_axis_strikes_puts:
                    y_axis_puts.append(last_prices_puts[counter])
                    y_axis_size_puts.append(put_volumes[counter])
                    counter += 1
                else:
                    y_axis_puts.append(0)
                    y_axis_size_puts.append(0)
            else:
                y_axis_puts.append(0)
                y_axis_size_puts.append(0)
        except IndexError:
            y_axis_puts.append(0)
            y_axis_size_puts.append(0)

    # naive attempt to normalize data
    if normalize_volumes:
        min_max_scaler = MinMaxScaler()
        # normalizing volumes separately
        if not normalize_together:
            # this should be in a function
            y_axis_size_calls = np.array(y_axis_size_calls)
            y_axis_size_calls = y_axis_size_calls.reshape(-1, 1)
            y_axis_size_calls = min_max_scaler.fit_transform(y_axis_size_calls)
            y_axis_size_calls = [value * 400 for value in y_axis_size_calls]

            y_axis_size_puts = np.array(y_axis_size_puts)
            y_axis_size_puts = y_axis_size_puts.reshape(-1, 1)
            y_axis_size_puts = min_max_scaler.fit_transform(y_axis_size_puts)
            y_axis_size_calls = [value * 400 for value in y_axis_size_puts]
        #   normalizing volumes together
        else:
            dataframe_ = pd.DataFrame({'col0': y_axis_size_calls, 'col1': y_axis_size_puts})
            x_scaled = min_max_scaler.fit_transform(dataframe_)
            df = pd.DataFrame(x_scaled)

            y_axis_size_calls = [value * 400 for value in list(df[0])]
            y_axis_size_puts = [value * 400 for value in list(df[1])]
    else:
        # make chart more readable
        y_axis_size_calls = [value / 10 for value in y_axis_size_calls]
        y_axis_size_puts = [value / 10 for value in y_axis_size_puts]

    # calculating percentage changes for second x-axis
    percentage_changes = []
    for strike in x_axis:
        if strike < current_asset_value:
            change = (-1) * ((1 - (strike / current_asset_value)) * 100)
        elif strike == current_asset_value:
            change = 0
        else:
            change = (((strike / current_asset_value) - 1) * 100)
        percentage_changes.append(change)

    def plot_chart(x_axis_strikes, y_axis_lastPrices_calls, y_axis_lastPrices_puts, percentage_changes):
        fig = plt.figure()
        ax1 = fig.add_subplot(111)
        ax1.scatter(x_axis_strikes, y_axis_lastPrices_calls, s=y_axis_size_calls, edgecolors='green',
                    facecolors='none', label="Call volume")
        ax1.scatter(x_axis_strikes, y_axis_lastPrices_puts, s=y_axis_size_puts, edgecolors='red', facecolors='none',
                    label="Put volume")
        ax1.plot(x_axis_strikes, y_axis_lastPrices_calls, 'ro', markersize=0.5, color="green", marker="^",
                 label="Call price")
        ax1.plot(x_axis_strikes, y_axis_lastPrices_puts, 'ro', markersize=0.5, color="red", marker="v",
                 label="Put price")
        ax1.legend(markerscale=1)

        ax1.set_xlabel("Strike")
        ax1.set_ylabel("Premium [$USD]")
        plt.title(
            f"{ticker} at {current_asset_value}, Expiry: {date}, {('Normalizing volumes together' if normalize_together else 'Normalizing volumes separately') if normalize_volumes else ' Not normalizing volumes'}")

        # line in the middle
        ax1.axvline(x=current_asset_value, linestyle='--')
        # plt.grid()

        # adding second x-axis for percentage change
        ax2 = ax1.twiny()
        ax2.plot(percentage_changes, [1 for x in range(0, len(percentage_changes))])
        ax2.cla()
        ax2.xaxis.set_ticks_position("bottom")
        ax2.xaxis.set_label_position("bottom")
        ax2.spines["bottom"].set_position(("axes", -0.15))
        ax2.set_xlabel("Percentage Change [%]")

        plt.show()

    plot_chart(x_axis, y_axis_calls, y_axis_puts, percentage_changes)


def download_data_and_print_chart(ticker, date, normalize, normalize_together=False):
    a_ticker = yf.Ticker(ticker=ticker)
    current_asset_value = a_ticker.history(period='1d').iloc[0][3]

    option_chain_data = a_ticker.option_chain(date=date)
    calls_data_frame = option_chain_data.calls  # pd.DataFrame(request[0])
    puts_data_frame = option_chain_data.puts  # pd.DataFrame(request[1])

    list_of_contracts_calls = []
    list_of_contracts_puts = []

    # ---- This should be a function
    for contract in calls_data_frame.iterrows():
        list_of_contracts_calls.append(
            Contract(strike=contract[1]["strike"], volume=contract[1]["volume"], lastPrice=contract[1]["lastPrice"],
                     date=date, ticker=ticker, type="CALL", openInterest=contract[1]["openInterest"]))

    for contract in puts_data_frame.iterrows():
        list_of_contracts_puts.append(
            Contract(strike=contract[1]["strike"], volume=contract[1]["volume"], lastPrice=contract[1]["lastPrice"],
                     date=date, ticker=ticker, type="PUT", openInterest=contract[1]["openInterest"]))
    # ----

    print_chart(list_of_contracts_calls, list_of_contracts_puts, current_asset_value, ticker=ticker, date=date,
                normalize_volumes=normalize, normalize_together=normalize_together)


if __name__ == "__main__":
    ticker = "NET"
    date = "2020-07-17"
    download_data_and_print_chart(ticker, date, normalize=False, normalize_together=True)
