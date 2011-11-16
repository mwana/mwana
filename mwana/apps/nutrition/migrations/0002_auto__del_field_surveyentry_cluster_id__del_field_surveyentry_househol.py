# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting field 'SurveyEntry.cluster_id'
        db.delete_column('nutrition_surveyentry', 'cluster_id')

        # Deleting field 'SurveyEntry.household_id'
        db.delete_column('nutrition_surveyentry', 'household_id')


    def backwards(self, orm):
        
        # Adding field 'SurveyEntry.cluster_id'
        db.add_column('nutrition_surveyentry', 'cluster_id', self.gf('django.db.models.fields.CharField')(max_length=25, null=True, blank=True), keep_default=False)

        # Adding field 'SurveyEntry.household_id'
        db.add_column('nutrition_surveyentry', 'household_id', self.gf('django.db.models.fields.CharField')(max_length=25, null=True, blank=True), keep_default=False)


    models = {
        'contactsplus.contacttype': {
            'Meta': {'object_name': 'ContactType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
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
        'nutrition.assessment': {
            'Meta': {'object_name': 'Assessment'},
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'healthworker': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Contact']", 'null': 'True'}),
            'height': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '4', 'decimal_places': '1', 'blank': 'True'}),
            'height4age': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '4', 'decimal_places': '2', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'muac': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '2', 'blank': 'True'}),
            'oedema': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'patient': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['people.Person']"}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'G'", 'max_length': '1'}),
            'survey': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['nutrition.Survey']"}),
            'weight': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '4', 'decimal_places': '1', 'blank': 'True'}),
            'weight4age': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '4', 'decimal_places': '2', 'blank': 'True'}),
            'weight4height': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '4', 'decimal_places': '2', 'blank': 'True'})
        },
        'nutrition.survey': {
            'Meta': {'object_name': 'Survey'},
            'avg_height4age': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '2', 'blank': 'True'}),
            'avg_weight4age': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '2', 'blank': 'True'}),
            'avg_weight4height': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '2', 'blank': 'True'}),
            'baseline_height4age': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '2', 'blank': 'True'}),
            'baseline_weight4age': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '2', 'blank': 'True'}),
            'baseline_weight4height': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '2', 'blank': 'True'}),
            'begin_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '160', 'null': 'True', 'blank': 'True'}),
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '160', 'null': 'True', 'blank': 'True'})
        },
        'nutrition.surveyentry': {
            'Meta': {'object_name': 'SurveyEntry'},
            'age_in_months': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True', 'blank': 'True'}),
            'child_id': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True', 'blank': 'True'}),
            'date_of_birth': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True', 'blank': 'True'}),
            'flag': ('django.db.models.fields.CharField', [], {'default': "'G'", 'max_length': '1'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True', 'blank': 'True'}),
            'healthworker_id': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True', 'blank': 'True'}),
            'height': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'muac': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'oedema': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'survey_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'weight': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True', 'blank': 'True'})
        },
        'people.person': {
            'Meta': {'object_name': 'Person'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'age_in_months': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'cluster_id': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_of_birth': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'household_id': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'people'", 'blank': 'True', 'to': "orm['locations.Location']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'reporter': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'people'", 'blank': 'True', 'to': "orm['rapidsms.Contact']"}),
            'status': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1000', 'blank': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['people.PersonType']"})
        },
        'people.persontype': {
            'Meta': {'object_name': 'PersonType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'plural': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'singular': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        },
        'rapidsms.contact': {
            'Meta': {'object_name': 'Contact'},
            'alias': ('django.db.models.fields.CharField', [], {'max_length': '100', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'errors': ('django.db.models.fields.IntegerField', [], {'default': '0', 'max_length': '5'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interviewer_id': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_help_admin': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Location']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'pin': ('django.db.models.fields.CharField', [], {'max_length': '4', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'A'", 'max_length': '1'}),
            'types': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'contacts'", 'blank': 'True', 'to': "orm['contactsplus.ContactType']"})
        }
    }

    complete_apps = ['nutrition']
