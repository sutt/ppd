

# WAITKEYS ------------------------------------------------------------

if cv2.waitKey(waitKeyRefresh)== ord('p'):
    print 'taking picture of rect'
    pause_rect = crop_img(img_t.copy(), Globals.current_tracking_frame)
    Globals.b_show_puase_rect = True

if cv2.waitKey(waitKeyRefresh)== ord('t'):
    print 'starting iter-thresh: \n'

    img_crop = crop_img(frame.copy(), Globals.current_tracking_frame)

    out_thresh = iterThreshA( img_crop
                                ,goal_pct = Globals.thresh_pct 
                                ,steep = False)
    _lo , _hi = out_thresh[1][3], out_thresh[1][4]
    print 'new thresh: ', str(_lo), str(_hi)
    
    if b_thresh_log:
        Globals.thresh_log.append( (_lo,_hi))
        _lo, _hi = combine_threshes(Globals.thresh_log)
        print 'combined log \n', str(_lo), str(_hi)
        
    Globals.threshLoRgb = np.array( _lo , dtype = 'uint8' )
    Globals.threshHiRgb = np.array( _hi, dtype = 'uint8' )
    print 'Globals set: ', str(Globals.threshLoRgb), str(Globals.threshHiRgb)
    sw_agenda = True

if cv2.waitKey(waitKeyRefresh)== ord('a'):    
    sw_agenda = True

if cv2.waitKey(waitKeyRefresh)== ord('l'):

    writepath = "data/write/july"
    output_dir = uni_dir(writepath)
    make_dir(writepath + "/" + output_dir)
    print 'writing out to: ', output_dir
    
    write_pic(frame
                ,name_base="img",path=output_dir)
    write_pic(img_t
                ,name_base="img_t",path=output_dir)
    write_pic(crop_img(frame.copy(), Globals.current_tracking_frame)
                ,name_base="rect",path=output_dir)
    write_pic(crop_img(img_t.copy(), Globals.current_tracking_frame)
                ,name_base="rect_t",path=output_dir)
    

if cv2.waitKey(waitKeyRefresh) == ord('o'):
    while(True):
        ret = Options()
        if ret == 1: 
            break
# /WAITKEYS -------------------------------------------------------------------------

# HISTOS ---------------------------------------------------------------------------

# PROC & SHOW HISTOS
if Globals.b_show_histos:
    
    if livehist == None:
        livehist = InitLiveHist(b_histo_backg
                                ,b_pause = args["startuppause"])
        last_hist_update = time.time() - (hist_update_hz + 1)    #and process
    
    if time.time() - last_hist_update > hist_update_hz:

        if Globals.b_histo:
            px_data = imgToPx(img_t, Globals.current_tracking_frame, ) ##frame should be img
            if Globals.b_show_puase_rect: 
                px_data = imgToPx2(img_t, pause_rect, Globals.current_tracking_frame )
                
            hist_data = pxToHist(px_data)
            
        
        if switch_new_ylim:
            SwitchYLim(livehist, hist_data)
            switch_new_ylim = False

        livehist.update_figure( hist_data
                    ,ax_ind = range(livehist.N)
                    ,frames = 1
                    ,show = True
                    ,epsilon = .0001)
        
        last_hist_update = time.time()

# ITER THRESH
if ((i+1) % 60 == 0) and False:
    
    img_crop = crop_img(frame.copy(), Globals.current_tracking_frame)
    out_thresh = iterThreshA(img_crop
                            ,goal_pct = Globals.thresh_pct
                            ,steep = False)
    Globals.threshLoRgb = np.array( out_thresh[1][3], dtype = 'uint8' )
    Globals.threshHiRgb = np.array( out_thresh[1][4], dtype = 'uint8' )
    print 'newThresh: \n', str(Globals.threshLoRgb), str(Globals.threshHiRgb)