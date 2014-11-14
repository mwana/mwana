# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'DHIS2User.password_salt'
        db.add_column(u'dhis2_dhis2user', 'password_salt', self.gf('django.db.models.fields.CharField')(max_length=8, null=True), keep_default=False)

        # Adding field 'DHIS2User.password_hash'
        db.add_column(u'dhis2_dhis2user', 'password_hash', self.gf('django.db.models.fields.CharField')(max_length=40, null=True), keep_default=False)

        # Adding field 'DHIS2User.name'
        db.add_column(u'dhis2_dhis2user', 'name', self.gf('django.db.models.fields.TextField')(default=''), keep_default=False)

        # Changing field 'DHIS2User.username'
        db.alter_column(u'dhis2_dhis2user', 'username', self.gf('django.db.models.fields.CharField')(max_length=100, null=True))

        # Changing field 'DHIS2User.password'
        db.alter_column(u'dhis2_dhis2user', 'password', self.gf('django.db.models.fields.CharField')(max_length=50, null=True))


    def backwards(self, orm):
        
        # Deleting field 'DHIS2User.password_salt'
        db.delete_column(u'dhis2_dhis2user', 'password_salt')

        # Deleting field 'DHIS2User.password_hash'
        db.delete_column(u'dhis2_dhis2user', 'password_hash')

        # Deleting field 'DHIS2User.name'
        db.delete_column(u'dhis2_dhis2user', 'name')

        # Changing field 'DHIS2User.username'
        db.alter_column(u'dhis2_dhis2user', 'username', self.gf('django.db.models.fields.CharField')(default='', max_length=100))

        # Changing field 'DHIS2User.password'
        db.alter_column(u'dhis2_dhis2user', 'password', self.gf('django.db.models.fields.CharField')(default='', max_length=50))


    models = {
        u'dhis2.dhis2user': {
            'Meta': {'object_name': 'DHIS2User'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'password_hash': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True'}),
            'password_salt': ('django.db.models.fields.CharField', [], {'max_length': '8', 'null': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
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
