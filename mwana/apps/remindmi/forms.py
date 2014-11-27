import datetime
from datetime import timedelta
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from rapidsms.models import Contact, Backend
from rapidsms.router import lookup_connections

from mwana.apps.appointments.forms import *
from mwana.apps.appointments.models import Milestone

from mwana.apps.labresults.models import Result

from mwana import const


class CollectForm(HandlerForm):
    """Notify client that results are ready for collection."""
    sample_id = forms.CharField(max_length=50, error_messages={
        'required': _('Please provide the sample id.')})

    def clean(self):
        "Check if sample id exists and if has carer_phone"
        sample_id = self.cleaned_data.get('sample_id', None)
        if sample_id is not None:
            samples = Result.objects.filter(
                requisition_id_search__exact=sample_id,
                verified=True
            )
            if samples.exists():
                params = {'sid': sample_id, }
                if samples[0].carer_phone is None:
                    # let user know sample does not exist or not yet ready.
                    message = _('Sorry, the sample %(sid)s does not have a '
                                'phone number registered to receive a result'
                                ' collection notice.') % params
                    raise forms.ValidationError(message)
                else:
                    self.cleaned_data['carer_phone'] = samples[0].carer_phone
            else:
                message = _('Sorry, the sample: %(sid)s is not yet ready'
                            'for collection. If you have been waiting for '
                            'long please send HELP sample_id.') % params
                raise forms.ValidationError(message)
        return self.cleaned_data

    def _get_backend(self, backend_name):
        """Returns a matching backend based on the name."""
        return Backend.objects.filter(name__iexact=backend_name)[0]

    def _validate_cell(self, num):
        if num is None:
            return None, False
        num = str(num)
        if num.strip().upper() in ['X', 'XX']:
            return None, False
        try:
            num = int(num)
        except ValueError:
            # register no number if not valid number
            return None, False
        # only accept 10 digit numbers for now
        # FIXME: replace with phonenumbers
        if len(str(num)) == 9:
            if str(num)[:1] == '8':
                backend_name = 'tnm'
            elif str(num)[:1] == '9':
                backend_name = 'zain'
            valid_cell = True
        else:
            backend_name = None
            valid_cell = False
        return backend_name, valid_cell

    def save(self):
        "Send a collection notification notice to the registered carer_phone"
        phone = self.cleaned_data['carer_phone']
        sample_id = self.cleaned_data['sample_id']
        healthworker = self.connection.contact
         # check opt-in
        backend_name, valid_cell = self._validate_cell(phone)
        if valid_cell:
            phone = "+265" + phone[1:]
            backend = self._get_backend(backend_name)
            conn = lookup_connections(backend=backend,
                                      identities=[phone])
        else:
            conn = phone = None

        return {
            'phone': conn,
            'phoneid': phone,
            'id': sample_id,
            'user': healthworker.name,
        }


