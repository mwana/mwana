# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'EIDConfirmation.reported_on'
        db.add_column(u'labresults_eidconfirmation', 'reported_on',
                      self.gf('django.db.models.fields.DateField')(auto_now_add=True, default=datetime.datetime(2015, 8, 23, 0, 0), blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'EIDConfirmation.reported_on'
        db.delete_column(u'labresults_eidconfirmation', 'reported_on')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contactsplus.contacttype': {
            'Meta': {'object_name': 'ContactType'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'labresults.eidconfirmation': {
            'Meta': {'object_name': 'EIDConfirmation'},
            'action_taken': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'age_in_months': ('django.db.models.fields.IntegerField', [], {'max_length': '2', 'null': 'True'}),
            'art_number': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['rapidsms.Contact']", 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reported_on': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'result': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['labresults.Result']", 'null': 'True'}),
            'sample': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        },
        u'labresults.lablog': {
            'Meta': {'object_name': 'LabLog'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'line': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'payload': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['labresults.Payload']"}),
            'raw': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        u'labresults.payload': {
            'Meta': {'object_name': 'Payload'},
            'auth_user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'client_timestamp': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'incoming_date': ('django.db.models.fields.DateTimeField', [], {}),
            'info': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'parsed_json': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'raw': ('django.db.models.fields.TextField', [], {}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'validated_schema': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        u'labresults.pendingpinconnections': {
            'Meta': {'object_name': 'PendingPinConnections'},
            'connection': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['rapidsms.Connection']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'result': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['labresults.Result']"}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'})
        },
        u'labresults.printedresult': {
            'Meta': {'object_name': 'PrintedResult'},
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['rapidsms.Contact']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'result': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['labresults.Result']"}),
            'times_printed': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        u'labresults.result': {
            'Meta': {'ordering': "('collected_on', 'requisition_id')", 'object_name': 'Result'},
            'arrival_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'birthdate': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'carer_phone': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'child_age': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '4', 'decimal_places': '1', 'blank': 'True'}),
            'child_age_unit': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'clinic': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'lab_results'", 'null': 'True', 'to': u"orm['locations.Location']"}),
            'clinic_care_no': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'clinic_code_unrec': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'coll_hw_title': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'collected_on': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'collecting_health_worker': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'entered_on': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mother_age': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'notification_status': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'old_value': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'payload': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'lab_results'", 'null': 'True', 'to': u"orm['labresults.Payload']"}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'processed_on': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'receipt_confirmed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'result_connections'", 'null': 'True', 'to': u"orm['rapidsms.Connection']"}),
            'record_change': ('django.db.models.fields.CharField', [], {'max_length': '6', 'null': 'True', 'blank': 'True'}),
            'requisition_id': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'requisition_id_search': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'result': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'result_detail': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'result_sent_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'sample_id': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'sex': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'verified': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'})
        },
        u'labresults.samplenotification': {
            'Meta': {'object_name': 'SampleNotification'},
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['rapidsms.Contact']"}),
            'count': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'count_in_text': ('django.db.models.fields.CharField', [], {'max_length': '160', 'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['locations.Location']"})
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

    complete_apps = ['labresults']