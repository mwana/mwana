# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'DHIS2User'
        db.create_table(u'dhis2_dhis2user', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('username', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal(u'dhis2', ['DHIS2User'])

        # Adding field 'Server.user'
        db.add_column(u'dhis2_server', 'user', self.gf('django.db.models.fields.related.ForeignKey')(default=0, to=orm['dhis2.DHIS2User']), keep_default=False)


    def backwards(self, orm):
        
        # Deleting model 'DHIS2User'
        db.delete_table(u'dhis2_dhis2user')

        # Deleting field 'Server.user'
        db.delete_column(u'dhis2_server', 'user_id')


    models = {
        u'dhis2.dhis2user': {
            'Meta': {'object_name': 'DHIS2User'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
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
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dhis2.DHIS2User']"})
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
