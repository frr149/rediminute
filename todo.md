# Modo estricto async de pytest

Por lo visto eso hace que los tests de código async sean más seguros:
[tool.pytest.ini_options]
asyncio_mode = "strict"
testpaths = ["tests"]

pero lo de strict no lo reconoce y da un warning al llamar a pytest. Se vuelve majar a hacer todo tipo de "cosas"
que no entiendo. De momento lo dejo así