# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Timeline'
        db.create_table('appointments_timeline', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('slug', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('appointments', ['Timeline'])

        # Adding model 'TimelineSubscription'
        db.create_table('appointments_timelinesubscription', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('timeline', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'subscribers', to=orm['appointments.Timeline'])),
            ('connection', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'timelines', to=orm['rapidsms.Connection'])),
            ('pin', self.gf('django.db.models.fields.CharField')(max_length=160)),
            ('start', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('end', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True)),
        ))
        db.send_create_signal('appointments', ['TimelineSubscription'])

        # Adding model 'Milestone'
        db.create_table('appointments_milestone', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('timeline', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'milestones', to=orm['appointments.Timeline'])),
            ('offset', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('appointments', ['Milestone'])

        # Adding model 'Appointment'
        db.create_table('appointments_appointment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('milestone', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'appointments', to=orm['appointments.Milestone'])),
            ('connection', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'appointments', to=orm['rapidsms.Connection'])),
            ('date', self.gf('django.db.models.fields.DateField')()),
            ('confirmed', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('reschedule', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name=u'appointments', null=True, to=orm['appointments.Appointment'])),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('notes', self.gf('django.db.models.fields.CharField')(default=u'', max_length=160, blank=True)),
        ))
        db.send_create_signal('appointments', ['Appointment'])

        # Adding model 'Notification'
        db.create_table('appointments_notification', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('appointment', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'notifications', to=orm['appointments.Appointment'])),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('sent', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, null=True, blank=True)),
            ('confirmed', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('message', self.gf('django.db.models.fields.CharField')(max_length=160)),
        ))
        db.send_create_signal('appointments', ['Notification'])


    def backwards(self, orm):
        # Deleting model 'Timeline'
        db.delete_table('appointments_timeline')

        # Deleting model 'TimelineSubscription'
        db.delete_table('appointments_timelinesubscription')

        # Deleting model 'Milestone'
        db.delete_table('appointments_milestone')

        # Deleting model 'Appointment'
        db.delete_table('appointments_appointment')

        # Deleting model 'Notification'
        db.delete_table('appointments_notification')


    models = {
        'appointments.appointment': {
            'Meta': {'ordering': "[u'-date']", 'object_name': 'Appointment'},
            'confirmed': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'connection': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'appointments'", 'to': "orm['rapidsms.Connection']"}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'milestone': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'appointments'", 'to': "orm['appointments.Milestone']"}),
            'notes': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '160', 'blank': 'True'}),
            'reschedule': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'appointments'", 'null': 'True', 'to': "orm['appointments.Appointment']"}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '1'})
        },
        'appointments.milestone': {
            'Meta': {'object_name': 'Milestone'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'offset': ('django.db.models.fields.IntegerField', [], {}),
            'timeline': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'milestones'", 'to': "orm['appointments.Timeline']"})
        },
        'appointments.notification': {
            'Meta': {'object_name': 'Notification'},
            'appointment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'notifications'", 'to': "orm['appointments.Appointment']"}),
            'confirmed': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '160'}),
            'sent': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '1'})
        },
        'appointments.timeline': {
            'Meta': {'object_name': 'Timeline'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'appointments.timelinesubscription': {
            'Meta': {'object_name': 'TimelineSubscription'},
            'connection': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'timelines'", 'to': "orm['rapidsms.Connection']"}),
            'end': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pin': ('django.db.models.fields.CharField', [], {'max_length': '160'}),
            'start': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'timeline': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'subscribers'", 'to': "orm['appointments.Timeline']"})
        },
        'rapidsms.backend': {
            'Meta': {'object_name': 'Backend'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'})
        },
        'rapidsms.connection': {
            'Meta': {'unique_together': "(('backend', 'identity'),)", 'object_name': 'Connection'},
            'backend': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Backend']"}),
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Contact']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identity': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'rapidsms.contact': {
            'Meta': {'object_name': 'Contact'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
        }
    }

    complete_apps = ['appointments']