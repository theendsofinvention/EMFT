# coding=utf-8

import binascii
import os
import shutil
import tempfile

import path
import pefile
from humanize import filesize


class Win32FileInfo:
    def __init__(self, _path):

        self.__path = str(Path(_path).abspath())
        self.__props = None
        self.__read_props()

    @property
    def comments(self):
        return self.__props.get('Comments')

    @property
    def internal_name(self):
        return self.__props.get('InternalName')

    @property
    def product_name(self):
        return self.__props.get('ProductName')

    @property
    def company_name(self):
        return self.__props.get('CompanyName')

    @property
    def copyright(self):
        return self.__props.get('LegalCopyright')

    @property
    def product_version(self):
        return self.__props.get('ProductVersion')

    @property
    def file_description(self):
        return self.__props.get('FileDescription')

    @property
    def trademark(self):
        return self.__props.get('LegalTrademarks')

    @property
    def private_build(self):
        return self.__props.get('PrivateBuild')

    @property
    def file_version(self):
        return self.__props.get('FileVersion')

    @property
    def fixed_version(self):
        return self.__props.get('fixed_version')

    @property
    def original_filename(self):
        return self.__props.get('OriginalFilename')

    @property
    def special_build(self):
        return self.__props.get('SpecialBuild')

    def __read_props(self):

        def _loword(dword):
            return dword & 0x0000ffff

        def _hiword(dword):
            return dword >> 16

        self.__props = {}

        try:
            pe = pefile.PE(self.__path)
        except pefile.PEFormatError as e:
            raise ValueError(e.value)
        else:
            ms = pe.VS_FIXEDFILEINFO.ProductVersionMS
            ls = pe.VS_FIXEDFILEINFO.ProductVersionLS
            self.__props['fixed_version'] = '.'.join(map(str, (_hiword(ms), _loword(ms), _hiword(ls), _loword(ls))))
            for file_info in pe.FileInfo:
                if file_info.Key == b'StringFileInfo':
                    for st in file_info.StringTable:
                        for entry in st.entries.items():
                            self.__props[entry[0].decode('latin_1')] = entry[1].decode('latin_1')


# noinspection PyAbstractClass
class Path(path.Path):
    def crc32(self):

        if not self.isfile():
            raise TypeError('cannot compute crc32, not a file: {}'.format(self.abspath()))

        else:

            try:

                with open(self.abspath(), 'rb') as buf:
                    buf = "%08X" % (binascii.crc32(buf.read()) & 0xFFFFFFFF)

                    return buf

            except FileNotFoundError:
                raise FileNotFoundError('failed to compute crc32 for: {}'.format(self.abspath()))

            except PermissionError:
                raise PermissionError('failed to compute crc32 for: {}'.format(self.abspath()))

            except:
                raise RuntimeError('failed to compute crc32 for: {}'.format(self.abspath()))

    def human_size(self) -> str:
        return filesize.naturalsize(self.getsize(), gnu=True)

    def normalize(self) -> str:
        return self.abspath().replace('\\', '/').lower()

    def get_win32_file_info(self) -> Win32FileInfo:

        if not self.exists():
            raise FileNotFoundError(self.abspath())

        elif not self.isfile():
            raise TypeError(self.abspath())

        return Win32FileInfo(self)

    def abspath(self):
        return path.Path.abspath(self)

    def exists(self):
        return path.Path.exists(self)

    def get_size(self):
        return path.Path.getsize(self)

    def remove(self):
        return path.Path.remove(self)

    def text(self,
             encoding=None,
             errors='strict'):

        return path.Path.text(self, encoding, errors)

    def write_text(self,
                   text,
                   encoding=None,
                   errors='strict',
                   linesep=os.linesep,
                   append=False):

        return path.Path.write_text(self, text, encoding, errors, linesep, append)

    def rmtree(self, must_exist=True):

        if not self.isdir():
            raise TypeError('not a directory: {}'.format(self.abspath()))

        if must_exist and not self.exists():
            raise ValueError('directory does not exist: {}'.format(self.abspath()))

        for root, _, filenames in os.walk(str(self.abspath())):
            for file in filenames:
                os.chmod(root + '\\' + file, 0o777)
                os.remove(root + '\\' + file)

        shutil.rmtree(self.abspath())

    def joinpath(self, first, *others):
        return Path(super(Path, self).joinpath(first, *others))

    def must_exist(self, exc):
        if not self.exists():
            raise exc(self.abspath())

    def must_be_a_file(self, exc):
        self.must_exist(exc)
        if not self.isfile():
            raise exc(self.abspath())

    def must_be_a_dir(self, exc):
        self.must_exist(exc)
        if not self.isdir():
            raise exc(self.abspath())


def create_temp_file(
        *,
        suffix: str = None,
        prefix: str = None,
        create_in_dir: str = None) -> Path:
    os_handle, temp_file = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=create_in_dir or tempfile.gettempdir())
    os.close(os_handle)

    return Path(temp_file)


def create_temp_dir(
        *,
        suffix: str = None,
        prefix: str = None,
        create_in_dir: str = None) -> Path:
    temp_dir = tempfile.mkdtemp(suffix=suffix, prefix=prefix, dir=create_in_dir or tempfile.gettempdir())

    return Path(temp_dir)


if __name__ == '__main__':
    t = Path(r'F:\DEV\MizFlat\dist\EMFT.exe')
    x = Win32FileInfo(t)
