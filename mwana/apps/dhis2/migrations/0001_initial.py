# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Server'
        db.create_table(u'dhis2_server', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=160)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200)),
        ))
        db.send_create_signal(u'dhis2', ['Server'])

        # Adding model 'Indicator'
        db.create_table(u'dhis2_indicator', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('server', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dhis2.Server'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=160)),
            ('location', self.gf('django.db.models.fields.CharField')(max_length=4)),
            ('period', self.gf('django.db.models.fields.CharField')(max_length=4)),
            ('rule', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('dhis2_id', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal(u'dhis2', ['Indicator'])

        # Adding model 'Submission'
        db.create_table(u'dhis2_submission', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date_sent', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('indicator', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dhis2.Indicator'])),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=30)),
        ))
        db.send_create_signal(u'dhis2', ['Submission'])


    def backwards(self, orm):
        
        # Deleting model 'Server'
        db.delete_table(u'dhis2_server')

        # Deleting model 'Indicator'
        db.delete_table(u'dhis2_indicator')

        # Deleting model 'Submission'
        db.delete_table(u'dhis2_submission')


    models = {
        u'dhis2.indicator': {
            'Meta': {'object_name': 'Indicator'},
            'dhis2_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '4'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '160'}),
            'period': ('django.db.models.fields.CharField', [], {'max_length': '4'}),
            'rule': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'server': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dhis2.Server']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '500'})
        },
        u'dhis2.server': {
            'Meta': {'object_name': 'Server'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '160'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        u'dhis2.submission': {
            'Meta': {'object_name': 'Submission'},
            'date_sent': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'indicator': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dhis2.Indicator']"}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        }
    }

    complete_apps = ['dhis2']
