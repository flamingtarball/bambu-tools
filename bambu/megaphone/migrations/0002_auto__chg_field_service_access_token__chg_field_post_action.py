# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Changing field 'Service.access_token'
        db.alter_column('megaphone_service', 'access_token', self.gf('django.db.models.fields.TextField')())

        # Renaming column for 'Post.action' to match new field type.
        db.rename_column('megaphone_post', 'action', 'action_id')
        # Changing field 'Post.action'
        db.alter_column('megaphone_post', 'action_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['megaphone.Action']))

        # Adding index on 'Post', fields ['action']
        db.create_index('megaphone_post', ['action_id'])


    def backwards(self, orm):
        
        # Removing index on 'Post', fields ['action']
        db.delete_index('megaphone_post', ['action_id'])

        # Changing field 'Service.access_token'
        db.alter_column('megaphone_service', 'access_token', self.gf('django.db.models.fields.CharField')(max_length=200))

        # Renaming column for 'Post.action' to match new field type.
        db.rename_column('megaphone_post', 'action_id', 'action')
        # Changing field 'Post.action'
        db.alter_column('megaphone_post', 'action', self.gf('django.db.models.fields.CharField')(max_length=50))


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
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'megaphone.action': {
            'Meta': {'object_name': 'Action'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message_template': ('django.db.models.fields.TextField', [], {'default': "'New {{ verbose_name }}: {{ title }} {{ url }}'"}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'service': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'actions'", 'to': "orm['megaphone.Service']"})
        },
        'megaphone.click': {
            'Meta': {'unique_together': "(('link', 'ip'),)", 'object_name': 'Click'},
            'clicks': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'link': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'clicks'", 'to': "orm['megaphone.Link']"})
        },
        'megaphone.link': {
            'Meta': {'object_name': 'Link'},
            'click_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'unique_click_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'url': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '255'})
        },
        'megaphone.post': {
            'Meta': {'unique_together': "(('action', 'object_id'),)", 'object_name': 'Post'},
            'action': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'messages'", 'to': "orm['megaphone.Action']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'sent': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'megaphone.service': {
            'Meta': {'ordering': "('identity',)", 'object_name': 'Service'},
            'access_token': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identity': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'provider': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'megaphone_services'", 'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['megaphone']
