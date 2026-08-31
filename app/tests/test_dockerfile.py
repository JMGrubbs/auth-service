import unittest
from pathlib import Path


class DockerfileTests(unittest.TestCase):
    def test_apt_uses_reliable_debian_transport(self) -> None:
        dockerfile = Path(__file__).resolve().parents[1] / "Dockerfile"
        contents = dockerfile.read_text(encoding="utf-8")

        self.assertIn("s|http://deb.debian.org|https://deb.debian.org|g", contents)
        self.assertIn("Acquire::ForceIPv4=true", contents)


if __name__ == "__main__":
    unittest.main()