class MayiForm(HandlerForm):
    """Register a mother on mothers continuum of care. """

    edd = forms.DateField(required=True, error_messages={
        'required': _(
            'Sorry, please use the DDMMYYYY or YYYY-MM-DD format.')})
    firstname = forms.CharField(required=False, error_messages={
        'required': _(
            'Sorry, you must provide a mothers first name.')})
    lastname = forms.CharField(required=False, error_messages={
        'required': _(
            'Sorry, you must provide a mothers last name.')})
    dob = forms.CharField(error_messages={'required': _('Please provide a'
                                                        ' date of birth.')})
    phone = forms.CharField(max_length=15, error_messages={
        'required': _('Please enter the phone number or X')})
    status = forms.CharField(max_length=10, error_messages={
        'required': _('Please enter P, N or U for the mothers status.')})
    name = forms.CharField(required=True, max_length=50, error_messages={
        'required': _('Please provide the id of the mother.')})
    volunteer = forms.CharField(max_length=15, required=False)

    def clean(self):
        "Check for previous subscription."
        timeline = self.cleaned_data.get('timeline', None)
        name = self.cleaned_data.get('name', None).upper()
        location = self.connection.contact.location
        if name is not None and timeline is not None and location is not None:
            previous = TimelineSubscription.objects.filter(
                Q(Q(end__isnull=True) | Q(end__gte=now())),
                timeline=timeline, connection=self.connection, pin=name
            )
            if previous.exists():
                prev_loc = previous[0].connection.contact.location
                location_name = location.__unicode__()
                if prev_loc.__unicode__() == location_name:
                    params = {'timeline': timeline.name,
                              'name': name,
                              'location': location_name}
                    message = _(
                        'Sorry, you previously registered a %(timeline)s for '
                        '%(name)s at %(location)s. You will be notified '
                        'when it is time for the next appointment.') % params
                    raise forms.ValidationError(message)
        return self.cleaned_data

    def _get_backend(self, backend_name):
        """Returns a matching backend based on the name."""
        return Backend.objects.filter(name__iexact=backend_name)[0]

    def _validate_cell(self, num):
        if num is None:
            return None, False
        num = str(num)
        if num.strip().upper() in ['X', 'XX']:
            return None, False
        try:
            num = int(num)
        except ValueError:
            # register no number if not valid number
            return None, False
        # only accept 10 digit numbers for now
        if len(str(num)) == 9:
            if str(num)[:1] == '8':
                backend_name = 'tnm'
            elif str(num)[:1] == '9':
                backend_name = 'airtelsmpp'
            valid_cell = True
        else:
            backend_name = None
            valid_cell = False
        return backend_name, valid_cell

    def save(self):
        if not self.is_valid():
            return None
        timeline = self.cleaned_data['timeline']
        name = self.cleaned_data['name'].upper()
        if "_" in name:
            firstname, lastname = name.split("_")
        else:
            firstname = lastname = ''
        start = self.cleaned_data['edd']
        edd_start = start - timedelta(days=270)
        phone = self.cleaned_data['phone']
        volunteer = self.cleaned_data['volunteer']
        v_backend_name, v_cell = self._validate_cell(volunteer)
        if v_cell:
            volunteer = "+265" + volunteer[1:]
            v_backend = self._get_backend(v_backend_name)
            v_conn = lookup_connections(backend=v_backend,
                                        identities=[volunteer])[0]
        else:
            v_conn = None
        healthworker = self.connection.contact
        location_id = self.connection.contact.location
        if v_conn is not None:
            reminder_conn = v_conn
        else:
            reminder_conn = self.connection

        TimelineSubscription.objects.create(
            timeline=timeline, start=edd_start, pin=name,
            connection=reminder_conn
        )
        exposed = Timeline.objects.get(name="Exposed")
        if self.cleaned_data['status'].upper() == "P":
            TimelineSubscription.objects.create(
                timeline=exposed, start=edd_start, pin=name,
                connection=reminder_conn
            )

        if len(volunteer) < 2:
            volunteer = self.connection.identity
        # create the patient
        if healthworker is not None and location_id is not None:
            patient, created = Contact.objects.get_or_create(
                name=name,
                location=location_id,
                first_name=firstname,
                last_name=lastname,
                date_of_birth=self.cleaned_data['dob'],
                volunteer=volunteer)

        patient_t = const.get_patient_type()
        if not patient.types.filter(pk=patient_t.pk).count():
            patient.types.add(patient_t)

        mother_t = const.get_mother_type()
        if not patient.types.filter(pk=mother_t.pk).count():
            patient.types.add(mother_t)

        # check opt-in
        backend_name, valid_cell = self._validate_cell(phone)
        if valid_cell:
            phone = "+265" + phone[1:]
            backend = self._get_backend(backend_name)
            patient_conn = lookup_connections(backend=backend,
                                              identities=[phone])[0]
            if patient_conn.contact_id is None:
                patient_conn.contact_id = patient.id
                patient_conn.contact = patient
                patient_conn.save()
                # patient opted in subscribe them to timeline.
                # TODO: need to add per appointment/contact_type messages
                TimelineSubscription.objects.create(
                    timeline=timeline, start=edd_start, pin=name,
                    connection=patient_conn
                )
                mother_registered = True
            else:
                mother_registered = None
        else:
            patient_conn = mother_registered = None

        user = ' %s' % healthworker.name
        return {
            'user': user,
            'date': start,
            'name': name,
            'timeline': timeline.name,
            'patient_conn': patient_conn,
            'mother_registered': mother_registered,
            'location_name': healthworker.location.__unicode__(),
        }


