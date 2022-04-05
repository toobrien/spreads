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

# Notes

- spreads are quoted with the following legs: 

    'cal':  -1, +1

    'fly':  +1, -2, +1
    
    'dfly': +1, -3, +3, -1

- for use with [futures_db](https://github.com/toobrien/futures_db)
- active spreads are highlighted red, while those expired are progressively fainter blue
- adjust min/max dte to get the best default fit for your scatter plots
- the histogram is in probability density format