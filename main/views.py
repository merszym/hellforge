from django.views.generic import CreateView, ListView, UpdateView, DetailView, DeleteView
from django.urls import reverse
from django.shortcuts import render
from .models import Location, Reference, Site, Layer, Culture, Date, Epoch, Checkpoint, DatingMethod, get_classname
from .forms import ReferenceForm, SiteForm, ProfileForm, CultureForm, \
    DateForm, EpochForm, CheckpointForm, ContactForm
import json
import seaborn as sns

def landing(request):
    return render(request, 'main/common/landing.html')

class LocationListView(ListView):
    model = Location

## Sites
class SiteDetailView(DetailView):
    model = Site
    extra_context = {'profile_form': ProfileForm, 'dating_form': DateForm, 'datingoptions': DatingMethod.objects.all() }
    template_name = 'main/site/site_detail.html'

    def get_context_data(self, **kwargs):
        from collections import defaultdict
        context = super(SiteDetailView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        data = []
        groups = []
        unit_groups = {}
        units = defaultdict(int)
        cultures = defaultdict(int)
        for checkpoint,color in zip(self.object.checkpoints, sns.color_palette('husl', len(self.object.checkpoints)).as_hex() ):
            data.append({
                "start": checkpoint.date.first().upper *-31556952-(1970*31556952000),
                "end": checkpoint.date.first().lower *-31556952-(1970*31556952000),
                "type":"background",
                #'style': f"border-left: solid 2px {color};border-right: solid 2px {color};",
                "content": f"<a href={reverse('checkpoint_update', kwargs={'pk':checkpoint.id})} class='btn-link'>{checkpoint.name}</a>",
                })
        for layer in self.object.layer.all():
            if layer.culture:
                if layer.pos > cultures[layer.culture.classname]:
                    cultures[layer.culture.classname] = layer.pos
            if layer.unit:
                if int(layer.pos) > units[layer.unit]:
                    units[layer.unit] = layer.pos
            if not layer.date.first() and not self.request.GET.get('include_undated', False) and not layer.reldate.first():
                continue

            upper = layer.mean_upper if not layer.reldate.first() else layer.reldate.first().upper
            lower = layer.mean_lower if not layer.reldate.first() else layer.reldate.first().lower

            if layer.unit:
                if layer.unit not in unit_groups:
                    unit_groups[layer.unit] = [layer.name.lower()]
                else:
                    unit_groups[layer.unit].append(layer.name.lower())

            groups.append({
                "id":layer.name.lower(),
                "content":layer.name,
                'treeLevel':1 if layer.unit else 2,
                "order": int(layer.pos)
            })
            layerdata = {
                "start": upper *-31556952-(1970*31556952000),
                "order":int(layer.pos),
                "content": f"{layer.culture.name if layer.culture else 'Sterile'} | {layer.age_summary}",
                "group": layer.name.lower(),
                "className":f"{layer.culture.classname if layer.culture else 'sterile'}",
                "type":"point"
                }
            # if range instead of point
            if (upper != lower):
                layerdata.update({
                    "end": lower *-31556952-(1970*31556952000),
                    "type": "range"
                })
            data.append(layerdata)

        for k,v in unit_groups.items():
            groups.append({
                "id":k,
                "content":k,
                'order':units[k],
                'treeLevel':2,
                'nestedGroups': v
            })
        context['groupdata'] = json.dumps(groups)
        context['itemdata'] = json.dumps(data)
        context['cultures'] = [
            (k,v) for k,v in zip(
                [x for x in sorted(cultures, key=lambda x: cultures[x])],
                sns.color_palette('husl',len(set(cultures))).as_hex()
            )
        ]
        # colors for the unit classes
        context['units'] = [
            (k,v) for k,v in zip(
                [get_classname(x) for x in sorted(units, key=lambda x: units[x])],
                sns.color_palette('viridis',len(set(units))).as_hex()
            )
        ]
        return context

class SiteListView(ListView):
    model = Site
    template_name = 'main/site/site_list.html'

## Cultures ##
class CultureDetailView(DetailView):
    model = Culture
    template_name = 'main/culture/culture_detail.html'

    # create the nested groups for the timeline template
    def get_context_data(self, **kwargs):
        context = super(CultureDetailView, self).get_context_data(**kwargs)
        items = []
        groupdata = []
        geo = {
            "type": "FeatureCollection",
            "features": []
        }
        nochildren = self.request.GET.get('nochildren',False)
        query = sorted(self.object.all_cultures(nochildren=nochildren), key=lambda x: x.upper*-1)
        # get the colors right
        ordered_sites = sorted(
                        self.object.all_sites(nochildren=nochildren),
                        key=lambda x: (x[0].upper, x[1].lowest_date(cult=self.object, nochildren=nochildren))
                    )
        all_sites = []
        [all_sites.append(site.name) for (cult,site) in ordered_sites if site.name not in all_sites]

        site_color_dict = {site.lower():f"{col}" for site,col in zip(all_sites, sns.color_palette('husl', len(all_sites)).as_hex()) }
        for cult in query:
            ordered_sites = sorted(
                        cult.all_sites(nochildren=True),
                        key=lambda x: x[1].lowest_date(cult=cult)*-1
                    )
            sites = []
            [sites.append(site) for (cult,site) in ordered_sites if site not in sites]
            if len(sites)==0:
                continue
            groupdata.append({
                'id':cult.name.lower(),
                'treeLevel':2,
                'content':f"{cult.name} | {cult.upper} - {cult.lower} ya",
                'order':int(cult.upper),
                'nestedGroups': [f"{cult.name.lower()}-{site.name.lower()}" for site in sites ],
            })
            site_date_dict = {}
            for site in sites:
                site_date_dict[site.name] = []
                geo['features'].append({
                    "type": "Feature",
                    "properties": {
                        'color':f'{site_color_dict[site.name.lower()]}',
                        'popupContent':f"<strong>{site.name}</strong><br><a href={reverse('site_detail', kwargs={'pk': site.id})} class=btn-link>Details</a>"
                        },
                    "geometry": site.geometry
                })
                groupdata.append({
                    'id':f"{cult.name.lower()}-{site.name.lower()}",
                    'content':f'{site.name}: <a href="{reverse("site_detail", kwargs={"pk":site.pk})}" class="btn-link">view</a>',
                    'treeLevel':3
                })
            for layer in cult.layer.all():
                site_date_dict[layer.site.name].extend([int(layer.mean_lower), int(layer.mean_upper)])

            for k,v in site_date_dict.items():
                culturedata = {
                    'start': max(v)*-31556952-(1970*31556952000), #1/1000 year in ms, start with year 0
                    'content': f"{k} | {max(v):,} ya",
                    'group': f"{cult.name.lower()}-{k.lower()}",
                    'type':'point'
                }
                if max(v) != min(v):
                    culturedata.update({
                        'end': min(v)*-31556952-(1970*31556952000),
                        'content': f"{k} | {max(v):,} - {min(v):,} ya",
                        'style': f"background-color: {site_color_dict[k.lower()]};",
                        'type':'range'
                    })
                items.append(culturedata)
        context['itemdata'] = items
        context['timelinedata'] = groupdata
        context['geo'] = geo
        return context


class CultureUpdateView(UpdateView):
    model = Culture
    form_class = CultureForm
    extra_context = {'reference_form': ReferenceForm, 'dating_form': DateForm, 'type':'Culture', 'datingoptions': DatingMethod.objects.all()}
    template_name = 'main/culture/culture_form.html'

    def get_context_data(self, **kwargs):
        context = super(CultureUpdateView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context


class CultureCreateView(CreateView):
    model = Culture
    form_class = CultureForm
    extra_context = {'reference_form': ReferenceForm, 'dating_form': DateForm, 'type':'Culture', 'datingoptions': DatingMethod.objects.all()}
    template_name = 'main/culture/culture_form.html'

    def get_context_data(self, **kwargs):
        context = super(CultureCreateView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context


class CultureListView(ListView):
    model = Culture
    template_name = 'main/culture/culture_list.html'

    def get_context_data(self, **kwargs):
        context = super(CultureListView, self).get_context_data(**kwargs)
        items = []
        groupdata = []

        query = Culture.objects.filter(culture__isnull=True)

        for n,cult in enumerate(query):
            groupdata.append({
                'id':cult.name.lower(),
                'content':f"<a class='btn-link' href={reverse('culture_detail', kwargs={'pk':cult.pk})}>{cult.name}</a> | {cult.upper} - {cult.lower} ya",
                'treeLevel':2,
                'nestedGroups': [int(f'{n}{m}') for m,subcult in enumerate(cult.all_cultures(noself=True)) ],
            })
            for m,subcult in enumerate(cult.all_cultures(noself=True)):
                groupdata.append({
                    'id':int(f'{n}{m}'),
                    'content':f"{subcult} <a class='btn-link' href={reverse('culture_detail', kwargs={'pk':subcult.pk})}>view</a>",
                    'order':int(f'{n}{m}'),
                    'treeLevel':3,
                })
                items.append({
                    'start': int(subcult.upper)*-31556952-(1970*31556952000), #1/1000 year in ms, start with year 0
                    'end': int(subcult.lower)*-31556952-(1970*31556952000),
                    'content': f"{subcult} | {subcult.upper} - {subcult.lower}",
                    'group': int(f'{n}{m}'),
                })
        context['itemdata'] = items
        context['timelinedata'] = groupdata
        return context


## Epoch ##
class EpochUpdateView(UpdateView):
    model = Epoch
    template_name = 'main/culture/culture_form.html'
    form_class = EpochForm
    extra_context = {'reference_form': ReferenceForm, 'dating_form': DateForm, 'type':'Epoch', 'datingoptions': DatingMethod.objects.all()}

    def get_context_data(self, **kwargs):
        context = super(EpochUpdateView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context

    def form_valid(self, form):
        """If the form is valid, save the associated model."""
        self.object = form.save()
        date = Date(upper=form.cleaned_data.get('upper'), lower=form.cleaned_data.get('lower'), method='hidden')
        date.save()
        date.refresh_from_db()
        self.object.date.add(date)
        return super().form_valid(form)


class EpochCreateView(CreateView):
    model = Epoch
    form_class = EpochForm
    template_name = 'main/culture/culture_form.html'
    extra_context = {'reference_form': ReferenceForm, 'dating_form': DateForm, 'type':'Epoch', 'datingoptions': DatingMethod.objects.all()}

    def get_context_data(self, **kwargs):
        context = super(EpochCreateView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context

    def form_valid(self, form):
        """If the form is valid, save the associated model."""
        self.object = form.save()
        date = Date(upper=form.cleaned_data.get('upper'), lower=form.cleaned_data.get('lower'), method='hidden')
        date.save()
        date.refresh_from_db()
        self.object.date.add(date)
        return super().form_valid(form)


class EpochListView(ListView):
    model = Epoch
    template_name = 'main/culture/culture_list.html'
    extra_context = {'type': 'Epoch'}

    def get_context_data(self, **kwargs):
        context = super(EpochListView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context


## Checkpoints
class CheckpointCreateView(CreateView):
    model = Checkpoint
    form_class = CheckpointForm
    extra_context = {'reference_form': ReferenceForm, 'dating_form': DateForm, 'datingoptions': DatingMethod.objects.all()}

    def get_context_data(self, **kwargs):
        context = super(CheckpointCreateView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context

    def form_valid(self, form):
        """If the form is valid, save the associated model."""
        self.object = form.save()
        date = Date(upper=form.cleaned_data.get('upper'), lower=form.cleaned_data.get('lower'), method='hidden')
        date.save()
        date.refresh_from_db()
        self.object.date.add(date)
        return super().form_valid(form)


class CheckpointUpdateView(UpdateView):
    model = Checkpoint
    form_class = CheckpointForm
    extra_context = {'reference_form': ReferenceForm, 'dating_form': DateForm, 'datingoptions': DatingMethod.objects.all()}

    def form_valid(self, form):
        """If the form is valid, save the associated model."""
        self.object = form.save()
        date = Date(upper=form.cleaned_data.get('upper'), lower=form.cleaned_data.get('lower'), method='hidden')
        date.save()
        date.refresh_from_db()
        self.object.date.add(date)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(CheckpointUpdateView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context