import os
import sys
import errno
import digitalocean
import time
from fuse import FUSE, FuseOSError, Operations, fuse_get_context

INF = 999999

class SurfFS(Operations):
    def __init__(self, personal_token, mount_point, storage):
        self._ocean_channel = digitalocean.Manager(token = personal_token)
        self._mount_point = mount_point
        self._storage = storage
        self._droplets = self._ocean_channel.get_all_droplets()
        self._DROPLET_ = "droplets"
        self._IMAGE_ = "images"
        self._initialize_directory_structure()

    def _storage_path(self, path):
        if path.startswith('/'):
            path = path[1:]
        return os.path.join(self._storage, path)

    def _get_file_name(self, path):
        return path.split('/')[-1]

    """
    Initialize the file system structure. The file system structure looks like:
    /
    --/droplets
    ----/droplet-0
    ------<file for droplet parameters>
    ----/droplet-1
    ------<file for droplet parameters>
    --/images
    """
    def _initialize_directory_structure(self):
        droplet_dir = self._storage_path(self._DROPLET_)
        image_dir = self._storage_path(self._IMAGE_)
        if not os.path.exists(droplet_dir):
            os.mkdir(self._storage_path(self._DROPLET_), 0755)
        for droplet in self._droplets:
            d_inst_dir = "/".join([self._DROPLET_, droplet.name])
            if not os.path.exists(self._mount_point + d_inst_dir):
                os.mkdir(self._storage_path(d_inst_dir), 0755)
        if not os.path.exists(image_dir):
            os.mkdir(self._storage_path(self._IMAGE_), 0755)

    """
    Overriden Filesystem methods
    ============================
    """
    def access(self, path, mode):
        path = self._storage_path(path)
        if not os.access(path, mode):
            raise FuseOSError(errno.EACCESS)

    def chmod(self, path, mode):
        path = self._storage_path(path)
        return os.chmod(path, mode)

    def chown(self, path, uid, gid):
        path = self._storage_path(path)
        return os.chown(path, uid, gid)
    
    def getattr(self, path, fh=None):
        path = self._storage_path(path)
        stats = os.lstat(path)
        return dict((key, getattr(stats, key)) for key in [attr for attr in
            dir(stats) if attr.startswith('st_')])

    def readdir(self, path, fh):
        path = self._storage_path(path)
        entries = ['.', '..']
        if os.path.isdir(path):
            entries.extend(os.listdir(path))
        for entry in entries:
            yield entry

    def mknode(self, path, mode, dev):
        return os.mknode(self._storage_path(path), mode, dev)

    def rmdir(self, path):
        return os.rmdir(self._storage_path(path))

    def mkdir(self, path, mode):
        return os.mkdir(self._storage_path(path), mode)

    def statfs(self, path):
        path = self._storage_path(path)
        vfs_stats = os.statvfs(path)
        return dict((key, getattr(vfs_stats, key)) for key in [attr for attr in
            dir(vfs_stats) if attr.startswith('f_')])

    
    def open(self, path, flags):
        return os.open(self._storage_path(path), flags)

    def create(self, path, mode, fi=None):
        return os.open(self._storage_path(path), 
                       os.O_WRONLY | os.O_CREAT, mode)

    def read(self, path, length, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    def write(self, path, buf, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, buf)

    def flush(self, path, fh):
        return os.fsync(fh)


