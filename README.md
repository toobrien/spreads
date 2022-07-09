chart spreads of various types against historical issues

# Usage

chart all butterflies by sequence, i.e. 0 = m1, m2, m3; 1 = m2, m3, m4; and so on:

`python app.py CL fly all_seq`

chart all butterflies by season, i.e. 'FGH', 'GHJ', 'HJK' etc.:

`python app.py ZW fly all_sea`

chart one season of butterflies:

`python app.py HO fly JKM`

chart one sequence of butterflies:

`python app.py ZL fly 0`

chart one season and one sequence:

`python app.py GE fly MUZ 0`

chart two calendars in consecutive seasons:

`python app.py ZC cal HK KN`

double flies are also available; chart three in sequence:

`python app.py ZQ dfly 0 1 2`

for STIRs and some "regularly produced" commodities, you may simply want to group all contracts. view all ZQ spreads with 50 to 100 days to expiration:

`python app.py ZQ fly all_50:150` 

# Watchlists

To avoid the tedium of entering the same spreads on successive days, you can configure `watchlists.json` to render sets of spreads automatically. See the included file for examples. To execute the `default` watchlist:

`python app.py watchlist default`

# Text Mode

You can add the word "text" to the end of the command for a printout, rather than charts. For example:

`python app.py ZL fly all_0:120 text`

`python app.py watchlist default text`

# Regression

`reg.py` allows you to regress either a reverse calendar or a butterfly onto a single contract, such as the front leg. Example usage:

`python reg.py pct HON2022 HON2022:HOQ2022 2022-02-01 2022-07-01 15`

The first argument determines whether log returns (`pct`) or subtraction (`abs`) is used to difference the series for regression. The second argument is the regressor variable, a single contract identified by symbol, month and year. The third argument identifies the response variable, which is a spread. A colon separates each leg. If there are two legs, the spread is a reverse calendar (+1, -1); if there are three legs, it is a butterfly (+1, -2, +1). The next two arguments are start and end dates in yyyy-mm-dd format. The last argument is the number of records to display, which show the settlement values for both the spread and regressor contract, and their changes for each day.

The example above regresses the july/august heating oil spread onto the july leg using log returns, between February 1st and July 1st, and displays 15 records.

# Notes

- spreads are quoted with the following legs: 

    'cal':  -1, +1

    'rcal': +1, -1

    'fly':  +1, -2, +1
    
    'dfly': +1, -3, +3, -1

- for use with [futures_db](https://github.com/toobrien/futures_db)
- active spreads are highlighted red, while those expired are progressively fainter blue
- adjust min/max dte to get the best default fit for your scatter plots
- the histogram is in probability density format