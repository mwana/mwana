# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Timeline'
        db.create_table(u'appointments_timeline', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('slug', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal(u'appointments', ['Timeline'])

        # Adding model 'TimelineSubscription'
        db.create_table(u'appointments_timelinesubscription', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('timeline', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'subscribers', to=orm['appointments.Timeline'])),
            ('connection', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'timelines', to=orm['rapidsms.Connection'])),
            ('pin', self.gf('django.db.models.fields.CharField')(max_length=160)),
            ('start', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2014, 7, 8, 11, 8, 16, 13342))),
            ('end', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True)),
        ))
        db.send_create_signal(u'appointments', ['TimelineSubscription'])

        # Adding model 'Milestone'
        db.create_table(u'appointments_milestone', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('timeline', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'milestones', to=orm['appointments.Timeline'])),
            ('offset', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'appointments', ['Milestone'])

        # Adding model 'Appointment'
        db.create_table(u'appointments_appointment', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('milestone', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'milestone_appointments', to=orm['appointments.Milestone'])),
            ('subscription', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'appointments', to=orm['appointments.TimelineSubscription'])),
            ('date', self.gf('django.db.models.fields.DateField')()),
            ('confirmed', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('reschedule', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name=u'appointments', null=True, to=orm['appointments.Appointment'])),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('notes', self.gf('django.db.models.fields.CharField')(default=u'', max_length=160, blank=True)),
        ))
        db.send_create_signal(u'appointments', ['Appointment'])

        # Adding model 'Notification'
        db.create_table(u'appointments_notification', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('appointment', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'notifications', to=orm['appointments.Appointment'])),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('sent', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2014, 7, 8, 11, 8, 16, 9612), null=True, blank=True)),
            ('confirmed', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('message', self.gf('django.db.models.fields.CharField')(max_length=160)),
        ))
        db.send_create_signal(u'appointments', ['Notification'])


    def backwards(self, orm):
        
        # Deleting model 'Timeline'
        db.delete_table(u'appointments_timeline')

        # Deleting model 'TimelineSubscription'
        db.delete_table(u'appointments_timelinesubscription')

        # Deleting model 'Milestone'
        db.delete_table(u'appointments_milestone')

        # Deleting model 'Appointment'
        db.delete_table(u'appointments_appointment')

        # Deleting model 'Notification'
        db.delete_table(u'appointments_notification')


    models = {
        u'appointments.appointment': {
            'Meta': {'ordering': "[u'-date']", 'object_name': 'Appointment'},
            'confirmed': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'milestone': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'milestone_appointments'", 'to': u"orm['appointments.Milestone']"}),
            'notes': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '160', 'blank': 'True'}),
            'reschedule': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'appointments'", 'null': 'True', 'to': u"orm['appointments.Appointment']"}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'subscription': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'appointments'", 'to': u"orm['appointments.TimelineSubscription']"})
        },
        u'appointments.milestone': {
            'Meta': {'object_name': 'Milestone'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'offset': ('django.db.models.fields.IntegerField', [], {}),
            'timeline': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'milestones'", 'to': u"orm['appointments.Timeline']"})
        },
        u'appointments.notification': {
            'Meta': {'object_name': 'Notification'},
            'appointment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'notifications'", 'to': u"orm['appointments.Appointment']"}),
            'confirmed': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '160'}),
            'sent': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 7, 8, 11, 8, 16, 20551)', 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '1'})
        },
        u'appointments.timeline': {
            'Meta': {'object_name': 'Timeline'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'appointments.timelinesubscription': {
            'Meta': {'object_name': 'TimelineSubscription'},
            'connection': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'timelines'", 'to': u"orm['rapidsms.Connection']"}),
            'end': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pin': ('django.db.models.fields.CharField', [], {'max_length': '160'}),
            'start': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 7, 8, 11, 8, 16, 24156)'}),
            'timeline': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'subscribers'", 'to': u"orm['appointments.Timeline']"})
        },
        u'contactsplus.contacttype': {
            'Meta': {'object_name': 'ContactType'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        u'locations.location': {
            'Meta': {'object_name': 'Location'},
            'census': ('django.db.models.fields.IntegerField', [], {'default': '10000'}),
            'has_independent_printer': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['locations.Location']", 'null': 'True', 'blank': 'True'}),
            'point': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['locations.Point']", 'null': 'True', 'blank': 'True'}),
            'population': ('django.db.models.fields.IntegerField', [], {}),
            'send_live_results': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['locations.LocationType']"})
        },
        u'locations.locationtype': {
            'Meta': {'object_name': 'LocationType'},
            'exists_in': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['locations.Location']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'plural': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'singular': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'locations.point': {
            'Meta': {'object_name': 'Point'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.DecimalField', [], {'max_digits': '13', 'decimal_places': '10'}),
            'longitude': ('django.db.models.fields.DecimalField', [], {'max_digits': '13', 'decimal_places': '10'})
        },
        u'rapidsms.backend': {
            'Meta': {'object_name': 'Backend'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'})
        },
        u'rapidsms.connection': {
            'Meta': {'unique_together': "(('backend', 'identity'),)", 'object_name': 'Connection'},
            'backend': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['rapidsms.Backend']"}),
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['rapidsms.Contact']", 'null': 'True', 'blank': 'True'}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identity': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'rapidsms.contact': {
            'Meta': {'object_name': 'Contact'},
            'alias': ('django.db.models.fields.CharField', [], {'max_length': '100', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_of_birth': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'errors': ('django.db.models.fields.IntegerField', [], {'default': '0', 'max_length': '5'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interviewer_id': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_help_admin': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['locations.Location']", 'null': 'True', 'blank': 'True'}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['rapidsms.Contact']", 'null': 'True', 'blank': 'True'}),
            'pin': ('django.db.models.fields.CharField', [], {'max_length': '4', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'A'", 'max_length': '1'}),
            'types': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'contacts'", 'blank': 'True', 'to': u"orm['contactsplus.ContactType']"})
        }
    }

    complete_apps = ['appointments']
