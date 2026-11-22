# Smoketest - Proves that our packages can be installed and imported
# Without atleast one test pytest will end with code 5 and our basic CI pipe will give red X
import study_buddy


def test_package_imports():
    assert study_buddy.__name__ == "study_buddy"
