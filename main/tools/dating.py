from iosacal import R
from django.http import JsonResponse
from django.shortcuts import render
from main.models import models

def calibrate(estimate, plusminus):
    curve = 'intcal20'
    r = R(int(estimate), int(plusminus), 'tmp')
    lower, upper = r.calibrate(curve).quantiles()[95]
    return upper, lower, curve

def calibrate_c14(request):
    date = request.GET.get('estimate', False)
    pm = request.GET.get('pm', False)
    if date and pm and pm != '0':
        upper, lower, curve = calibrate(date, pm)
        return JsonResponse({"status":True, "lower":lower, 'upper':upper, 'curve':curve})
    return JsonResponse({"status":False})

def add(request):
    from main.forms import DateForm
    from main.models import DatingMethod
    form = DateForm(request.POST)
    if form.is_valid(): # is always valid because nothing is required
        # validate that dates exist
        if any([form.cleaned_data.get(x,False) for x in ['estimate','upper','lower']]):
            obj = form.save() # post_safe signal fires here to calibrate if not done yet
            obj.refresh_from_db()
            #if we have an associated model (e.g. Layer)
            if dat := form.cleaned_data.get('info', False):
                model,pk = dat.split(',')
                layer = models[model].objects.get(pk=int(pk))
                layer.date.add(obj)
                layer.save() #not needed for adding, but for post-save signal in layer
            return JsonResponse({"status":True})
        # error validation
        form.add_error(None, 'Please provide a Date')
    return render(request,'main/dating/dating-modal-content.html',{'datingoptions': DatingMethod.objects.all(), 'form':form})