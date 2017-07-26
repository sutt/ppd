from GraphicsA import LiveHist


def InitLiveHist(inp):
    if inp:
        h,w = 2,3
        NUM_PLOTS = 6
    else:
        h,w = 1,3
        NUM_PLOTS = 3

    livehist = LiveHist( h = h, w = w, bins = 30
                        ,x_lo = -1, x_hi = 256
                        ,y_lo = 0 ,y_hi = 7000 )

    livehist.show_plt(wait_time = 2)

    return livehist