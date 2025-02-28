from oqs import oqs_python_version, oqs_version, get_enabled_kem_mechanisms


print(f'{oqs_python_version()}, {oqs_version()}, {get_enabled_kem_mechanisms()}')