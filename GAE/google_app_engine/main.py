from google.appengine.api import users
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
import webapp2
from os import path
from google.appengine.ext.webapp.template import render
from google.appengine.ext.webapp.xmpp_handlers import BaseHandler
from google.appengine.ext import db


#This is the model for storing the file information
class FileInfo(db.Model):
  blob = blobstore.BlobReferenceProperty(required=True) #Add references to blobs to domain models using BlobReferenceProperty:
  uploaded_by = db.UserProperty(required=True) #A user property.
  uploaded_at = db.DateTimeProperty(required=True, auto_now_add=True)# Construct a DateTimeProperty


class FileUploadFormHandler(BaseHandler):
  #@util.login_required #You have to be logged in to upload a file, unfortunatly this gave me errors so I commented it out
  def get(self):
    files_info = FileInfo.all().order('-uploaded_at').fetch(10)
    if(files_info is ""):
      self.response.out.write("""
      <html>
      <body> No files</body></html>""")
    else:
       user = users.get_current_user()
       context = {
            'user': user,
            'files_info': files_info,
            'form_url': blobstore.create_upload_url('/upload'),
            'download_url': '/downloadChecked',
            'logout_url': users.create_logout_url('/'),
       }
       tmpl = path.join(path.dirname(__file__), 'static/html/index.html')
       self.response.write(render(tmpl, context))
         #self.template.render(tmpl,context)

#This code handles the upload of files.
class FileUploadHandler(blobstore_handlers.BlobstoreUploadHandler):
  #You have to be logged in to upload a file
  def post(self):
    blob_info = self.get_uploads()[0]#Get uploads sent to this handler. Blobstore API only allows for one upload file so this will get a single file to upload
    if not users.get_current_user(): #Get current user
      blob_info.delete()
      self.redirect(users.create_login_url("/")) # Issues an HTTP redirect to the given relative URI.
      return
    user = users.get_current_user()
    file_info = FileInfo(blob=blob_info.key(),uploaded_by=user)
    db.put(file_info)
    #self.redirect("/file/%d" % (file_info.key().id(),))
    #self.redirect("/" % (file_info.key().id(),))
    self.redirect("/")


class FileDownloadHandler(blobstore_handlers.BlobstoreDownloadHandler):
#You have to be logged in to download a file
  def get(self, file_id):
    file_info = FileInfo.get_by_id(long(file_id))
    if not file_info or not file_info.blob:
      self.error(404)
      return
    self.send_blob(file_info.blob, save_as=True)

class CheckedFileDownloadHandler(BaseHandler):
     def post(self):
         checkedBoxes = self.request.get('fileChecked', allow_multiple=True)
         #Loop through checkedboxes so multiple files could be downloaded, unfortunatly this did not work and the user can only download one file.
         for check in checkedBoxes:
            self.redirect("/file/%s/download" % check)
            # print self.redirect("/file/5676073085829120/download")



app = webapp2.WSGIApplication([
    ('/', FileUploadFormHandler),
    ('/upload', FileUploadHandler),
    ('/downloadChecked', CheckedFileDownloadHandler),
    ('/file/([^/]+)?/download', FileDownloadHandler), #Regex used because the file id could be any amount of number or letters.
], debug=True)
# [END all]