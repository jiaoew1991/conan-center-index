from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.env import VirtualBuildEnv
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, collect_libs, copy, export_conandata_patches, get, rmdir
import os

required_conan_version = ">=1.52.0"


class XercesCConan(ConanFile):
    name = "xerces-c"
    description = (
        "Xerces-C++ is a validating XML parser written in a portable subset of C++"
    )
    topics = ("xerces", "XML", "validation", "DOM", "SAX", "SAX2")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://xerces.apache.org/xerces-c/index.html"
    license = "Apache-2.0"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        # https://xerces.apache.org/xerces-c/build-3.html
        "char_type": ["uint16_t", "char16_t", "wchar_t"],
        "network_accessor": ["curl", "socket", "cfurl", "winsock"],
        "transcoder": ["gnuiconv", "iconv", "icu", "macosunicodeconverter", "windows"],
        "message_loader": ["inmemory", "icu", "iconv"],
        "mutex_manager": ["standard", "posix", "windows"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "char_type": "uint16_t",
        "network_accessor": "socket",
        "transcoder": "gnuiconv",
        "message_loader": "inmemory",
        "mutex_manager": "standard",
    }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
            self.options.network_accessor = "winsock"
            self.options.transcoder = "windows"
            self.options.mutex_manager = "windows"
        elif self.settings.os == "Macos":
            self.options.network_accessor = "cfurl"
            self.options.transcoder = "macosunicodeconverter"
            self.options.mutex_manager = "posix"
        elif self.settings.os == "Linux":
            self.options.mutex_manager = "posix"

    def configure(self):
        if self.options.shared:
            try:
                del self.options.fPIC
            except Exception:
                pass

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if "icu" in (self.options.transcoder, self.options.message_loader):
            self.requires("icu/71.1")
        if self.options.network_accessor == "curl":
            self.requires("libcurl/7.85.0")

    def _validate(self, option, value, os):
        """
        Validate that the given `option` has the required `value` for the given `os`
        If not raises a ConanInvalidConfiguration error

        :param option: the name of the option to validate
        :param value: the value that the `option` should have
        :param os: either a single string or a tuple of strings containing the
                   OS(es) that `value` is valid on
        """
        if self.info.settings.os not in os and getattr(self.info.options, option) == value:
            raise ConanInvalidConfiguration(
                "Option '{option}={value}' is only supported on {os}".format(
                    option=option, value=value, os=os
                )
            )

    def validate(self):
        if self.info.settings.os not in ("Windows", "Macos", "Linux"):
            raise ConanInvalidConfiguration("OS is not supported")
        self._validate("char_type", "wchar_t", ("Windows", ))
        self._validate("network_accessor", "winsock", ("Windows", ))
        self._validate("network_accessor", "cfurl", ("Macos", ))
        self._validate("network_accessor", "socket", ("Linux", "Macos"))
        self._validate("network_accessor", "curl", ("Linux", "Macos"))
        self._validate("transcoder", "macosunicodeconverter", ("Macos", ))
        self._validate("transcoder", "windows", ("Windows", ))
        self._validate("mutex_manager", "posix", ("Linux", "Macos"))
        self._validate("mutex_manager", "windows", ("Windows", ))

    def build_requirements(self):
        if hasattr(self, "settings_build") and self.options.message_loader == "icu":
            self.tool_requires("icu/71.1")

    def source(self):
        get(self, **self.conan_data["sources"][self.version],
            destination=self.source_folder, strip_root=True)

    def generate(self):
        env = VirtualBuildEnv(self)
        env.generate()
        tc = CMakeToolchain(self)
        # https://xerces.apache.org/xerces-c/build-3.html
        tc.variables["network-accessor"] = self.options.network_accessor
        tc.variables["transcoder"] = self.options.transcoder
        tc.variables["message-loader"] = self.options.message_loader
        tc.variables["xmlch-type"] = self.options.char_type
        tc.variables["mutex-manager"] = self.options.mutex_manager
        # avoid picking up system dependency
        tc.variables["CMAKE_DISABLE_FIND_PACKAGE_CURL"] = self.options.network_accessor != "curl"
        tc.variables["CMAKE_DISABLE_FIND_PACKAGE_ICU"] = "icu" not in (self.options.transcoder, self.options.message_loader)
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        for license in ("LICENSE", "NOTICE"):
            copy(self, license, src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "share"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_find_mode", "both")
        self.cpp_info.set_property("cmake_file_name", "XercesC")
        self.cpp_info.set_property("cmake_target_name", "XercesC::XercesC")
        self.cpp_info.set_property("pkg_config_name", "xerces-c")
        self.cpp_info.libs = collect_libs(self)
        if self.settings.os == "Macos":
            self.cpp_info.frameworks = ["CoreFoundation", "CoreServices"]
        elif self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("pthread")

        self.cpp_info.names["cmake_find_package"] = "XercesC"
        self.cpp_info.names["cmake_find_package_multi"] = "XercesC"
