# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting field 'FloodReport.requested_by'
        db.delete_column(u'emergency_floodreport', 'requested_by_id')

        # Deleting field 'FloodReport.requested_on'
        db.delete_column(u'emergency_floodreport', 'requested_on')

        # Adding field 'FloodReport.reported_by'
        db.add_column(u'emergency_floodreport', 'reported_by', self.gf('django.db.models.fields.related.ForeignKey')(default=25, to=orm['rapidsms.Connection']), keep_default=False)

        # Adding field 'FloodReport.reported_on'
        db.add_column(u'emergency_floodreport', 'reported_on', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.utcnow), keep_default=False)


    def backwards(self, orm):
        
        # User chose to not deal with backwards NULL issues for 'FloodReport.requested_by'
        raise RuntimeError("Cannot reverse this migration. 'FloodReport.requested_by' and its values cannot be restored.")

        # Adding field 'FloodReport.requested_on'
        db.add_column(u'emergency_floodreport', 'requested_on', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.utcnow), keep_default=False)

        # Deleting field 'FloodReport.reported_by'
        db.delete_column(u'emergency_floodreport', 'reported_by_id')

        # Deleting field 'FloodReport.reported_on'
        db.delete_column(u'emergency_floodreport', 'reported_on')


    models = {
        u'contactsplus.contacttype': {
            'Meta': {'object_name': 'ContactType'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        u'emergency.floodreport': {
            'Meta': {'object_name': 'FloodReport'},
            'additional_text': ('django.db.models.fields.CharField', [], {'max_length': '160', 'null': 'True', 'blank': 'True'}),
            'addressed_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'comments': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'reported_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['rapidsms.Connection']"}),
            'reported_on': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
            'resolved_by': ('django.db.models.fields.CharField', [], {'max_length': '160', 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'P'", 'max_length': '1'})
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
            'types': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'contacts'", 'blank': 'True', 'to': u"orm['contactsplus.ContactType']"}),
            'volunteer': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['emergency']
