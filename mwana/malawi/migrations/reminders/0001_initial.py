# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Event'
        db.create_table('reminders_event', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('slug', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('gender', self.gf('django.db.models.fields.CharField')(max_length=1, blank=True)),
        ))
        db.send_create_signal('reminders', ['Event'])

        # Adding model 'Appointment'
        db.create_table('reminders_appointment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('event', self.gf('django.db.models.fields.related.ForeignKey')(related_name='appointments', to=orm['reminders.Event'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('num_days', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('reminders', ['Appointment'])

        # Adding model 'PatientEvent'
        db.create_table('reminders_patientevent', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('patient', self.gf('django.db.models.fields.related.ForeignKey')(related_name='patient_events', to=orm['rapidsms.Contact'])),
            ('event', self.gf('django.db.models.fields.related.ForeignKey')(related_name='patient_events', to=orm['reminders.Event'])),
            ('cba_conn', self.gf('django.db.models.fields.related.ForeignKey')(related_name='cba_patient_events', to=orm['rapidsms.Connection'])),
            ('date', self.gf('django.db.models.fields.DateField')()),
            ('date_logged', self.gf('django.db.models.fields.DateTimeField')()),
            ('notification_status', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('notification_sent_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal('reminders', ['PatientEvent'])

        # Adding unique constraint on 'PatientEvent', fields ['patient', 'event', 'date']
        db.create_unique('reminders_patientevent', ['patient_id', 'event_id', 'date'])

        # Adding model 'SentNotification'
        db.create_table('reminders_sentnotification', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('appointment', self.gf('django.db.models.fields.related.ForeignKey')(related_name='sent_notifications', to=orm['reminders.Appointment'])),
            ('patient_event', self.gf('django.db.models.fields.related.ForeignKey')(related_name='sent_notifications', to=orm['reminders.PatientEvent'])),
            ('recipient', self.gf('django.db.models.fields.related.ForeignKey')(related_name='sent_notifications', to=orm['rapidsms.Connection'])),
            ('date_logged', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal('reminders', ['SentNotification'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'PatientEvent', fields ['patient', 'event', 'date']
        db.delete_unique('reminders_patientevent', ['patient_id', 'event_id', 'date'])

        # Deleting model 'Event'
        db.delete_table('reminders_event')

        # Deleting model 'Appointment'
        db.delete_table('reminders_appointment')

        # Deleting model 'PatientEvent'
        db.delete_table('reminders_patientevent')

        # Deleting model 'SentNotification'
        db.delete_table('reminders_sentnotification')


    models = {
        'contactsplus.contacttype': {
            'Meta': {'object_name': 'ContactType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        'locations.location': {
            'Meta': {'object_name': 'Location'},
            'has_independent_printer': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Location']", 'null': 'True', 'blank': 'True'}),
            'point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Point']", 'null': 'True', 'blank': 'True'}),
            'population': ('django.db.models.fields.IntegerField', [], {}),
            'send_live_results': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.LocationType']"})
        },
        'locations.locationtype': {
            'Meta': {'object_name': 'LocationType'},
            'exists_in': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Location']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'plural': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'singular': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'locations.point': {
            'Meta': {'object_name': 'Point'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.DecimalField', [], {'max_digits': '13', 'decimal_places': '10'}),
            'longitude': ('django.db.models.fields.DecimalField', [], {'max_digits': '13', 'decimal_places': '10'})
        },
        'rapidsms.backend': {
            'Meta': {'object_name': 'Backend'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'})
        },
        'rapidsms.connection': {
            'Meta': {'object_name': 'Connection'},
            'backend': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Backend']"}),
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Contact']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identity': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'rapidsms.contact': {
            'Meta': {'object_name': 'Contact'},
            'alias': ('django.db.models.fields.CharField', [], {'max_length': '100', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'errors': ('django.db.models.fields.IntegerField', [], {'default': '0', 'max_length': '5'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interviewer_id': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_help_admin': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Location']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'pin': ('django.db.models.fields.CharField', [], {'max_length': '4', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'A'", 'max_length': '1'}),
            'types': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'contacts'", 'blank': 'True', 'to': "orm['contactsplus.ContactType']"})
        },
        'reminders.appointment': {
            'Meta': {'object_name': 'Appointment'},
            'event': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'appointments'", 'to': "orm['reminders.Event']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'num_days': ('django.db.models.fields.IntegerField', [], {})
        },
        'reminders.event': {
            'Meta': {'object_name': 'Event'},
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'reminders.patientevent': {
            'Meta': {'unique_together': "(('patient', 'event', 'date'),)", 'object_name': 'PatientEvent'},
            'cba_conn': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'cba_patient_events'", 'to': "orm['rapidsms.Connection']"}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'date_logged': ('django.db.models.fields.DateTimeField', [], {}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'patient_events'", 'to': "orm['reminders.Event']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notification_sent_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'notification_status': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'patient': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'patient_events'", 'to': "orm['rapidsms.Contact']"})
        },
        'reminders.sentnotification': {
            'Meta': {'object_name': 'SentNotification'},
            'appointment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sent_notifications'", 'to': "orm['reminders.Appointment']"}),
            'date_logged': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'patient_event': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sent_notifications'", 'to': "orm['reminders.PatientEvent']"}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sent_notifications'", 'to': "orm['rapidsms.Connection']"})
        }
    }

    complete_apps = ['reminders']
