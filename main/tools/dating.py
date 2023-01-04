from iosacal import R
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import path
from django.db.models import Q
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

def batch_upload(request):
    #handle the csv upload --> #TODO: make a verification!
    #render into new modal, so that people can verify
    #dont save anything yet, but process how it will be saved! show the table
    #TODO: maybe make a general upload-helper function, independant of the model!
    #TODO: verify required columns

    import pandas as pd
    import main.tools as tools
    from main.models import Date, Reference, Layer
    expected = Date.table_columns()
    #import csv without saving

    df = pd.read_csv(request.FILES['file'], sep=',')
    df.drop_duplicates(inplace=True)

    site = Layer.objects.get(pk=int(request.POST.get('layer').split(',')[1])).site
    all_layers = [x.name for x in site.layer.all()]

    #filter for expected/unexpected columns
    issues = []
    if dropped := [x for x in df.columns if x not in expected]:
        issues.append(f"Dropped Table Columns: {','.join(dropped)}")
    df = df[[x for x in df.columns if x in expected ]]

    #hardcode the testing for now
    if 'Reference' in df.columns:
        df['Reference'] = df.Reference.apply(lambda x: tools.references.find(x))
        if 'Not Found' in set(df['Reference']):
            issues.append('Reference was not found (see Table)')

    layer_wrong = df[df.Layer.isin(all_layers)==False].copy()
    if len(layer_wrong) > 0:
        issues.append(f"Removed non-existing Layers: {','.join(set(layer_wrong['Layer']))}")
        df.drop(layer_wrong.index, inplace=True)
    return render(
        request,
        'main/dating/dating-batch-confirm.html',
        {
            'dataframe': df.fillna('').to_html(index=False, classes='table table-striped col-12'),
            'issues': issues,
            'json': df.to_json(),
            'site':site
        }
    )

def save_verified_batchdata(request):
    import pandas as pd
    from main.models import Date, Site, Layer, Reference
    df = pd.read_json(request.POST.get('batch-data'))
    site = Site.objects.get(pk=int(request.POST.get('site')))
    df.convert_dtypes()
    #TODO: use a date-form to create instances for each row
    for i, dat in df.iterrows():
        dat = dat.dropna()
        tmp = Date(
            method = dat['Method']
        )
        if 'Lab Code' in dat:
            try:
                #get an already existing date
                tmp = Date.objects.get(oxa=dat['Lab Code'])
            except:
                #continue with the new one
                tmp.oxa = dat['Lab Code']
        #if a new date
        if not tmp.pk:
            if 'Date' in dat:
                tmp.estimate = dat['Date']
            if 'Error' in dat:
                tmp.plusminus = dat['Error']
            if 'Upper Bound' in dat:
                tmp.upper = dat['Upper Bound']
            if 'Lower Bound' in dat:
                tmp.lower = dat['Lower Bound']
            if 'Notes' in dat:
                tmp.description = dat['Notes']
            tmp.save()
            tmp.refresh_from_db()

        if 'Reference' in dat:
            tmp.ref.add(Reference.objects.get(pk=dat['Reference']['id']))
        tmp_layer = Layer.objects.filter(Q(site = site) & Q(name = dat['Layer'])).first()
        tmp_layer.date.add(tmp)
        tmp_layer.save()
    return JsonResponse({'status': True})

def add(request):
    from main.forms import DateForm
    from main.models import DatingMethod, Date
    form = DateForm(request.POST)
    if form.is_valid(): # is always valid because nothing is required
        #create a tmp-date, dont save
        obj = Date(method='tmp')
        # check if we have the date already in the database
        # replace the tmp-date
        if oxa := form.cleaned_data.get('oxa'):
            try:
                obj = Date.objects.get(oxa=oxa)
            except Date.DoesNotExist:
                pass
        # validate that dates exist in the form... is relevant if the date doesnt exist yet
        if not obj.pk:
            if any([form.cleaned_data.get(x,False) for x in ['estimate','upper','lower']]):
                obj = form.save() # post_safe signal fires here to calibrate if not done yet
                obj.refresh_from_db()
            else:
                form.add_error(None, 'Please provide a Date')
                return render(request,'main/dating/dating-modal-content.html',{'datingoptions': DatingMethod.objects.all(), 'form':form})
        #if we have an associated model (e.g. Layer)
        if dat := form.cleaned_data.get('info', False):
            model,pk = dat.split(',')
            layer = models[model].objects.get(pk=int(pk))
            layer.date.add(obj)
            layer.save() #not needed for adding, but for post-save signal in layer
        return JsonResponse({"status":True})
        # error validation
    return render(request,'main/dating/dating-modal-content.html',{'datingoptions': DatingMethod.objects.all(), 'form':form})

def delete(request):
    from main.models import Layer, Date
    layer = Layer.objects.get(pk=int(request.POST.get('layer')))
    date = Date.objects.get(pk=int(request.POST.get('date')))
    #remove the date
    layer.date.remove(date)
    #not sure if I really want to delte dates?
    if len(date.model.all()) == 0:
        date.delete()
    return JsonResponse({'status':True})

def add_relative(request):
    from main.forms import RelDateForm
    form = RelDateForm(request.POST)
    if form.is_valid(): # is always valid because nothing is required
        obj = form.save()
        #if we have an associated model (e.g. Layer)
        if dat := form.cleaned_data.get('info', False):
            model,pk = dat.split(',')
            layer = models[model].objects.get(pk=int(pk))
            layer.reldate.add(obj)
            layer.save() #not needed for adding, but for post-save signal in layer
        return JsonResponse({"status":True})
        # error validation
    return render(request,'main/dating/reldate-modal-content.html',{'form':form})

urlpatterns = [
    path('add',        add,                     name='ajax_date_add'),
    path('delete',     delete,                  name='ajax_date_unlink'),
    path('upload',     batch_upload,            name='ajax_date_batch_upload'),
    path('save-batch', save_verified_batchdata, name='ajax_save_verified_batchdata'),
    path('calibrate',  calibrate_c14,           name='ajax_date_cal'),
    path('add_rel',    add_relative,            name='ajax_add_reldate'),
]