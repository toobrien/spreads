import  plotly.graph_objects    as go
from    plotly.subplots         import make_subplots
from    sys                     import argv
from    time                    import time
from    util                    import get_term_days


def render(sym: str):

    rows = get_term_days(sym)

    pass


if __name__ == "__main__":

    t0      = time()
    syms    = argv[1:]
    n_syms  = len(syms)
    fig     = make_subplots(rows = n_syms, cols = 1)

    for i in range(n_syms):

        sym = syms[i]

        trace = render(sym)

        fig.add_trace(
            row = i,
            col = 1 
        )

    print(f"{time() - t0:0.1f}s")

    pass