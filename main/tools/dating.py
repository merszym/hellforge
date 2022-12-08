from iosacal import R

def calibrate_c14(date, plusminus, id='tmp'):
    curve = 'intcal20'
    r = R(date, plusminus, id)
    lower, upper = r.calibrate(curve).quantiles()[95]
    return upper,lower, curve