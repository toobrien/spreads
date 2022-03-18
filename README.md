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

# Notes

- spreads are quoted with the following legs: 

    'cal':  -1, +1 
    'fly':  +1, -2, +1 
    'dfly': +1, -3, +3, -1

- for use with [futures_db](https://github.com/toobrien/futures_db)
- active spreads are highlighted red, while those expired are progressively fainter blue
- adjust min/max dte to get the best default fit for your scatter plots
- the histogram is in probability density format