class MwanaForm(HandlerForm):
    """Register a child and enroll on appropriate timeline dependent
    on mothers status."""

    date = forms.DateField(required=True, error_messages={
        'invalid': _('Sorry, Please use the DDMMYYYY format.')
    })
    mother_name = forms.CharField(error_messages={
        'required': _(
            'Sorry, you must provide the mothers firstname_lastname'
            ' or an id')
    })
    child_name = forms.CharField(error_messages={
        'required': _(
            'Sorry, you must provide the childs firstname_lastname'
            ' or an id')
    })
    volunteer = forms.CharField(required=False, max_length=15)

    def clean(self):
        "Check for previous subscription."
        timeline = self.cleaned_data.get('timeline', None)
        name = self.cleaned_data['child_name'].upper()
        mother_name = self.cleaned_data['mother_name'].upper()
        location = self.connection.contact.location
        if name is not None and timeline is not None and location is not None:
            previous = TimelineSubscription.objects.filter(
                Q(Q(end__isnull=True) | Q(end__gte=now())),
                timeline=timeline, connection=self.connection, pin=name
            )
            try:
                child = Contact.objects.get(parent__name=mother_name)
            except:
                child = None
            if previous.exists() and child is not None:
                prev_loc = previous[0].connection.contact.location
                location_name = location.__unicode__()
                if prev_loc.__unicode__() == location_name:
                    params = {'timeline': timeline.name,
                              'name': name,
                              'mother': mother_name,
                              'location': location_name}
                    message = _(
                        'Sorry, you previously registered a birth for '
                        '%(name)s born to %(mother)s at %(location)s. You will'
                        ' be notified when it is time for the next'
                        ' appointment.') % params
                raise forms.ValidationError(message)
        return self.cleaned_data

    def _get_backend(self, backend_name):
        """Returns a matching backend based on the name."""
        return Backend.objects.filter(name__iexact=backend_name)[0]

    def _validate_cell(self, num):
        if num is None:
            return None, False
        num = str(num)
        if num.strip().upper() in ['X', 'XX']:
            return None, False
        try:
            num = int(num)
        except ValueError:
            # register no number if not valid number
            return None, False
        # only accept 10 digit numbers for now
        if len(str(num)) == 9:
            if str(num)[:1] == '8':
                backend_name = 'tnm'
            elif str(num)[:1] == '9':
                backend_name = 'airtelsmpp'
            valid_cell = True
        else:
            backend_name = None
            valid_cell = False
        return backend_name, valid_cell

    def save(self):
        if not self.is_valid():
            return None
        timeline = self.cleaned_data['timeline']
        name = self.cleaned_data['child_name'].upper()
        if "_" in name:
            child_firstname, child_lastname = name.split("_")
        else:
            child_firstname = child_lastname = ''
        mother_name = self.cleaned_data['mother_name'].upper()
        if "_" in mother_name:
            mother_firstname, mother_lastname = mother_name.split("_")
        else:
            mother_firstname = mother_lastname = ''
        date = self.cleaned_data['date']
        healthworker = self.connection.contact
        location_id = self.connection.contact.location
        volunteer = self.cleaned_data['volunteer']
        v_backend_name, v_cell = self._validate_cell(volunteer)
        if v_cell:
            volunteer = "+265" + volunteer[1:]
            v_backend = self._get_backend(v_backend_name)
            v_conn = lookup_connections(backend=v_backend,
                                        identities=[volunteer])[0]
        else:
            v_conn = None
        if v_conn is not None:
            reminder_conn = v_conn
        else:
            reminder_conn = self.connection
        # subscribe to birth timeline
        TimelineSubscription.objects.create(
            timeline=timeline, start=date, pin=mother_name,
            connection=reminder_conn
        )

        if len(volunteer) < 2:
            volunteer = self.connection.identity
        # create the patient
        if healthworker is not None and location_id is not None:
            mother, created_mom = Contact.objects.get_or_create(
                name=mother_name,
                location=location_id,
                first_name=mother_firstname,
                last_name=mother_lastname,
                volunteer=volunteer
            )

            patient_t = const.get_patient_type()
            if not mother.types.filter(pk=patient_t.pk).count():
                mother.types.add(patient_t)

            # create and link child with mother
            child, created_child = Contact.objects.get_or_create(
                name=name,
                location=location_id,
                first_name=child_firstname,
                last_name=child_lastname,
                date_of_birth=date,
                parent=mother)

            child_t = const.get_child_type()
            if not child.types.filter(pk=child_t.pk).count():
                child.types.add(child_t)
            if not child.types.filter(pk=patient_t.pk).count():
                child.types.add(patient_t)

        user = ' %s' % healthworker.name
        return {
            'user': user,
            'date': date,
            'name': name,
            'timeline': timeline.name,
            'location_name': healthworker.location.name,
        }


