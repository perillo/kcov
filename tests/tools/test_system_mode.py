import os
import platform
import time
import unittest

import libkcov
from libkcov import cobertura


class SystemModeBase(libkcov.TestCase):
    def writeToPipe(self, str):
        f = open("/tmp/kcov-system.pipe", "w")
        f.write(str)
        f.close()


class system_mode_can_start_and_stop_daemon(SystemModeBase):
    def runTest(self):
        rv, o = self.do(self.kcov_system_daemon + " -d", False)

        pf = "/tmp/kcov-system.pid"
        assert os.path.isfile(pf)

        self.writeToPipe("STOPME")

        time.sleep(2)

        assert os.path.isfile(pf) is False


class system_mode_can_instrument_binary(SystemModeBase):
    def runTest(self):
        rv, o = self.do(
            self.kcov + " --system-record " + self.outbase + "/kcov " + self.binaries + "/"
        )
        assert rv == 0

        src = self.binaries + "/main-tests"
        dst = self.outbase + "/kcov/main-tests"

        assert os.path.isfile(src)
        assert os.path.isfile(dst)

        assert os.path.getsize(dst) > os.path.getsize(src)


class system_mode_can_record_and_report_binary(SystemModeBase):
    @unittest.skipIf(platform.machine() == "i686", "x86_64-only")
    def runTest(self):
        self.write_message(platform.machine())

        rv, o = self.do(
            self.kcov + " --system-record " + self.outbase + "/kcov " + self.binaries + "/"
        )

        rv, o = self.do(self.kcov_system_daemon + " -d", False)

        os.environ["LD_LIBRARY_PATH"] = self.outbase + "/kcov/lib"
        rv, o = self.do(self.outbase + "/kcov/main-tests", False)
        self.skipTest("Fickle test, ignoring")
        assert rv == 0

        time.sleep(3)
        self.writeToPipe("STOPME")

        rv, o = self.do(
            self.kcov + " --system-report " + self.outbase + "/kcov-report /tmp/kcov-data"
        )
        assert rv == 0

        dom = cobertura.parseFile(self.outbase + "/kcov-report/main-tests/cobertura.xml")
        assert cobertura.hitsPerLine(dom, "main.cc", 9) == 1
        assert cobertura.hitsPerLine(dom, "main.cc", 14) is None
        assert cobertura.hitsPerLine(dom, "main.cc", 18) >= 1
