import os
from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import get, copy, rmdir
from conan.tools.scm import Version

from conans import __version__ as conan_version

required_conan_version = ">=1.47.0"


class StrawberryPerlConan(ConanFile):
    name = "strawberryperl"
    description = "Strawberry Perl for Windows. Useful as build_require"
    license = ("Artistic-1.0", "GPL-1.0")
    homepage = "http://strawberryperl.com"
    url = "https://github.com/conan-io/conan-center-index"
    topics = ("installer", "perl", "windows")
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        self.folders.build = "build"

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type

    def validate(self):
        if self.info.settings.os != "Windows":
            raise ConanInvalidConfiguration("Strawberry Perl is only intended to be used on Windows.")

    def build(self):
        get(self, **self.conan_data["sources"][self.version][str(self.settings.arch)], destination=self.build_folder)

    def package(self):
        copy(self, pattern="License.rtf*", src=os.path.join(self.build_folder, "licenses"), dst=os.path.join(self.package_folder, "licenses"))
        copy(self, pattern="*", src=os.path.join(self.build_folder, "perl", "bin"), dst=os.path.join(self.package_folder, "bin"))
        copy(self, pattern="*", src=os.path.join(self.build_folder, "perl", "lib"), dst=os.path.join(self.package_folder, "lib"))
        copy(self, pattern="*", src=os.path.join(self.build_folder, "perl", "vendor", "lib"), dst=os.path.join(self.package_folder, "lib"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.libdirs = []
        self.cpp_info.includedirs = []

        # TODO remove once conan v2 is the only support and recipes have been migrated
        if Version(conan_version) < "2.0.0-beta":
            bin_path = os.path.join(self.package_folder, "bin")
            self.env_info.PATH.append(bin_path)

        perl_path = os.path.join(self.package_folder, "bin", "perl.exe").replace("\\", "/")
        self.conf_info.define("user.strawberryperl:perl", perl_path)
        if Version(conan_version) < "2.0.0-beta":
            self.user_info.perl = perl_path
