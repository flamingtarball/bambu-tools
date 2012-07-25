# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Task'
        db.create_table('tasks_task', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('function', self.gf('django.db.models.fields.TextField')()),
            ('arguments', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('keyword_arguments', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('state', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('success_callback_function', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('success_callback_arguments', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('success_callback_keyword_arguments', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('failure_callback_function', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('failure_callback_arguments', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('failure_callback_keyword_arguments', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('tasks', ['Task'])


    def backwards(self, orm):
        
        # Deleting model 'Task'
        db.delete_table('tasks_task')


    models = {
        'tasks.task': {
            'Meta': {'ordering': "('created',)", 'object_name': 'Task'},
            'arguments': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'failure_callback_arguments': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'failure_callback_function': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'failure_callback_keyword_arguments': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'function': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'keyword_arguments': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'success_callback_arguments': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'success_callback_function': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'success_callback_keyword_arguments': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['tasks']
