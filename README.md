# A.G.N.I.S-Agent

MVP de una cadena de agentes en Python para convertir un borrador de auditoría web en un informe Markdown estructurado.

## Estado del MVP

El pipeline ya separa:

1. **Normalización:** transforma el Markdown en un modelo Pydantic.
2. **POC:** usa un adaptador explícito; el adaptador incluido no ejecuta peticiones y deja los pasos sin confirmar.
3. **Clasificación:** propone vector CVSS 4.0, OWASP y causa técnica.
4. **Impacto:** recibe únicamente pasos confirmados.
5. **Renderizado:** genera el informe Markdown.

Las decisiones deterministas —confirmación de pasos, puntuación CVSS, severidad, tablas y validación final— todavía deben implementarse antes de usarlo en producción.

## Instalación

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[openai,dev]'
export OPENAI_API_KEY='...'
```

## Uso

```bash
agnis borrador.md --output informe.md
```

El modelo se configura mediante `langchain-openai` y usa `gpt-4o-mini` con temperatura cero. El proveedor está aislado en `agnis/llm.py` para poder sustituirlo sin modificar los agentes.

## Próximos adaptadores

- Implementar un `PocRunner` para navegador o Burp.
- Cargar `cwec_v5.0.xml` y filtrar candidatos antes del selector CWE.
- Calcular CVSS con la librería oficial y derivar la severidad en código.
- Añadir validación de esquema, persistencia de artefactos y revisión del auditor.
