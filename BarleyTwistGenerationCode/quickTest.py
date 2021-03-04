
import yfinance as yf

msft = yf.Ticker("AACQU")

print(msft.recommendations)

print(msft.info)
#'twoHundredDayAverage'
#'trailingAnnualDividendYield'
#'payoutRatio'
#'averageVolume10days'
#'dividendRate': 2.24, 'exDividendDate'
#'trailingPE'
#'priceToSalesTrailing12Months':
#'fiftyTwoWeekHigh'
#'fiftyTwoWeekLow'
#'dividendYield': 0.01, 
#'profitMargins':
#'sharesOutstanding'
#'regularmarketopen'