# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'FileUpload'
        db.create_table('smgl_fileupload', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('suggestion', self.gf('django.db.models.fields.related.ForeignKey')(related_name='attached_files', to=orm['smgl.Suggestion'])),
            ('posted_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('created_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('file', self.gf('django.db.models.fields.files.FileField')(max_length=255, null=True)),
        ))
        db.send_create_signal('smgl', ['FileUpload'])

        # Adding model 'Suggestion'
        db.create_table('smgl_suggestion', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('created_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('last_edited_time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('parent_suggestion', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smgl.Suggestion'], null=True, blank=True)),
            ('text', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('smgl', ['Suggestion'])

        # Adding M2M table for field authors on 'Suggestion'
        db.create_table('smgl_suggestion_authors', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('suggestion', models.ForeignKey(orm['smgl.suggestion'], null=False)),
            ('user', models.ForeignKey(orm['auth.user'], null=False))
        ))
        db.create_unique('smgl_suggestion_authors', ['suggestion_id', 'user_id'])


    def backwards(self, orm):
        
        # Deleting model 'FileUpload'
        db.delete_table('smgl_fileupload')

        # Deleting model 'Suggestion'
        db.delete_table('smgl_suggestion')

        # Removing M2M table for field authors on 'Suggestion'
        db.delete_table('smgl_suggestion_authors')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 12, 12, 13, 51, 43, 840014)'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 12, 12, 13, 51, 43, 839941)'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contactsplus.contacttype': {
            'Meta': {'ordering': "['name']", 'object_name': 'ContactType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'formplayer.xform': {
            'Meta': {'object_name': 'XForm'},
            'checksum': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'namespace': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'uiversion': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'version': ('django.db.models.fields.IntegerField', [], {'null': 'True'})
        },
        'locations.location': {
            'Meta': {'object_name': 'Location'},
            'has_independent_printer': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Location']", 'null': 'True', 'blank': 'True'}),
            'point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Point']", 'null': 'True', 'blank': 'True'}),
            'send_live_results': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.LocationType']"})
        },
        'locations.locationtype': {
            'Meta': {'object_name': 'LocationType'},
            'exists_in': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Location']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'plural': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'singular': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'locations.point': {
            'Meta': {'object_name': 'Point'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.DecimalField', [], {'max_digits': '13', 'decimal_places': '10'}),
            'longitude': ('django.db.models.fields.DecimalField', [], {'max_digits': '13', 'decimal_places': '10'})
        },
        'messagelog.message': {
            'Meta': {'object_name': 'Message'},
            'connection': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Connection']", 'null': 'True'}),
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Contact']", 'null': 'True'}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'direction': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {})
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
            'alias': ('django.db.models.fields.CharField', [], {'max_length': '100', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'created_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_help_admin': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_super_user': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Location']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'pin': ('django.db.models.fields.CharField', [], {'max_length': '4', 'blank': 'True'}),
            'return_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'types': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'contacts'", 'blank': 'True', 'to': "orm['contactsplus.ContactType']"}),
            'unique_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'unique': 'True', 'null': 'True', 'blank': 'True'})
        },
        'smgl.ambulancerequest': {
            'Meta': {'object_name': 'AmbulanceRequest'},
            'ambulance_driver': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'ambulance_driver'", 'null': 'True', 'to': "orm['rapidsms.Contact']"}),
            'form_id': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mother': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smgl.PregnantMother']", 'null': 'True', 'blank': 'True'}),
            'mother_uid': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'other_recipient': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'other_recipient'", 'null': 'True', 'to': "orm['rapidsms.Contact']"}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smsforms.XFormsSession']"}),
            'triage_nurse': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'triage_nurse'", 'null': 'True', 'to': "orm['rapidsms.Contact']"})
        },
        'smgl.ambulanceresponse': {
            'Meta': {'object_name': 'AmbulanceResponse'},
            'ambulance_request': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smgl.AmbulanceRequest']", 'null': 'True', 'blank': 'True'}),
            'form_id': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mother': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smgl.PregnantMother']", 'null': 'True', 'blank': 'True'}),
            'mother_uid': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'responded_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'responder': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Contact']"}),
            'response': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smsforms.XFormsSession']"})
        },
        'smgl.birthregistration': {
            'Meta': {'object_name': 'BirthRegistration'},
            'complications': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'connection': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Connection']"}),
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Contact']", 'null': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'district': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'birth_district'", 'null': 'True', 'to': "orm['locations.Location']"}),
            'facility': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'birth_facility'", 'null': 'True', 'to': "orm['locations.Location']"}),
            'form_id': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'birth_location'", 'null': 'True', 'to': "orm['locations.Location']"}),
            'mother': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smgl.PregnantMother']", 'null': 'True', 'blank': 'True'}),
            'number': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'place': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smsforms.XFormsSession']"})
        },
        'smgl.deathregistration': {
            'Meta': {'object_name': 'DeathRegistration'},
            'connection': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Connection']"}),
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Contact']", 'null': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'district': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'death_district'", 'null': 'True', 'to': "orm['locations.Location']"}),
            'facility': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'death_facility'", 'null': 'True', 'to': "orm['locations.Location']"}),
            'form_id': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'death_location'", 'null': 'True', 'to': "orm['locations.Location']"}),
            'person': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'place': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smsforms.XFormsSession']"}),
            'unique_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'smgl.facilityvisit': {
            'Meta': {'object_name': 'FacilityVisit'},
            'baby_status': ('django.db.models.fields.CharField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'}),
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Contact']"}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'district': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'district_location'", 'null': 'True', 'to': "orm['locations.Location']"}),
            'edd': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Location']"}),
            'mother': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'facility_visits'", 'to': "orm['smgl.PregnantMother']"}),
            'mother_status': ('django.db.models.fields.CharField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'}),
            'next_visit': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'reason_for_visit': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'referred': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reminded': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'visit_date': ('django.db.models.fields.DateField', [], {}),
            'visit_type': ('django.db.models.fields.CharField', [], {'default': "'anc'", 'max_length': '255'})
        },
        'smgl.fileupload': {
            'Meta': {'object_name': 'FileUpload'},
            'created_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '255', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'posted_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'suggestion': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'attached_files'", 'to': "orm['smgl.Suggestion']"})
        },
        'smgl.pregnantmother': {
            'Meta': {'object_name': 'PregnantMother'},
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Contact']"}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'edd': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '160'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '160'}),
            'lmp': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Location']"}),
            'next_visit': ('django.db.models.fields.DateField', [], {}),
            'reason_for_visit': ('django.db.models.fields.CharField', [], {'max_length': '160'}),
            'reminded': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'risk_reason_cmp': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'risk_reason_csec': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'risk_reason_gd': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'risk_reason_hbp': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'risk_reason_none': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'risk_reason_oth': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'risk_reason_psb': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'uid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '160'}),
            'zone': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'pregnant_mother_zones'", 'null': 'True', 'to': "orm['locations.Location']"})
        },
        'smgl.preregistration': {
            'Meta': {'object_name': 'PreRegistration'},
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Contact']", 'null': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'has_confirmed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'english'", 'max_length': '255'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Location']"}),
            'phone_number': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'unique_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'zone': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'})
        },
        'smgl.referral': {
            'Meta': {'object_name': 'Referral'},
            'amb_req': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smgl.AmbulanceRequest']", 'null': 'True', 'blank': 'True'}),
            'baby_outcome': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'facility': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Location']"}),
            'form_id': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'from_facility': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'referrals_made'", 'null': 'True', 'to': "orm['locations.Location']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mode_of_delivery': ('django.db.models.fields.CharField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'}),
            'mother': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smgl.PregnantMother']", 'null': 'True', 'blank': 'True'}),
            'mother_outcome': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'mother_showed': ('django.db.models.fields.NullBooleanField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'mother_uid': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'reason_aph': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reason_cpd': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reason_ec': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reason_fd': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reason_hbp': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reason_oth': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reason_pec': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reason_pl': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reason_pp': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reason_pph': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reminded': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'responded': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smsforms.XFormsSession']"}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.TimeField', [], {'null': 'True'})
        },
        'smgl.remindernotification': {
            'Meta': {'object_name': 'ReminderNotification'},
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mother': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smgl.PregnantMother']", 'null': 'True', 'blank': 'True'}),
            'mother_uid': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sent_notifications'", 'to': "orm['rapidsms.Contact']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'smgl.suggestion': {
            'Meta': {'ordering': "('-last_edited_time', '-created_time')", 'object_name': 'Suggestion'},
            'authors': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'symmetrical': 'False'}),
            'created_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_edited_time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'parent_suggestion': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smgl.Suggestion']", 'null': 'True', 'blank': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'smgl.syphilistest': {
            'Meta': {'object_name': 'SyphilisTest'},
            'date': ('django.db.models.fields.DateField', [], {}),
            'district': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Location']", 'null': 'True', 'blank': 'True'}),
            'form_id': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mother': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smgl.PregnantMother']", 'null': 'True', 'blank': 'True'}),
            'mother_uid': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'result': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smsforms.XFormsSession']"})
        },
        'smgl.syphilistreatment': {
            'Meta': {'object_name': 'SyphilisTreatment'},
            'date': ('django.db.models.fields.DateField', [], {}),
            'district': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Location']", 'null': 'True', 'blank': 'True'}),
            'form_id': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mother': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smgl.PregnantMother']", 'null': 'True', 'blank': 'True'}),
            'mother_uid': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'next_visit_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'reminded': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smsforms.XFormsSession']"}),
            'shot_number': ('django.db.models.fields.CharField', [], {'max_length': '2'})
        },
        'smgl.toldreminder': {
            'Meta': {'object_name': 'ToldReminder'},
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Contact']", 'null': 'True'}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'form_id': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mother': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smgl.PregnantMother']", 'null': 'True', 'blank': 'True'}),
            'mother_uid': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smsforms.XFormsSession']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '3'})
        },
        'smgl.xformkeywordhandler': {
            'Meta': {'ordering': "['keyword']", 'object_name': 'XFormKeywordHandler'},
            'function_path': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'keyword': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'smsforms.decisiontrigger': {
            'Meta': {'object_name': 'DecisionTrigger'},
            'context_data': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'final_response': ('django.db.models.fields.CharField', [], {'max_length': '160', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'trigger_keyword': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'xform': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['formplayer.XForm']"})
        },
        'smsforms.xformssession': {
            'Meta': {'object_name': 'XFormsSession'},
            'cancelled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'connection': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'xform_sessions'", 'to': "orm['rapidsms.Connection']"}),
            'end_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'ended': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'error_msg': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'has_error': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message_incoming': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'message_incoming'", 'null': 'True', 'to': "orm['messagelog.Message']"}),
            'message_outgoing': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'message_outgoing'", 'null': 'True', 'to': "orm['messagelog.Message']"}),
            'modified_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'select_text_mode': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'session_id': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'trigger': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smsforms.DecisionTrigger']"})
        },
        'taggit.tag': {
            'Meta': {'object_name': 'Tag'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100', 'db_index': 'True'})
        },
        'taggit.taggeditem': {
            'Meta': {'object_name': 'TaggedItem'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'taggit_taggeditem_tagged_items'", 'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'taggit_taggeditem_items'", 'to': "orm['taggit.Tag']"})
        }
    }

    complete_apps = ['smgl']
