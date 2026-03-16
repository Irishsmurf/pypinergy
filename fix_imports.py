with open("tests/unit/test_models.py", "r") as f:
    content = f.read()

# Make sure we didn't remove the imports needed for test_sensitive_fields_not_in_repr at the end
import re

if "from pypinergy.models import User, CreditCard" not in content and "def test_sensitive_fields_not_in_repr" in content:
    # Need to add them back in correctly
    pass
