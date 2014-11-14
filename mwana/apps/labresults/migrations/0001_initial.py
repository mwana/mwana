# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'SampleNotification'
        db.create_table(u'labresults_samplenotification', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('contact', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['rapidsms.Contact'])),
            ('location', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['locations.Location'])),
            ('count', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('count_in_text', self.gf('django.db.models.fields.CharField')(max_length=160, null=True, blank=True)),
            ('date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.utcnow)),
        ))
        db.send_create_signal(u'labresults', ['SampleNotification'])

        # Adding model 'Result'
        db.create_table(u'labresults_result', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sample_id', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('requisition_id', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('requisition_id_search', self.gf('django.db.models.fields.CharField')(max_length=50, db_index=True)),
            ('clinic_care_no', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('payload', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='lab_results', null=True, to=orm['labresults.Payload'])),
            ('clinic', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='lab_results', null=True, to=orm['locations.Location'])),
            ('clinic_code_unrec', self.gf('django.db.models.fields.CharField')(max_length=20, blank=True)),
            ('result', self.gf('django.db.models.fields.CharField')(max_length=1, blank=True)),
            ('result_detail', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('collected_on', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('entered_on', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('processed_on', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('notification_status', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('birthdate', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('child_age', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=4, decimal_places=1, blank=True)),
            ('child_age_unit', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('sex', self.gf('django.db.models.fields.CharField')(max_length=1, blank=True)),
            ('mother_age', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('collecting_health_worker', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('coll_hw_title', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('record_change', self.gf('django.db.models.fields.CharField')(max_length=6, null=True, blank=True)),
            ('old_value', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('verified', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('result_sent_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('arrival_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'labresults', ['Result'])

        # Adding model 'Payload'
        db.create_table(u'labresults_payload', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('incoming_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('auth_user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('version', self.gf('django.db.models.fields.CharField')(max_length=10, blank=True)),
            ('source', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('client_timestamp', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('info', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('parsed_json', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('validated_schema', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('raw', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'labresults', ['Payload'])

        # Adding model 'LabLog'
        db.create_table(u'labresults_lablog', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('message', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('level', self.gf('django.db.models.fields.CharField')(max_length=20, blank=True)),
            ('line', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('payload', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['labresults.Payload'])),
            ('raw', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'labresults', ['LabLog'])

        # Adding model 'PrintedResult'
        db.create_table(u'labresults_printedresult', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('result', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['labresults.Result'])),
            ('contact', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['rapidsms.Contact'])),
            ('times_printed', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'labresults', ['PrintedResult'])

        # Adding model 'PendingPinConnections'
        db.create_table(u'labresults_pendingpinconnections', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('connection', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['rapidsms.Connection'])),
            ('result', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['labresults.Result'])),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True)),
        ))
        db.send_create_signal(u'labresults', ['PendingPinConnections'])


    def backwards(self, orm):
        
        # Deleting model 'SampleNotification'
        db.delete_table(u'labresults_samplenotification')

        # Deleting model 'Result'
        db.delete_table(u'labresults_result')

        # Deleting model 'Payload'
        db.delete_table(u'labresults_payload')

        # Deleting model 'LabLog'
        db.delete_table(u'labresults_lablog')

        # Deleting model 'PrintedResult'
        db.delete_table(u'labresults_printedresult')

        # Deleting model 'PendingPinConnections'
        db.delete_table(u'labresults_pendingpinconnections')


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
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 5, 3, 23, 0, 55, 62732)'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 5, 3, 23, 0, 55, 62054)'}),
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
            'processed_on': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
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
            'pin': ('django.db.models.fields.CharField', [], {'max_length': '4', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'A'", 'max_length': '1'}),
            'types': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'contacts'", 'blank': 'True', 'to': u"orm['contactsplus.ContactType']"})
        }
    }

    complete_apps = ['labresults']