class RefillForm(HandlerForm):
    name = forms.CharField(required=True, error_messages={
        'required': _(
            'Sorry, you must provide the mothers firstname_lastname'
            ' or an id')
    })

    date = forms.DateField(required=True, error_messages={
        'invalid': _('Sorry, Please use the YYYY-MM-DD format.')
    })

    def clean(self):
        "Check that mother is subscribed"
        timeline = self.cleaned_data.get('timeline', None)
        name = self.cleaned_data['name'].upper()
        if name is not None and timeline is not None:
            previous = TimelineSubscription.objects.filter(
                Q(Q(end__isnull=True) | Q(end__gte=now())),
                timeline=timeline, pin=name
            )
            if not previous.exists():
                params = {'timeline': timeline.name,
                          'name': name, }
                message = _(
                    'Sorry, we do not have '
                    '%(name)s registered for %(timeline)s. '
                    ' Please make sure they are registered'
                    ' first.') % params
                raise forms.ValidationError(message)
            else:
                self.cleaned_data['sub'] = previous[0]
        return self.cleaned_data

    def save(self):
        if not self.is_valid():
            return None
        # timeline = self.get_cleaned_data['timeline']
        name = self.cleaned_data['name'].upper()
        date = self.cleaned_data['date']
        sub = self.cleaned_data['sub']
        milestone, created = Milestone.objects.get(
            name="ART refill (Adhoc)")
        # create the appointment
        appt, created = Appointment.objects.get_or_create(
            subscription=sub,
            milestone=milestone,
            date=date
        )
        # return for response
        return {
            'date': date,
            'name': name, }


class StatusForm(HandlerForm):
    "Set the status of an appointment that a patient was seen"

    name = forms.CharField()
    status = forms.CharField()

    def clean_status(self):
        "Map values from inbound messages to Appointment.STATUS_CHOICES"
        raw_status = self.cleaned_data.get('status', '')
        valid_status_update = Appointment.STATUS_CHOICES[1:]
        status = next((x[0] for x in valid_status_update
                       if x[1].upper() == raw_status.upper()), None)
        if not status:
            choices = tuple([x[1].upper() for x in valid_status_update])
            params = {'choices': ', '.join(choices), 'raw_status': raw_status}
            msg = _('Sorry, the status update must be in %(choices)s. You '
                    'supplied %(raw_status)s') % params
            raise forms.ValidationError(msg)
        return status

    def clean_name(self):
        "Find the most recent appointment/trace for the patient."
        timeline = self.cleaned_data.get('timeline', None)
        name = self.cleaned_data.get('name', '').upper()
        # name should be a pin for an active timeline subscription
        timelines = TimelineSubscription.objects.filter(
            Q(Q(end__gte=now()) | Q(end__isnull=True)),
            timeline=timeline, connection=self.connection, pin=name
        ).values_list('timeline', flat=True)
        if not timelines:
            # PIN doesn't match an active subscription for this connection
            raise forms.ValidationError(_('Sorry, name/id does not match an '
                                          'active subscription.'))
        try:
            appointment = Appointment.objects.filter(
                status=Appointment.STATUS_DEFAULT,
                date__lte=now(),
                milestone__timeline__in=timelines
            ).order_by('-date')[0]
        except IndexError:
            # No recent appointment that is not STATUS_DEFAULT
            msg = _('Sorry, user has no recent appointments that require a '
                    'status update.')
            raise forms.ValidationError(msg)
        else:
            self.cleaned_data['appointment'] = appointment
        try:
            trace = PatientTrace.objects.filter(
                name=name, status='new',
                location=self.connection.contact.clinic)[0]
        except IndexError:
            # no trace for the patient was found
            msg = _('Sorry, %s has no trace request waiting for an '
                    'update.' % name)
            raise forms.ValidationError(msg)
        else:
            self.cleaned_data['trace'] = trace
        return name

    def save(self):
        "Mark the appointment/trace status and return it"
        if not self.is_valid():
            return None
        appointment = self.cleaned_data['appointment']
        appointment.status = self.cleaned_data['status']
        appointment.save()
        trace = self.cleaned_data['trace']
        trace.status = self.cleaned_data['status']
        trace.save()
        return {}


