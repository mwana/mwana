# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'XFormKeywordHandler.function_name'
        db.delete_column('smgl_xformkeywordhandler', 'function_name')

        # Adding field 'XFormKeywordHandler.function_path'
        db.add_column('smgl_xformkeywordhandler', 'function_path',
                      self.gf('django.db.models.fields.CharField')(default='path', max_length=255),
                      keep_default=False)

    def backwards(self, orm):

        # User chose to not deal with backwards NULL issues for 'XFormKeywordHandler.function_name'
        raise RuntimeError("Cannot reverse this migration. 'XFormKeywordHandler.function_name' and its values cannot be restored.")
        # Deleting field 'XFormKeywordHandler.function_path'
        db.delete_column('smgl_xformkeywordhandler', 'function_path')

    models = {
        'smgl.xformkeywordhandler': {
            'Meta': {'object_name': 'XFormKeywordHandler'},
            'function_path': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'keyword': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['smgl']