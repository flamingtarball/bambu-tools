# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Upload'
        db.create_table('uploadify_upload', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('guid', self.gf('django.db.models.fields.CharField')(unique=True, max_length=36)),
            ('filename', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('uploadify', ['Upload'])


    def backwards(self, orm):
        
        # Deleting model 'Upload'
        db.delete_table('uploadify_upload')


    models = {
        'uploadify.upload': {
            'Meta': {'object_name': 'Upload'},
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'guid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '36'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['uploadify']
