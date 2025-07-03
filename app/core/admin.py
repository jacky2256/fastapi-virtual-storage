# app/admin.py
from sqladmin import Admin, ModelView
from app.db.session import sessionmanager
from app.db.models import Folder, File, ResourceArchive

class FolderAdmin(ModelView, model=Folder):
    column_list = [
        Folder.id, Folder.name, Folder.virtual_path, Folder.parent_id, Folder.created_at,
        Folder.storage_path, Folder.creator_user_id, Folder.access_url, Folder.is_published,
    ]
    column_searchable_list = [Folder.name, Folder.virtual_path]
    # column_filters = [Folder.is_published]

class FileAdmin(ModelView, model=File):
    column_list = [
        File.id, File.name, File.mime_type, File.size_bytes, File.folder_id, File.created_at,
        File.storage_path, File.virtual_path, File.uploader_user_id, File.access_url,
    ]

class ResourceArchiveAdmin(ModelView, model=ResourceArchive):
    column_list = [ResourceArchive.id, ResourceArchive.folder_id, ResourceArchive.size, ResourceArchive.file_count, ResourceArchive.created_at]

def init_admin(app):
    # engine — это AsyncEngine из sessionmanager._engine
    admin = Admin(app, sessionmanager._engine, title="Virtual Storage Admin")
    admin.add_view(FolderAdmin)
    admin.add_view(FileAdmin)
    admin.add_view(ResourceArchiveAdmin)
