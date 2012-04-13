# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'XFormKeywordHandler'
        db.create_table('smgl_xformkeywordhandler', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('keyword', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('function_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('smgl', ['XFormKeywordHandler'])

    def backwards(self, orm):
        # Deleting model 'XFormKeywordHandler'
        db.delete_table('smgl_xformkeywordhandler')

    models = {
        'smgl.xformkeywordhandler': {
            'Meta': {'object_name': 'XFormKeywordHandler'},
            'function_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'keyword': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['smgl']