class QuitForm(HandlerForm):
    "Unsubscribes a user from a timeline by populating the end date."

    keyword = forms.CharField()
    name = forms.CharField(error_messages={
        'required': _('Sorry, you must include a name or id for your '
            'unsubscription.')
    })
    date = forms.DateTimeField(required=False, error_messages={
        'invalid': _('Sorry, we cannot understand that date format. '
            'For the best results please use the ISO YYYY-MM-DD format.')
    })

    def clean_keyword(self):
        "Check if this keyword is associated with any timeline."
        keyword = self.cleaned_data.get('keyword', '')
        match = None
        if keyword:
            # Query DB for valid keywords
            for timeline in Timeline.objects.filter(slug__icontains=keyword):
                if keyword.strip().lower() in timeline.keywords:
                    match = timeline
                    break
        if match is None:
            # Invalid keyword
            raise forms.ValidationError(_('Sorry, we could not find any appointments for '
                    'the keyword: %s') % keyword)
        else:
            self.cleaned_data['timeline'] = match
        return keyword

    def clean(self):
        "Check for previous subscription."
        timeline = self.cleaned_data.get('timeline', None)
        name = self.cleaned_data.get('name', None)
        if name is not None and timeline is not None:
            previous = TimelineSubscription.objects.filter(
                Q(Q(end__isnull=True) | Q(end__gte=now())),
                timeline=timeline, connection=self.connection, pin__iexact=name
            )
            if not previous.exists():
                params = {'timeline': timeline.name, 'name': name}
                message = _('Sorry, you have not registered a %(timeline)s for '
                        '%(name)s.') % params
                raise forms.ValidationError(message)
            self.cleaned_data['subscription'] = previous[0]
        return self.cleaned_data

    def save(self):
        if not self.is_valid():
            return None
        subscription = self.cleaned_data['subscription']
        name = self.cleaned_data['name']
        end = self.cleaned_data.get('date', now()) or now()
        user = ' %s' % self.connection.contact.name if self.connection.contact else ''
        subscription.end = end
        subscription.save()
        return {
            'user': user,
            'date': end,
            'name': name,
            'timeline': subscription.timeline.name,
        }


class PatientReportFilterForm(forms.Form):
    PATIENT_TYPES = [('child', 'Child'), ('patient', 'Mother')]
    name = forms.CharField(label='Patient ID', required=False)
    # reporter_id = forms.CharField(label='Reporter ID', required=False)
    types = forms.ChoiceField(choices=[('', 'All')] + PATIENT_TYPES,
                              label='Patient Type', required=False)
    # location = forms.ModelChoiceField()
    # status = forms.ChoiceField(choices=[('', '')] + .STATUS_CHOICES,
                               # required=False)

    def get_items(self):
        if self.is_valid():
            filters = dict([(k, v) for k, v in self.cleaned_data.iteritems()
                            if v])
            return Contact.objects.filter(**filters)
        return Contact.objects.none()


class BaseFilterForm(forms.Form):
    DISTRICTS = [(x, x) for x in settings.DISTRICTS]
    init_end = datetime.date.today()
    init_start = init_end - timedelta(days=30)
    locations = forms.MultipleChoiceField(choices=DISTRICTS,
                                          label='District', required=False)
    startdate = forms.DateField(required=False, initial=str(init_start),
                                widget=forms.HiddenInput(
                                    attrs={'id': 'startdate'}))
    enddate = forms.DateField(required=False, initial=str(init_end),
                              widget=forms.HiddenInput(
                                  attrs={'id': 'enddate'}))
    # hmis_code = forms.CharField(required=False, initial="HMIS CODE",
    # label='Facility (HMIS Code)')

    def clean(self):
        """Check that date values or set defaults"""
        startdate = self.cleaned_data.get('startdate', None)
        enddate = self.cleaned_data.get('enddata', None)
        if startdate is None and enddate is None:
            today = datetime.date.today()
            self.cleaned_data['enddate'] = today
            self.cleaned_data['startdate'] = today - timedelta(days=30)
        return self.cleaned_data


class ContactFilterForm(BaseFilterForm):
    def get_items(self):
        if self.is_valid():
            locations = self.cleaned_data.get('locations', None)
            startdate = self.cleaned_data['startdate']
            enddate = self.cleaned_data['enddate']
            # hmis_code = self.cleaned_data.get('hmis_code', None)
            qs = Contact.objects.filter(created_on__gte=startdate,
                                        created_on__lte=enddate)
            # if hmis_code is not None:
            # qs = qs.filter(location__slug=hmis_code)
            if "All" not in locations or locations is not None:
                q = Q()
                for v in locations:
                    q |= Q(location__parent__parent__name=v)
                return qs.filter(q).distinct()
            else:
                return qs
        return Contact.objects.none()


class DateFilterForm(forms.Form):
    init_end = datetime.date.today()
    init_start = init_end - timedelta(days=30)
    startdate = forms.DateField(required=False, initial=str(init_start),
                                widget=forms.HiddenInput(
                                    attrs={'id': 'startdate'}))
    enddate = forms.DateField(required=False, initial=str(init_end),
                              widget=forms.HiddenInput(
                                  attrs={'id': 'enddate'}))

    def clean(self):
        """Check that date values or set defaults"""
        startdate = self.cleaned_data.get('startdate', None)
        enddate = self.cleaned_data.get('enddata', None)
        if startdate is None and enddate is None:
            today = datetime.date.today()
            self.cleaned_data['enddate'] = today
            self.cleaned_data['startdate'] = today - timedelta(days=30)
        return self.cleaned_data
